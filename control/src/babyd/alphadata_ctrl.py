
import logging

from odin.adapters.parameter_tree import ParameterTree

from babyd.adxdma import adxdma, Register

from functools import partial
import struct
import json


class AlphaDataController():

    def __init__(self, reg_file) -> None:

        self.xdma = adxdma()
        # mapper = RegisterMapper(reg_file)
        with open(reg_file, 'r') as openfile:
            reg_dict = json.load(openfile)

        self.registers = {}

        for map in reg_dict:
            self.registers[map] = {}
            for reg in reg_dict[map]:
                register = reg_dict[map][reg]
                self.registers[map][reg] = Register(register["addr"], register["size"], register['readonly'], register.get("fields"))

        self.param_tree = None

        # logging.debug(mapper.reg_dict.keys())
        # self.registers = mapper.reg_dict

        self._params = {
            "control": {
                "is_connected": (lambda: self.xdma.is_connected, None),
                "connect": (None, self.connect_device),
                "disconnect": (None, self.disconnect_device),
            },
            "registers": {key.lower(): {
                reg_name: {
                    **reg.param_tree,
                    "value": (partial(self.read_reg, register=reg),
                              None if reg.readonly else (partial(self.write_reg, register=reg))),
                    "fields": None if not reg.fields else {
                        field_name: (partial(self.read_field, register=reg, field_addr=field_addr),
                                     None if reg.readonly else (partial(self.write_field, register=reg, field_addr=field_addr)))
                        for field_name, field_addr in reg.fields.items()}
                } for reg_name, reg in value.items()
            } for key, value in self.registers.items()}
        }

    def init_tree(self):
        self.param_tree = ParameterTree(self._params)

    def add_param(self, name: str, args):
        self._params["control"][name] = args

    def connect_device(self, _):
        self.xdma.connect()
        self.xdma._openWindow()
        self.xdma._openDMAEngine()

    def disconnect_device(self, _):
        self.xdma._closeDMAEngine()
        self.xdma._closeWindow()
        self.xdma.disconnect()

    def read_reg(self, register: Register):
        if not self.xdma.is_connected:
            return register.value
        register.value = self.xdma.read(register.addr, register.length, register.word_size)
        return register.value
    
    def write_reg(self, value, register: Register):
        if not self.xdma.is_connected or register.readonly:
            return
        logging.debug("Writing Reg with Word size {}".format(register.word_size))
        self.xdma.write(register.addr, value, register.length, register.word_size)
        return self.read_reg(register)

    def read_field(self, register: Register, field_addr):
        struct_format = "<" + ("I" * len(register.value))
        value = int.from_bytes(struct.pack(struct_format, *register.value), "little")
        if isinstance(field_addr, (tuple, list)):
            lo, hi = field_addr

            value = value >> lo
            mask = ~(~0 << (1 + hi - lo))
            extracted_bits = value & mask

            return extracted_bits
        else:
            return 1 if (1 << field_addr) & value else 0

    def write_field(self, value, register: Register, field_addr):
        # is it safe to assume the value in the register is the most up-to-date val available?
        struct_format = "<" + ("I" * len(register.value))
        reg_val = int.from_bytes(struct.pack(struct_format, *register.value), "little")

        if isinstance(field_addr, (tuple, list)):
            lo, hi = field_addr
            bit_len = value.bit_length()
            if bit_len > (1 + hi - lo):
                # value provided is too big to fit into the bitspace given for this field
                return
            # mask out just the bits we are interested in
            mask = ~(~0 << hi << 1) & (~0 << lo)

            # get original val in correct position within reg val
            org_val = reg_val & mask
            # XOR original val, to set the bits we're intereted in to zeros
            reg_val = reg_val ^ org_val
            # or with new val to set the required bits
            reg_val = reg_val | (value << lo)
        else:
            # set, or unset, the field depending on the new value
            reg_val = (reg_val | (1 << field_addr)) if value else (reg_val & ~(1 << field_addr))
        
        # split the value back up int 4 byte words
        reg_val = reg_val.to_bytes(register.length, "little")
        reg_val = list(struct.unpack(struct_format, reg_val))

        self.write_reg(reg_val, register)