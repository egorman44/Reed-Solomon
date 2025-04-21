from gf_arithmetic import GFArithmetic

class ReedSolomonEncoder:
    def __init__(self, gf: GFArithmetic, N_LEN: int, K_LEN: int, fcr: int = 1, bus_width: int = 0):
        self.gf = gf
        self.N_LEN = N_LEN
        self.K_LEN = K_LEN
        self.fcr = fcr
        self.ecc_len = N_LEN - K_LEN  # nsym
        self.T_LEN = self.ecc_len // 2
        self.poly_gen = self._gen_generator_poly(self.ecc_len, self.fcr)
        self._compute_gamma_matrix(bus_width)

    def _poly_mul(self, p: list[int], q: list[int]) -> list[int]:
        result = [0] * (len(p) + len(q) - 1)
        for i in range(len(p)):
            for j in range(len(q)):
                result[i + j] ^= self.gf.gf_mult(p[i], q[j])
        return result

    def _gen_generator_poly(self, nsym: int, fcr: int = 1) -> list[int]:
        gen = [1]
        for i in range(nsym):
            gen = self._poly_mul(gen, [1, self.gf.gf_pow(self.gf.generator, i + fcr)])
        return gen

    def symb_to_alpha_poly(self, poly_symb: list[int]) -> list[int]:
        return [self.gf.symb_to_alpha(term) for term in poly_symb]

    def encode(self, message: list[int]) -> list[int]:
        if len(message) != self.K_LEN:
            raise ValueError(f"Input message length must be {self.K_LEN}, got {len(message)}")

        msg_out = message + [0] * self.ecc_len
        for i in range(len(message)):
            coef = msg_out[i]
            if coef != 0:
                for j in range(len(self.poly_gen)):
                    msg_out[i + j] ^= self.gf.gf_mult(coef, self.poly_gen[j])
        return message + msg_out[-self.ecc_len:]

    def _compute_gamma_matrix(self, I: int):
        g = self.poly_gen[::-1]
        self.gamma = [[0 for _ in range(self.ecc_len)] for _ in range(I + 1)]
        self.gamma_str = ''
        print(self.gamma)
        for i in range(self.ecc_len):
            for omega in range(1, I + 1):
                g0_idx = i - omega + 1
                term1 = g[g0_idx] if 0 <= g0_idx < len(g) else 0
                term1_str = f"g[{g0_idx}]"
                acc = 0
                acc_formula_str = ""
                acc_val_str = ""
                for j in range(1, omega + 1):
                    g_val = g[self.ecc_len - j] if 0 <= self.ecc_len - j < len(g) else 0
                    acc ^= self.gf.gf_mult(g_val, self.gamma[i][omega - j])
                    sum_term_str = f"g[{self.ecc_len-j}]*gamma[{i}][{omega-j}]"
                    acc_formula_str += ' ^ ' + sum_term_str
                    acc_val_str += ' ^ ' + f"{g_val}*{self.gamma[i][omega - j]}"
                self.gamma[i][omega] = term1 ^ acc
                self.gamma_str += f"gamma[{i}][{omega}] = {term1_str}{acc_formula_str} = {term1}{acc_val_str} = {self.gamma[i][omega]}"
                #print(f"gamma[{i}][{omega}] = {term1_str}{acc_formula_str} = {term1}{acc_val_str} = {self.gamma[i][omega]}")

    def evaluate_lfsr_states(self, input_symbols: list[int]) -> list[int]:
        omega = len(input_symbols)
        lfsr_state_current = [0] * self.ecc_len
        lfsr_state = []
        print("\n\n")
        for i in range(self.ecc_len):
            x_prev = 0 if i - omega < 0 else lfsr_state_current[i - omega]
            x_prev_str = f"X[{i-omega}]"
            acc = 0
            acc_formula_str = ''
            acc_val_str = ''
            for j in range(1, omega + 1):
                sum_term = f"gamma[{i}][{omega-j+1}]*(I[{j-1}]+X[{self.ecc_len-j}])"
                gamma_coef = self.gamma[i][omega - j + 1]
                input_symb = input_symbols[j - 1]
                x_feedback_idx = self.ecc_len - j
                x_feedback_val = (
                    lfsr_state_current[x_feedback_idx]
                    if x_feedback_idx < len(lfsr_state_current)
                    else 0
                )
                sum_term_eval = f"{gamma_coef}*({input_symb}+{x_feedback_val})"
                sum_input = input_symb ^ x_feedback_val
                acc ^= self.gf.gf_mult(gamma_coef, sum_input)
                acc_formula_str += ' ^ ' + sum_term
                acc_val_str += ' ^ ' + sum_term_eval
            x_i = x_prev ^ acc
            lfsr_state_current.append(x_i)
            lfsr_state.append(x_i)
            X_str = f"X[{i}] = {x_prev_str}{acc_formula_str} = {x_prev}{acc_val_str} = {x_i}"
            print(X_str)
        return lfsr_state

    def print_structure(self):
        print("Gamma coefficients:")
        print(self.gamma_str)
