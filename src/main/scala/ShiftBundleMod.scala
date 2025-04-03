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
import chisel3.util._

// interTermDelay is used to specify the pause (in cycles) between consecutive valid terms of the output signal. It helps handle the multicycle latency of the logic connected to the output of shiftBundleMod.
//   interTermDelay = 0: The block produces terms back-to-back on the output interface;
//   interTermDelay = 1: There is a single-cycle pause between two consecutive terms of the output signal;
//   etc

class ShiftBundleMod[T <: Data](shiftUnit: T, width: Int, shiftVal: Int, interTermDelay: Int=0) extends Module{
  require(shiftVal <= width, "[ERROR] ShiftBundle. Wrong shiftVal compared to the width.")
  val io = IO(new Bundle {
    val vecIn = Input(Valid(Vec(width, shiftUnit)))
    val vecOut = Output(Valid(Vec(shiftVal, shiftUnit)))
    val lastOut = Output(Bool())
  })

  val shiftCntrQ = RegInit(UInt(log2Ceil(width).W), 0.U)
  val shiftEn = Wire(UInt(1.W))

  //
  when(io.vecIn.valid) {
    shiftCntrQ := 0.U
  }.otherwise{
    when(shiftCntrQ === interTermDelay.U) {
      shiftCntrQ := 0.U
    }.otherwise {
      shiftCntrQ := shiftCntrQ + 1.U
    }
  }

  if(interTermDelay == 0){
    shiftEn := 1.U
  }else{
    shiftEn := (shiftCntrQ === interTermDelay.U)
  }

  if(shiftVal == width) {
    io.vecOut.bits := RegNext(next=io.vecIn.bits)
    io.lastOut := RegNext(next=io.vecIn.valid)
    io.vecOut.valid := RegNext(next=io.vecIn.valid, init=false.B)
  } else {

    val vldWidth  = math.ceil(width/shiftVal.toDouble).toInt
    val dataShift = Reg(Vec(width, shiftUnit))
    val vldShift  = RegInit(UInt(vldWidth.W), 0.U)

    // Load data into the shift register
    when(io.vecIn.valid) {
      dataShift := io.vecIn.bits
      vldShift := ((BigInt(1)<<vldWidth)-1).U
    }.elsewhen(shiftEn === 1.U) {
      vldShift := vldShift >> 1
      for(i <- 0 until width-shiftVal)
        dataShift(i) := dataShift(i+shiftVal)
      // Nullify begining of the shiftReg to clear up the pipe.
      for(i <- width-shiftVal until width)
        dataShift(i) := 0.U.asTypeOf(shiftUnit)
    }

    io.vecOut.valid := vldShift.asTypeOf(Vec(vldWidth, Bool())).reduce(_|_)

    when(vldShift === 1.U) {
      io.lastOut := 1.U
    }.otherwise {
      io.lastOut := 0.U
    }

    for(i <- 0 until shiftVal){
      io.vecOut.bits(i) := dataShift(i)
    }
  }

}
