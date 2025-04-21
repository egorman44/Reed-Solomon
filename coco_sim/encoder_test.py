from gf_arithmetic import GFArithmetic
from rs_encoder import ReedSolomonEncoder

# Initialize Galois Field GF(2^3) with poly = x^3 + x + 1 => 0b1011
gf = GFArithmetic(symb_width=3, poly=0b1011, generator=2)

# RS(7,3) means N=7, K=3 => 4 ECC symbols
rs = ReedSolomonEncoder(gf=gf, N_LEN=7, K_LEN=3, bus_width = 3)

# Define message using alpha exponents: [α^5, α^3, α^1]
message = [
    gf.alpha_to_symb(5),
    gf.alpha_to_symb(3),
    gf.alpha_to_symb(1),
]

# Encode the message
encoded = rs.encode(message)

lfsr = rs.evaluate_lfsr_states(message)

# Display the result in symbol and alpha power formats
print("Encoded message (symbols):", encoded)
print("Encoded message (alpha exponents):", [gf.symb_to_alpha(symb) for symb in encoded])
for i in range(len(lfsr)):
    print(f"{i}: {lfsr[i]} = a^{gf.symb_to_alpha(lfsr[i])}")
