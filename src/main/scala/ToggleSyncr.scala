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

class ToggleSyncr() extends Module{
  val io = IO(new Bundle{
    val in = Input(Bool())
    val out = Output(Bool())
    val outRst = Input(Bool())
    val outClk = Input(Clock())
  })

  val inQ = RegNext(io.in, init=false.B)

  val toggleInClkQ = RegInit(Bool(), false.B)

  when(io.in & ~inQ){
    toggleInClkQ := ~toggleInClkQ
  }

  val toggle0OutClkQ = Wire(Bool())
  val toggle1OutClkQ = Wire(Bool())
  val toggle2OutClkQ = Wire(Bool())

  withClockAndReset(io.outClk, io.outRst) {
    toggle0OutClkQ := RegNext(toggleInClkQ, init = false.B)
    toggle1OutClkQ := RegNext(toggle0OutClkQ, init = false.B)
    toggle2OutClkQ := RegNext(toggle1OutClkQ, init = false.B)
  }

  io.out := toggle1OutClkQ ^ toggle2OutClkQ

}
