/*
 * ----------------------------------------------------------------------
 *  Copyright (c) 2024 Egor Smirnov
 *
 *  Licensed under terms of the MIT license
 *  See https://github.com/egorman44/Reed-Solomon/blob/main/LICENSE
 *    for license terms
 * ----------------------------------------------------------------------
 */

package Rs

import chisel3._
import circt.stage.ChiselStage
import chisel3.util._

class RsBlockRecovery(c: Config) extends Module {
  val io = IO(new Bundle {
    val sAxisIf = Input(Valid(new axisIf(c.BUS_WIDTH, c.SYMB_WIDTH)))
    val mAxisIf = Output(Valid(new axisIf(c.BUS_WIDTH, c.SYMB_WIDTH)))
    val fifoFull = Output(UInt(1.W))
    val coreClock = if(c.decoderSingleClock) None else Some(Input(Clock()))
    val coreRst = if(c.decoderSingleClock) None else Some(Input(Bool()))
  })

  // Instance RsDecoder
  val rsDecoder = Module(new RsDecoder(c))
  rsDecoder.io.sAxisIf <> io.sAxisIf

  rsDecoder.io.coreClock := io.coreClock.getOrElse(clock)
  rsDecoder.io.coreRst := io.coreRst.getOrElse(reset)
  
  val goodMsg = ~rsDecoder.io.msgCorrupted & rsDecoder.io.syndValid

  val startMsg = Wire(Bool())

  // store error positions and values in the queues.
  // When the message is not corrupted make queueErrPos.io.enq.bits.ffs = 0
  val queueErrPos = Module(new Queue(new vecFfsIf(c.T_LEN, c.SYMB_WIDTH), c.msgNum))
  queueErrPos.io.enq.valid := rsDecoder.io.errPosIf.valid
  queueErrPos.io.enq.bits.vec := rsDecoder.io.errPosIf.bits.vec
  queueErrPos.io.enq.bits.ffs := rsDecoder.io.errPosIf.bits.ffs
  queueErrPos.io.deq.ready := startMsg

  val queueErrVal = Module(new Queue(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)), c.msgNum))
  queueErrVal.io.enq.valid := rsDecoder.io.errValIf.valid
  queueErrVal.io.enq.bits := rsDecoder.io.errValIf.bits.vec
  queueErrVal.io.deq.ready := startMsg

  // sQueue is used to store incomming messages
  class sQueueBundle(width: Int) extends Bundle {
    val tdata = Vec(width, UInt(c.SYMB_WIDTH.W))
    val tlast = Bool()
  }
  val sQueue = Module(new Queue(new sQueueBundle(c.BUS_WIDTH), c.msgNum*c.MSG_DURATION))

  sQueue.io.enq.valid := io.sAxisIf.valid
  sQueue.io.enq.bits.tdata := io.sAxisIf.bits.tdata
  sQueue.io.enq.bits.tlast := io.sAxisIf.bits.tlast

  val cntr = RegInit(UInt((log2Ceil(c.BUS_WIDTH * c.MSG_DURATION)+1).W), 0.U)
  val mReady = RegInit(Bool(),false.B)

  sQueue.io.deq.ready := mReady

  // cntr keeps track positions of messages that reading out from the sQueue.
  // It's used to correspond positions located in the errPosVec barrelShifter.
  when(startMsg) {
    cntr := c.BUS_WIDTH.U
    mReady := true.B
  }.elsewhen(mReady){
    when(sQueue.io.deq.bits.tlast) {
      cntr := 0.U
      mReady := false.B
    }.otherwise{
      cntr := cntr + c.BUS_WIDTH.U
    }
  }

  // startMsg is used to pop out the messages from sQueue, queueErrPos, queueErrVal FIFOs.
  // Read out the message when queueErrVal is not empty
  // and there is no reading operation.
  // B2B: during last cycle of block N check queueErrVal.io.deq.valid
  // if the block N+1 has already proccesed and ErrVal available then start
  // to read out block N+1 from the sQueue.

  when(~mReady & queueErrVal.io.deq.valid) {
    startMsg := true.B
  }.elsewhen(mReady & sQueue.io.deq.bits.tlast & queueErrVal.io.deq.valid){
    startMsg := true.B
  }.otherwise{
    startMsg := false.B
  }

  // Shift position value is less than current cntr value
  // Define the max 
  val LOOP_LIMIT = if(c.T_LEN < c.BUS_WIDTH) c.T_LEN else c.BUS_WIDTH

  val shiftEnableVec = Wire(Vec(LOOP_LIMIT, UInt(1.W)))
  val shiftVal = shiftEnableVec.reduce(_+&_)
  
  val errPosVecRev = VecInit(queueErrPos.io.deq.bits.vec.reverse)
  val errValVecRev = VecInit(queueErrVal.io.deq.bits.reverse)
  val errPosAxis = Wire(Vec(LOOP_LIMIT, UInt(log2Ceil(c.BUS_WIDTH).W)))
  val errPosVec = Reg(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
  val errValVec = Reg(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
  val errPosSel = Reg(UInt(c.T_LEN.W))

  val ffsCountOnes = c.T_LEN.U - PopCount(queueErrPos.io.deq.bits.ffs)

  dontTouch(ffsCountOnes)

  // Load barrelShifters only if the errors were detected
  val correctMsg = startMsg & queueErrPos.io.deq.bits.ffs.orR

  when(correctMsg) {
    errPosVec := (errPosVecRev.asUInt >> (c.SYMB_WIDTH.U * ffsCountOnes)).asTypeOf(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
    errValVec := (errValVecRev.asUInt >> (c.SYMB_WIDTH.U * ffsCountOnes)).asTypeOf(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
    errPosSel := queueErrPos.io.deq.bits.ffs
  }.elsewhen(shiftEnableVec.reduce(_|_) === 1.U){
    errPosVec := (errPosVec.asUInt >> (c.SYMB_WIDTH.U * shiftVal)).asTypeOf(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
    errValVec := (errValVec.asUInt >> (c.SYMB_WIDTH.U * shiftVal)).asTypeOf(Vec(c.T_LEN, UInt(c.SYMB_WIDTH.W)))
    errPosSel := errPosSel >> shiftVal
  }

  // Check if the error positions match the current message position that is reading out from sQueue.
  // If matched then 
  for(i <- 0 until LOOP_LIMIT) {
    errPosAxis(i) := errPosVec(i) % c.BUS_WIDTH.U
    when(errPosVec(i) < cntr) {
      shiftEnableVec(i) := errPosSel(i)
    }.otherwise{
      shiftEnableVec(i) := 0.U
    }
  }

  val mTdata = Wire(Vec(c.BUS_WIDTH, UInt(c.SYMB_WIDTH.W)))
  val mTkeep = Wire(UInt(c.BUS_WIDTH.W))

  mTdata := sQueue.io.deq.bits.tdata  

  val TLAST_TKEEP = if(c.N_LEN % c.BUS_WIDTH == 0) c.BUS_WIDTH else c.N_LEN % c.BUS_WIDTH

  when(sQueue.io.deq.bits.tlast){
    mTkeep := Fill(TLAST_TKEEP, 1.U)
  }.otherwise{
    mTkeep := Fill(c.BUS_WIDTH, 1.U)
  }

  for(i <- 0 until LOOP_LIMIT) {
    when(shiftEnableVec(i) === 1.U){
      mTdata(errPosAxis(i)) := sQueue.io.deq.bits.tdata(errPosAxis(i)) ^ errValVec(i)
    }
  }

  io.mAxisIf.valid := mReady
  io.mAxisIf.bits.tdata := mTdata
  io.mAxisIf.bits.tlast := sQueue.io.deq.bits.tlast
  io.mAxisIf.bits.tkeep := mTkeep
  io.fifoFull := !sQueue.io.enq.ready
}

// runMain Rs.GenRsBlockRecovery
object GenRsBlockRecovery extends App {

  val projectRoot = System.getProperty("project.root")

  ConfigParser.parse(args) match {
    case Some(cmdConfig) =>
      JsonHandler.writeToFile(cmdConfig, "rs.json")
      val c = new Config(cmdConfig)
      ChiselStage.emitSystemVerilogFile(new RsBlockRecovery(c), Array())
    case None =>
      sys.exit(1)      
  }  
}

