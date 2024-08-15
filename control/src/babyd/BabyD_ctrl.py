from odin.adapters.parameter_tree import ParameterTreeError

from BabyD.alphadata_ctrl import AlphaDataController
from functools import partial
import struct

import logging

class BabyDController(AlphaDataController):

    def __init__(self, reg_file):
        super(BabyDController, self).__init__(reg_file)

        # add references to required registers for Acquisition Control
        self.ip_local = self.registers['UDP']['IP_LOCAL']
        self.ip_remote = self.registers['UDP']['IP_REMOTE']
        self.data_rate = self.registers['AURORA']['CTRL']
        self.link0_status = self.registers['AURORA']['CORE0_STATUS']
        self.link1_status = self.registers['AURORA']['CORE1_STATUS']
        self.clockA_period = self.registers["IIC"]["CLOCKA_PERIOD"]
        self.clockB_period = self.registers["IIC"]["CLOCKB_PERIOD"]

        self.digest = self.registers["AUTH"]["DIGEST"]
        self.dna = self.registers["AUTH"]["PUF_ID"]

        self.clock_ref = self.registers["AURORA"]["REFCLK_FREQ"]

        self.frame_count_ch0 = self.registers['FRAMER']['STATS_CH0_NFRAMES']
        self.frame_count_ch1 = self.registers['FRAMER']['STATS_CH1_NFRAMES']

        self.mac_sent = self.registers["UDP"]["MAC_NFRAMES_SENT"]

        self.add_param("ip_local", (partial(self.get_ip_addr, register=self.ip_local),
                                    partial(self.set_ip_addr, register=self.ip_local)))
        self.add_param("ip_remote", (partial(self.get_ip_addr, register=self.ip_remote),
                                     partial(self.set_ip_addr, register=self.ip_remote)))
        self.add_param('link_status', {
            "link0": {field_name: (partial(self.read_field, register=self.link0_status, field_addr=field_addr), None)
                      for field_name, field_addr in self.link0_status.fields.items()},
            "link1": {field_name: (partial(self.read_field, register=self.link1_status, field_addr=field_addr), None)
                      for field_name, field_addr in self.link1_status.fields.items()}
        })

        self.add_param("digest", (partial(self.read_reg, register=self.digest), None))

        self.clock_speeds = {
            2.5: 0x441e9db,
            3.0: 0x51be5e0,
            3.5: 0x5f5e100,
            4.0: 0x6cfdc92,
            4.1: 0x6fb7549,
            4.2: 0x7270e00,
            5.0: 0x883d3b6,
            7.0: -1,
             14: -1
        }

        self.add_param("clock_speed", {
            "options": (list(self.clock_speeds.keys()), None),
            "speed": (self.get_clock_speed, self.set_clock_speed)
        })

        self.add_param("frame_count", {
            "ch0": (partial(self.read_reg_value, register=self.frame_count_ch0), None),
            "ch1": (partial(self.read_reg_value, register=self.frame_count_ch1), None)
        })

        # self.add_param("mac_sent", (partial(self.read_reg_value, register=self.mac_sent), None))

    def get_ip_addr(self, register):
        val = self.read_reg(register)[0].to_bytes(4, "little")

        return "{}.{}.{}.{}".format(val[3], val[2], val[1], val[0])

    def set_ip_addr(self, ip, register):
        try:
            vals = [int(x) for x in ip.split(".")]
            val = vals[0] << 24 | vals[1] << 16 | vals[2] << 8 | vals[3]
            logging.debug(val)
            self.write_reg([val], register)

        except ValueError as e:
            raise ParameterTreeError(e)

    def get_clock_speed(self):
        rate_val = self.read_field(self.data_rate, (16, 17))
        clock_ref = self.read_reg(self.clock_ref)[0]
        if rate_val == 0:
            return 14.0
        elif rate_val == 1:
            return 7.0

        for speed, reg_val in self.clock_speeds.items():
            # if we reach here, then it's a custom speed
            if reg_val == clock_ref:
                return speed

        return -1

    def set_clock_speed(self, speed):
        logging.debug("Setting Clock Speed to %d", speed)
        if speed == 14:
            logging.debug("clock speed 14")
            self.write_field(0, self.data_rate, (16, 17))
        elif speed == 7:
            logging.debug("clock speed 7")
            self.write_field(1, self.data_rate, (16, 17))
        else:
            try:
                logging.debug("clock speed special")
                self.write_field(2, self.data_rate, (16, 17))
                self.write_reg([self.clock_speeds[speed]], self.clock_ref)
            except ValueError as e:
                raise ParameterTreeError(e)

    def read_reg_value(self, register):
        val = self.read_reg(register)
        if len(val) == 1:
            return val[0]

        else:
            full_val_byte = struct.pack("I"*len(val), *val)
            return int.from_bytes(full_val_byte, "little")
