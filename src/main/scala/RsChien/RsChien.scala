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
import chisel3.util.ImplicitConversions.intToUInt
import circt.stage.ChiselStage
import chisel3.util._

/////////////////////////////////////////
// RsChien
/////////////////////////////////////////

class RsChien(c: Config) extends Module{
  val io = IO(new Bundle {
    val errLocIf = Input(Valid(new vecFfsIf(c.T_LEN+1, c.SYMB_WIDTH)))
    val errPosIf = Output(Valid(new vecFfsIf(c.T_LEN, c.SYMB_WIDTH)))
    val chienErrDetect = Output(Bool())
  })

  val rsChienErrBitPos = Module(new RsChienErrBitPos(c))
  //val rsChienBitPosToNum = Module(new RsChienBitPosToNum(c))
  val rsChienBitPosToNum = Module(new CapturePositions(c))

  rsChienErrBitPos.io.errLocIf <> io.errLocIf
  rsChienBitPosToNum.io.bitPos <> rsChienErrBitPos.io.bitPos
  io.errPosIf <> rsChienBitPosToNum.io.errPosIf

  when(io.errPosIf.valid) {
    io.chienErrDetect := (io.errLocIf.bits.ffs(c.T_LEN,1) ^ io.errPosIf.bits.ffs).orR
  }.otherwise {
    io.chienErrDetect := 0.U
  }

  /////////////////
  // Assert stable
  /////////////////
  val stableAssrt = Module(new DataStableAssrt(new vecFfsIf(c.T_LEN, c.SYMB_WIDTH)))
  stableAssrt.io.start := io.errPosIf.valid
  stableAssrt.io.stop := false.B
  stableAssrt.io.data := io.errPosIf.bits

}

//
// runMain Rs.GenChien
object GenChien extends App{
  val config = JsonHandler.readConfig("/home/egorman44/chisel-lib/rs.json")
  ChiselStage.emitSystemVerilogFile(new RsChien(config), Array())
}
