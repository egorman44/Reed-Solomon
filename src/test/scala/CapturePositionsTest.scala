package Rs

/*
import chisel3._
import chiseltest._
import org.scalatest.freespec.AnyFreeSpec
import chisel3.util._
import BitsManipulation._
class CapturePositionsTest extends AnyFreeSpec with ChiselScalatestTester {

  //behavior of "CapturePositions"
  "CapturePositionsTest" in {

    val projectRoot = System.getProperty("project.root")
    val c = JsonHandler.readConfig(projectRoot + "/rs.json")

    test(new CapturePositions(c)).withAnnotations(Seq(WriteVcdAnnotation)) { dut =>
      // Reset the DUT (Device Under Test)
      dut.reset.poke(true.B)
      dut.clock.step()
      dut.reset.poke(false.B)
      dut.clock.step()

      var outPositions = List[BigInt]()
      val positions = List(213, 80, 29)
      val positionsOh = xorBitAtPositions(positions.map(c.N_LEN-1-_))

      val sliceWidth = 64
      val numberWidth = 256
      val testPositions = sliceBigInt(positionsOh, sliceWidth, numberWidth).reverse

      var base = 0

      for(testPos <- testPositions) {
        outPositions = outPositions ++ findPositionsOfOnes(testPos).map(_+base)
        base = base + c.chienRootsPerCycle
      }
      val errPosIfVal = outPositions.map(c.N_LEN-1-_)
      val testPositionsHex = testPositions.map(_.toString(16).toUpperCase)
      println(s"testPositions: $testPositionsHex")
      println(s"outPositions: $outPositions")
      println(s"errPosIfVal: $errPosIfVal")

      // Iterate through cycles and provide bit positions
      val stimulusThread = fork {
        for (i <- testPositions.indices) {
          dut.io.bitPos.valid.poke(true.B)
          dut.io.bitPos.last.poke(if (i == testPositions.size - 1) true.B else false.B)
          dut.io.bitPos.pos.poke(testPositions(i).U)

          dut.clock.step()
        }
        dut.io.bitPos.valid.poke(false.B)
        dut.io.bitPos.last.poke(false.B)
      }

      // Storage for captured output
      var capturedOutput = List[BigInt]()
      var stopTest = false
      val captureThread = fork {
        // Wait for valid signal
        while(!stopTest){
          if (dut.io.errPosIf.valid.peekBoolean()) {
            val tkeep = dut.io.errPosIf.bits.ffs.peekInt()
            // Caprure valid data only
            for( i <- (0 until c.T_LEN).reverse) {
              if((tkeep & ( 1 << i)) != 0) {
                // Capture output when valid is true
                //val output = (0 until c.T_LEN).map(i => dut.io.errPosIf.bits.vec(i).peekInt()).toSeq
                val output = dut.io.errPosIf.bits.vec(i).peekInt()
                capturedOutput = capturedOutput :+ output
              }
            }
          }
          dut.clock.step()
        }
      }

      // Join threads after the test duration
      stimulusThread.join()
      // Wait for the last flag to propagate and capture the output
      dut.clock.step(50)
      stopTest = true
      captureThread.join() // Terminate the capture thread after test is done
      println(s"Captured Output: $capturedOutput")
      assert(capturedOutput == errPosIfVal)
    }
  }
}
*/