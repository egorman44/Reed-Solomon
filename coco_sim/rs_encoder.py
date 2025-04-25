from gf_arithmetic import GFArithmetic

class ReedSolomonEncoder:
    def __init__(self, gf: GFArithmetic, N_LEN: int, K_LEN: int, fcr: int = 0, bus_width: int = 0):
        self.gf = gf
        self.N_LEN = N_LEN
        self.K_LEN = K_LEN
        self.fcr = fcr
        self.ecc_len = N_LEN - K_LEN  # nsym
        self.T_LEN = self.ecc_len // 2
        self.poly_gen = self._gen_generator_poly(self.ecc_len, self.fcr)
        self.bus_width = bus_width
        # Check the data is aligned on the last cycle        
        self.non_aligned = K_LEN % bus_width
        self.last_shift = self.bus_width - self.non_aligned
        self._compute_gamma_matrix(bus_width)
        # Initialize par/seq encoder states:
        self.lfsr_seq = [0] * self.ecc_len
        self.lfsr_par = [0] * self.ecc_len
        
    def _poly_mul(self, p: list[int], q: list[int]) -> list[int]:
        result = [0] * (len(p) + len(q) - 1)
        for i in range(len(p)):
            for j in range(len(q)):
                result[i + j] ^= self.gf.gf_mult(p[i], q[j])
        return result

    def _gen_generator_poly(self, nsym: int, fcr: int = 0) -> list[int]:
        gen = [1]
        for i in range(nsym):
            gen = self._poly_mul(gen, [1, self.gf.gf_pow(self.gf.generator, i + fcr)])
        print(f"poly_gen1 : {gen}")
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

    def encode_seq(self, message: list[int]) -> list[int]:
        self.lfsr_seq = [0] * self.ecc_len
        self.get_lfsr_seq(message)
        return message + self.lfsr_seq[::-1]

    def encode_par(self, message: list[int]) -> list[int]:
        """
        Parallel encoding using LFSR logic and gamma matrix.
        The message is processed in bus_width-symbol chunks.

        :param message: List of input message symbols (length == K_LEN)
        :return: Encoded message [data | ecc]
        """
        last_cycle = 0
        if len(message) != self.K_LEN:
            raise ValueError(f"Input message length must be {self.K_LEN}, got {len(message)}")
        if not hasattr(self, 'bus_width'):
            raise AttributeError("Encoder must define self.bus_width before using encode_par().")

        # Step 1: Reset the LFSR state
        self.lfsr_par = [0] * self.ecc_len

        # Step 2: Feed chunks of message symbols into get_lfsr_par()
        for i in range(0, self.K_LEN, self.bus_width):
            chunk = message[i:i + self.bus_width]

            # Pad last chunk if it's smaller than bus_width
            if len(chunk) < self.bus_width:
                chunk += [0] * (self.bus_width - len(chunk))
                last_cycle = 1

            self.lfsr_par = self.get_lfsr_par(chunk, self.lfsr_par, last_cycle)
            print(f"lfsr_par[{i}] = {self.lfsr_par}")

        # Step 3: Return full encoded message (message + parity)
        return message + self.lfsr_par[::-1]
    
    def _compute_gamma_matrix(self, I: int):
        g = self.poly_gen[::-1]
        self.gamma = [[0 for _ in range(I+1)] for _ in range(self.ecc_len)]
        self.gamma_str = ''
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
        self._compute_gamma_matrix_last()
        print(f"self.gamma = {self.gamma}")
        print(f"self.gamma_last = {self.gamma_last}")


    def _compute_gamma_matrix_last(self):
        self.gamma_last = []
        for i in range(len(self.gamma)):
            if(self.non_aligned):
                self.gamma_last.append([0]*self.last_shift + self.gamma[i][:self.bus_width+1-self.last_shift])
            else:
                self.gamma_last.append(self.gamma[i])
            
                
    def get_lfsr_par(self, input_symbols: list[int], lfsr_state_current: list[int], last_cycle: int=0) -> list[int]:
        # Make a local gamma to change coefficients
        # when K_LEN is not aligned with bus_width
        gamma = self.gamma_last if last_cycle else self.gamma
        omega = self.non_aligned if last_cycle else self.bus_width
        
        lfsr_state = []
        print("\n\n")
        for i in range(self.ecc_len):
            x_prev = 0 if i - omega < 0 else lfsr_state_current[i - omega]
            x_prev_str = f"X[{i-omega}]"
            acc = 0
            acc_formula_str = ''
            acc_val_str = ''
            for j in range(1, self.bus_width + 1):
                sum_term = f"gamma[{i}][{self.bus_width-j+1}]*(I[{j-1}]+X[{self.ecc_len-j}])"
                gamma_coef = gamma[i][self.bus_width - j + 1]
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
            #print(X_str)
        return lfsr_state

    def get_lfsr_seq(self, input_symbols: list[int]) -> list[int]:
        """
        Sequentially evaluate LFSR states for a list of input symbols.
        This simulates the register behavior over time.
        
        :param input_symbols: List of input symbols fed to the encoder (length = K_LEN)
        :return: List representing final LFSR state (length = ecc_len)
        """
        g = self.poly_gen[::-1]
        for n in range(len(input_symbols)):
            feedback = input_symbols[n] ^ self.lfsr_seq[-1]  # I[n] + X[2T-1][n-1]

            # Compute next state for each register from right to left
            new_lfsr = [0] * self.ecc_len
            for i in range(self.ecc_len):
                mult = self.gf.gf_mult(feedback, g[i])
                prev = self.lfsr_seq[i - 1] if i > 0 else 0
                new_lfsr[i] = mult ^ prev

            self.lfsr_seq = new_lfsr
            print(f"lfsr_seq[{n}] = {self.lfsr_seq}")
