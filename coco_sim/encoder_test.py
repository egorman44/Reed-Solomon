from reedsolo import rs_encode_msg
from reedsolo import init_tables

from gf_arithmetic import GFArithmetic
from rs_encoder import ReedSolomonEncoder
from enc_msg_comparator import EncodedMessageComparator
    
FCR=0
POLY=285
N_LEN=240
K_LEN=214
SYMB_WIDTH=8
REDUNDANCY=N_LEN-K_LEN

init_tables()
message = []
for i in range(K_LEN):
    message.append(i)

enc_msg_reedsolo = list(rs_encode_msg(msg_in=message, fcr=FCR , nsym=REDUNDANCY))

# Initialize Galois Field GF(2^3) with poly = x^3 + x + 1 => 0b1011
gf = GFArithmetic(symb_width=SYMB_WIDTH, poly=POLY, generator=2)

# RS(7,3) means N=7, K=3 => 4 ECC symbols
rs = ReedSolomonEncoder(gf=gf, N_LEN=N_LEN, K_LEN=K_LEN, bus_width = 4, fcr=FCR)
    
# Encode the message
enc_msg = rs.encode(message)
enc_msg_seq = rs.encode_seq(message)
enc_msg_par = rs.encode_par(message)

# Create comparator
comparator = EncodedMessageComparator()
#comparator.add_msg('encode', enc_msg)
comparator.add_msg('encode_seq', enc_msg_seq)
comparator.add_msg('encode_par', enc_msg_par )
comparator.compare()
