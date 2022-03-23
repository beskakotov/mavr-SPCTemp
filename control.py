from re import L
from tkinter.messagebox import RETRY
import pywinusb.hid as hid
from time import sleep

class RODOS:
    __device__ = hid.HidDeviceFilter(vendor_id=0x16c0).get_devices()[0]
    __device__.open()
    __report__ = __device__.find_feature_reports()[0]
    __inputbuffer__ = [0]*9
    __outputbuffer__ = [0]*9
    __sensors__ = []
    __result__ = False
    __precisions__ = (0x00, 0x20, 0x40, 0x60)

    @classmethod
    def clear_buffer(cls):
        __inputbuffer__ = [0]*9
        __outputbuffer__ = [0]*9

    @classmethod
    def send_report(cls):
        report_id =tuple(cls.__report__.keys())[0]
        cls.__report__[report_id] = cls.__outputbuffer__[1:]
        cls.__report__.send()
        sleep(0.01)
        cls.__inputbuffer__ = cls.__report__.get()

    @classmethod
    def set_port(cls, value): # __result__ +
        cls.clear_buffer()
        if 0 <= value <= 24 and value % 8 == 0 and isinstance(value, int):
            cls.__outputbuffer__[1] = 0xE7
            cls.__outputbuffer__[2] = value
            cls.send_report()
            cls.__result__ = (cls.__inputbuffer__[1] == 0xE7) & (cls.__inputbuffer__[2] == value) & (cls.__inputbuffer__[3] == value)
        else:
            raise ValueError('ERROR #1')
        
    @classmethod
    def get_port(cls): # __result__ +
        cls.clear_buffer()
        cls.__outputbuffer__[1] = 0x7E
        cls.send_report()
        value = cls.__inputbuffer__[2]
        cls.__result__ = True
        if cls.__result__:
            return value
        else:
            raise ValueError('ERROR #2')

    @classmethod
    def search_sensors(cls):
        cls.__sensors__ = []
        cls.__search_sensors__(0, 0)
    
    @classmethod
    def __search_sensors__(cls, NEXT_ROM, PL):
        cls.__result__ = False
        CL = [False] * 64
        RL = [0] * 64
        B1 = 1
        ROM = 0

        cls.__ow_reset__()
        cls.__ow_write_byte__(0xF0)

        if not cls.__result__:
            raise ValueError("ERROR #3")

        for i in range(64):
            if cls.__result__:
                read_2bit = cls.__ow_read_2bit__()
                if read_2bit&0x03 == 0:
                    if PL < i:
                        CL[i] = True
                        RL[i] = ROM
                    elif PL >= i:
                        BIT = (NEXT_ROM >> i) & 0x01
                    else:
                        BIT = 0
                    cls.__ow_write_bit__(BIT)
                    if not cls.__result__:
                        break
                    if BIT == 1:
                        ROM = ROM + (B1 << i)

                elif read_2bit&0x03 == 1:
                    cls.__ow_write_bit__(0x01)
                    if cls.__result__:
                        ROM = ROM + (B1 << i)

                elif read_2bit&0x03 == 2:
                    cls.__ow_write_bit__(0x00)
                    if not cls.__result__:
                        break

                elif read_2bit&0x03 == 3:
                    cls.__result__ = False
                    break
                else:
                    raise ValueError('Unknown error #1')

            else:
                raise ValueError('Unknown error #2')
            
            if not cls.__result__:
                break

        if ROM == 0:
            cls.__result__ = False
        
        if cls.__result__:
            CRC = 0
            for j in range(8):
                CRC = cls.__CRC8__(CRC, (ROM >> (j*8)) & 0xFF)
            cls.__result__ = CRC == 0
        
        if cls.__result__:
            cls.__sensors__.append(ROM)
        
        for i in range(64):
            if CL[i]:
                cls.__search_sensors__(RL[i] | (B1 << i), i)
    
    @classmethod
    def __match_rom__(cls, ROM):
        cls.__result__ = False
        cls.__ow_reset__()
        cls.__ow_write_byte__(0x55)
        cls.__ow_write_4byte__(ROM & 0xFFFFFFFF)
        cls.__ow_write_4byte__((ROM >> 32) & 0xFFFFFFFF)

    @classmethod
    def __get_temperature__(cls, ROM):
        FAMILY = ROM & 0xFF
        cls.__result__ = False
        cls.__match_rom__(ROM)
        if cls.__result__:
            cls.__ow_write_byte__(0xBE)
            L1 = cls.__ow_read_4byte__()
            L2 = cls.__ow_read_4byte__()
            L3 = cls.__ow_read_byte__()
            CRC = 0
            for i in range(4):
                CRC = cls.__CRC8__(CRC, (L1 >> (i * 8)) & 0xFF)
            for i in range(4):
                CRC = cls.__CRC8__(CRC, (L2 >> (i * 8)) & 0xFF)
            CRC = cls.__CRC8__(CRC, L3)
            cls.__result__ = CRC == 0 
            K = L1 & 0xFFFF
            T = 1000
            if FAMILY == 0x28 or FAMILY == 0x22:
                T = K * 0.0625
            elif FAMILY == 0x10:
                T = K * 0.5
            if cls.__result__:
                return T
        return 1000            

    @classmethod
    def __CRC8__(cls, CRC, D):
        R = CRC
        for i in range(8):
            if (R ^ (D >> i)) & 0x01 == 0x01:
                R = ((R ^ 0x18) >> 1) | 0x80
            else:
                R = (R >> 1) & 0x7F
        return R

    @classmethod
    def __ow_reset__(cls): # __result__ +
        cls.clear_buffer()
        cls.__outputbuffer__[1] = 0x18
        cls.__outputbuffer__[2] = 0x48
        cls.send_report()
        __result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x48) & (cls.__inputbuffer__[3] == 0x00)

    @classmethod
    def __ow_read_bit__(cls):
        raise NotImplementedError("МЕТОД НЕ ОПИСАН!!!")

    @classmethod
    def __ow_read_2bit__(cls): # __result__ +
        cls.clear_buffer()
        cls.__outputbuffer__[1] = 0x18
        cls.__outputbuffer__[2] = 0x82
        cls.__outputbuffer__[3] = 0x01
        cls.__outputbuffer__[4] = 0x01
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x82)
        return (cls.__inputbuffer__[3] & 0x01) + ((cls.__inputbuffer__[4] << 1) & 0x02)

    @classmethod
    def __ow_read_byte__(cls):
        cls.clear_buffer()
        cls.__outputbuffer__[1]=0x18
        cls.__outputbuffer__[2]=0x88
        cls.__outputbuffer__[3]=0xFF
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x88)
        return cls.__inputbuffer__[3]

    @classmethod
    def __ow_read_4byte__(cls):
        cls.clear_buffer()
        cls.__outputbuffer__[1]=0x18
        cls.__outputbuffer__[2]=0x84
        cls.__outputbuffer__[3]=0xFF
        cls.__outputbuffer__[4]=0xFF
        cls.__outputbuffer__[5]=0xFF
        cls.__outputbuffer__[6]=0xFF
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x84)
        return cls.__inputbuffer__[3] + (cls.__inputbuffer__[4] << 8) + (cls.__inputbuffer__[5] << 16) + (cls.__inputbuffer__[6] << 24)
        
    @classmethod
    def __ow_write_bit__(cls, B): # __result__ +
        cls.clear_buffer()
        cls.__outputbuffer__[1] = 0x18
        cls.__outputbuffer__[2] = 0x81
        cls.__outputbuffer__[3] = B & 0x01
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x81) & ((cls.__inputbuffer__[3] & 0x01) == (B & 0x01))
        
    @classmethod
    def __ow_write_byte__(cls, B): # __result__ +
        cls.clear_buffer()
        cls.__outputbuffer__[1] = 0x18
        cls.__outputbuffer__[2] = 0x88
        cls.__outputbuffer__[3] = B
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1] == 0x18) & (cls.__inputbuffer__[2] == 0x88) & (cls.__inputbuffer__[3] == B)
    
    @classmethod
    def __ow_write_4byte__(cls, B):
        cls.__result__ = False
        D0 = B & 0xFF
        D1 = (B >> 8) & 0xFF
        D2 = (B >> 16) & 0xFF
        D3 = (B >> 24) & 0xFF
        cls.clear_buffer()
        cls.__outputbuffer__[1] =0x18
        cls.__outputbuffer__[2] =0x84
        cls.__outputbuffer__[3] = D0
        cls.__outputbuffer__[4] = D1
        cls.__outputbuffer__[5] = D2
        cls.__outputbuffer__[6] = D3
        cls.send_report()
        cls.__result__ = (cls.__inputbuffer__[1]==0x18) & \
                            (cls.__inputbuffer__[2] == 0x84) & \
                            (cls.__inputbuffer__[3] == D0) & \
                            (cls.__inputbuffer__[4] == D1) & \
                            (cls.__inputbuffer__[5] == D2) & \
                            (cls.__inputbuffer__[6] == D3)
    
    @classmethod
    def __skip_rom_convert__(cls):
        cls.__result__ = False
        cls.__ow_reset__()
        cls.__ow_write_byte__(0xCC)
        cls.__ow_write_byte__(0x44)

    @classmethod
    def __skip_rom__(cls):
        pass

    @classmethod
    def __set_temperature_precision__(cls, V):
        if not 0 <= V <= 3:
            raise ValueError('Wrong value of precision [0, 3]')
        all_results = []
        cls.__skip_rom__()
        all_results.append(bool(cls.__result__))
        cls.__ow_write_byte__(0x4e)
        all_results.append(bool(cls.__result__))
        cls.__ow_write_byte__(0x00)
        all_results.append(bool(cls.__result__))
        cls.__ow_write_byte__(0xFF)
        all_results.append(bool(cls.__result__))
        cls.__ow_write_byte__(cls.__precisions__[V])
        all_results.append(bool(cls.__result__))
        cls.__skip_rom__()
        all_results.append(bool(cls.__result__))
        cls.__ow_write_byte__(0x48)
        all_results.append(bool(cls.__result__))


        if not all(all_results):
            raise ValueError('ERROR OF SET UP PRECISION')
        
        
