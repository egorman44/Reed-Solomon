from reedsolo import rs_encode_msg
from reedsolo import rs_calc_syndromes
from reedsolo import rs_find_error_locator
from reedsolo import rs_find_errors
from reedsolo import rs_correct_errata
from reedsolo import rs_correct_msg_nofsynd
from reedsolo import init_tables

from packet import Packet
import copy

class RsPacketsBuilder():

    def __init__(self, K_LEN, REDUNDANCY, FCR, msg_patterm='random'):
        init_tables()
        self.K_LEN = K_LEN
        self.REDUNDANCY = REDUNDANCY
        self.FCR = FCR
        self._builder = {}
        self._pkt_cntr = None
        self._msg_pattern = msg_patterm
        self.register_rs_pkt()

    # Register packets
    def register_rs_pkt(self):
        self._builder['sAxisIf'] = self.get_cor_msg
        self._builder['syndIf'] = self.get_syndrome
        self._builder['errLocIf'] = self.get_err_locator
        self._builder['errPosIf'] = self.get_err_pos
        self._builder['errValIf'] = self.get_err_val
        self._builder['errPosOutIf'] = self.get_err_pos
        
    def generate_msg(self):
        if self._pkt_cntr is None:
            self._pkt_cntr = 0
        else:
            self._pkt_cntr += 1
        self.ref_msg = Packet(name=f'ref_msg{self._pkt_cntr}')
        self.ref_msg.generate(pkt_size=self.K_LEN, pattern=self._msg_pattern, delay=0)
        self.ref_msg.print_pkt()
        
    def encode_msg(self):
        enc_msg = list(rs_encode_msg(msg_in=self.ref_msg.data, fcr=self.FCR,nsym=self.REDUNDANCY))
        self.enc_msg = Packet(name=f'enc_msg{self._pkt_cntr}')
        self.enc_msg.write_data(enc_msg, delay=0)
        
    def corrupt_msg(self, positions, errors=None):
        self.cor_msg = copy.deepcopy(self.enc_msg)
        self.cor_msg.name = f"cor_msg{self._pkt_cntr}"
        self.cor_msg.corrupt_pkt(positions=positions, errors=errors)
        self.cor_msg.compare(self.enc_msg)
        self.cor_msg.print_pkt()
        print(self.cor_msg.data)

    ''' Generate RS packets '''
    
    def get_pkt(self, if_name):
        gen_func = self._builder.get(if_name)
        if not gen_func:
            raise ValueError(f"Not expected value for if_name = {if_name}.")
        return gen_func()
        
    def get_cor_msg(self):
        return self.cor_msg
    
    def get_syndrome(self):
        syndrome = rs_calc_syndromes(self.cor_msg.data, self.REDUNDANCY, self.FCR)
        syndrome.pop(0)
        synd_pkt = Packet(name=f'synd_pkt{self._pkt_cntr}')
        synd_pkt.write_data(ref_data=syndrome)
        return synd_pkt

    def get_err_locator(self):
        syndrome = rs_calc_syndromes(self.cor_msg.data, self.REDUNDANCY, self.FCR)
        error_locator = rs_find_error_locator(syndrome, self.REDUNDANCY)
        error_locator = error_locator[::-1]
        err_loc_pkt = Packet(name=f'err_loc_pkt{self._pkt_cntr}')
        err_loc_pkt.write_data(ref_data=error_locator)
        return err_loc_pkt

    def get_err_pos(self):
        syndrome = rs_calc_syndromes(self.cor_msg.data, self.REDUNDANCY, self.FCR)
        print(f"syndrome: {syndrome}")
        if all(x == 0 for x in syndrome):
            return None
        else:
            error_locator = rs_find_error_locator(syndrome, self.REDUNDANCY)
            error_locator = error_locator[::-1]
            error_position = rs_find_errors(err_loc=error_locator,nmess=len(self.enc_msg.data))
            err_pos_pkt = Packet(name=f'err_pos_pkt{self._pkt_cntr}')
            err_pos_pkt.write_data(ref_data=error_position)
            return err_pos_pkt

    def get_err_val(self):
        syndrome = rs_calc_syndromes(self.cor_msg.data, self.REDUNDANCY, self.FCR)
        if all(x == 0 for x in syndrome):
            return None
        else:
            error_locator = rs_find_error_locator(syndrome, self.REDUNDANCY)
            error_locator = error_locator[::-1]
            error_position = rs_find_errors(err_loc=error_locator,nmess=len(self.enc_msg.data))
            _, magnitude = rs_correct_errata(msg_in=self.cor_msg.data, synd=syndrome, err_pos=error_position, fcr=self.FCR)
            err_val_pkt = Packet(name=f'err_val_pkt{self._pkt_cntr}')
            err_val_pkt.write_data(ref_data=magnitude)
            return err_val_pkt
