package Rs

import chisel3._
import chisel3.util._
import chiseltest._
import org.scalatest.freespec.AnyFreeSpec
import chisel3._
import chisel3.util._

import scala.collection.mutable.ArrayBuffer
import scala.util.Random

class GfMultWrap(SYMB_WIDTH : Int = 8) extends Module {
  val symA = IO(Input(UInt(SYMB_WIDTH.W)))
  val symB = IO(Input(UInt(SYMB_WIDTH.W)))
  val res = IO(Output(UInt()))
  val is_equal = IO(Output(Bool()))

  val confObj = Config(CmdConfig(
                        AXIS_CLOCK = 100.0,
                        CORE_CLOCK = 100.0,
                        SYMB_WIDTH = SYMB_WIDTH,
                        BUS_WIDTH = 4,
                        POLY = 285,
                        FCR = 0,
                        N_LEN = 240,
                        K_LEN = 214
                      )
  )

  val res1 = confObj.gfMult(symA, symB, "basic")
  val res2 = confObj.gfMult(symA, symB, "barrett")
  assert(res1 === res2)

  res := res1
  is_equal := res1 === res
}

class GfMultTest extends AnyFreeSpec with ChiselScalatestTester {
  "prove gfmult equal" in {
    //verify(new GfMultA(), Seq(BoundedCheck(1)))
    test(new GfMultWrap(8)).withAnnotations(Seq(WriteVcdAnnotation)) {
      c => {
        for (i <- 0 until 1000) {
          val a = Random.nextInt(256)
          val b = Random.nextInt(256)
          c.symA.poke(a.U)
          c.symA.poke(b.U)
          c.clock.step()
          c.is_equal.expect(true.B)
          //c.res.expect((a % b).U)
          if (i % 1000 == 0) println(s"Ran ${i} vectors")
        }
      }
    }
  }
}
