package Rs
import chisel3._
import chisel3.util.{MuxLookup, log2Ceil}

object RsUtil {
  def isPowerOfTwo(n: Int): (Boolean, Int) = {
    if (n <= 0) (false, -1)
    else if ((n & (n - 1)) == 0) (true, Integer.numberOfTrailingZeros(n))
    else (false, -1)
  }

  def modulo(a : UInt, b : Int, mtype : String = "default") : UInt = {
    mtype match {
      case "barrett" =>
        val bitWidth = if ((a.getWidth & 1) == 1) a.getWidth / 2 + 1 else a.getWidth / 2
        val m = b.U(bitWidth.max(log2Ceil(b)).W)
        val k = 2 * bitWidth
        val mu = ((BigInt(1) << k) / b).U((k + 1).W) // Precomputed value of mu = floor(2^(2*bitWidth) / m)

        // Compute q = floor(x / m) using Barrett reduction approximation
        val q = (a * mu) >> k

        // Compute r = x - q * m
        val r = a - (q * m)

        // If r >= m, subtract m
        Mux(r >= m, r - m, r)
      case "unrolled" =>
        val constMap = for  {
          i <- 0 until (1 << a.getWidth)
          if (i >= b)
        } yield i.U -> (i % b).U
        MuxLookup(a, a)(constMap)
      case _ =>
        a % b.U
    }
  }

  def const_mul(x: UInt, mul: Int): UInt = {
    require(mul >= 0)
    if (mul > 0) {
      var shift: Int = 0
      var m: Int = mul
      val width = x.getWidth + log2Ceil(mul)
      val mstage = Wire(Vec(log2Ceil(mul + 1), UInt(width.W)))
      while (m > 0) {
        if ((m & 1) == 1) {
          mstage(shift) := x << shift
        } else {
          mstage(shift) := 0.U
        }
        shift += 1
        m = m >> 1
      }
      mstage.reduce(_ + _)
    } else 0.U
  }
}
