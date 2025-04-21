class GFArithmetic:
    def __init__(self, symb_width: int, poly: int, generator: int = 2):
        self.symb_width = symb_width
        self.poly = poly
        self.generator = generator
        self.size = 1 << symb_width  # Field size (2^m)
        self.max_exponent = self.size - 1

        self.alpha_to_symb_tbl = self._gen_alpha_to_symb()
        self.symb_to_alpha_tbl = self._gen_symb_to_alpha()

    def _gen_alpha_to_symb(self) -> list[int]:
        tbl = [1]
        for _ in range(1, self.size):
            next_val = tbl[-1] * self.generator
            if next_val >= self.size:
                next_val ^= self.poly
            tbl.append(next_val)
        return tbl

    def _gen_symb_to_alpha(self) -> list[int]:
        tbl = [0] * self.size
        for i in range(self.size - 1):
            symb = self.alpha_to_symb_tbl[i]
            tbl[symb] = i
        return tbl

    def alpha_to_symb(self, alpha: int) -> int:
        return self.alpha_to_symb_tbl[alpha % self.max_exponent]

    def symb_to_alpha(self, symb: int) -> int:
        if symb == 0:
            return None
        return self.symb_to_alpha_tbl[symb]

    def gf_mult(self, symbA: int, symbB: int) -> int:
        if symbA == 0 or symbB == 0:
            return 0
        alphaA = self.symb_to_alpha(symbA)
        alphaB = self.symb_to_alpha(symbB)
        return self.alpha_to_symb((alphaA + alphaB) % self.max_exponent)

    def gf_div(self, dividend: int, divider: int) -> int:
        if dividend == 0:
            return 0
        alpha_dividend = self.symb_to_alpha(dividend)
        alpha_divider = self.symb_to_alpha(divider)
        return self.alpha_to_symb((alpha_dividend - alpha_divider + self.max_exponent) % self.max_exponent)

    def gf_inv(self, symb: int) -> int:
        if symb == 0:
            raise ZeroDivisionError("Inverse of zero is undefined in GF")
        return self.alpha_to_symb((self.max_exponent - self.symb_to_alpha(symb)) % self.max_exponent)

    def gf_pow(self, symb: int, degree: int) -> int:
        if symb == 0:
            return 0
        return self.alpha_to_symb((self.symb_to_alpha(symb) * degree) % self.max_exponent)
