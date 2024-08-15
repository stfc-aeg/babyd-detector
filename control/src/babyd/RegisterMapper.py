from babyd.adxdma import adxdma, AdxdmaException, Register


import csv
import json

import logging
import re


class RegisterMapper():

    def __init__(self, file_path, reg_name_prefix="\w*_C_REG_([A-Z]+)_(\w+)_[ABE]", read=None, write=None) -> None:

        self.reg_dict = {}
        self.json_dict = {}
        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)
            current_map = ""
            current_reg = ""
            current_addr = ""
            current_size = 0
            fields = []
            for row in reader:
                # 0: name, 1: addr/bit, 2: size/num_bits, 3: comment(can ignore)
                name = row[0]
                addr = int(row[1], 0)
                size = int(row[2], 0) if row[2] else None

                if name.endswith("_A"):
                    # its a register. save previous register
                    if current_reg:
                        if current_map not in self.reg_dict:
                            logging.debug("NEW REG MAP SECTION: %s", current_map)
                            self.reg_dict[current_map] = {}
                        self.reg_dict[current_map][current_reg] = Register(current_addr, current_size, "STATUS" in current_reg, fields)
                        # else:
                            # self.reg_dict[current_map][current_reg] = DetailedRegister(current_addr, current_size, read, write,
                                                                                    #    fields, "STATUS" in current_reg)
                    # previous register saved. Save new register
                    # current_reg = self.remove_suffix(name, "_A")
                    x = re.search(reg_name_prefix, name)
                    # current_reg = self.remove_prefix(current_reg, reg_name_prefix)
                    current_map = x.group(1)
                    current_reg = x.group(2)
                    # logging.debug("NEW REGISTER FOUND: %s", current_reg)
                    current_addr = addr
                    current_size = size if size else 4
                    fields = {}

                elif name.endswith("_B"):
                    # its a bit def. add it to the current bit defs for the current reg
                    bit = addr if not size or size == 1 else (addr, addr + size-1)
                    x = re.search(reg_name_prefix, name)
                    bit_name = x.group(2)
                    bit_name = self.remove_prefix(bit_name, current_reg + "_")
                    # bit_name = self.remove_suffix(bit_name, "_B")
                    # entry = (bit_name, bit)
                    # logging.debug("BIT {}, NAME: {}".format(bit, bit_name))
                    fields[bit_name] = bit

        with open("reg_def.json", "w") as outfile:
            json.dump(self.reg_dict, outfile)

    def remove_prefix(self, text, prefix):
        if text.startswith(prefix):
            return text[len(prefix):]
        else:
            return text
        
    def remove_suffix(self, text, suffix):
        if text.endswith(suffix):
            return text[:-len(suffix)]


class RegisterMapperJson():

    def __init__(self, file_path, reg_name_prefix="\w*_C_REG_([A-Z]+)_(\w+)_[ABE]"):
        self.json_dict = {}

        with open(file_path) as csvfile:
            reader = csv.reader(csvfile)

            map = ""
            reg = ""
            for row in reader:
                name = row[0]
                addr = int(row[1], 0)
                size = int(row[2], 0) if row[2] else None

                if name.endswith("_A"):
                    x = re.search(reg_name_prefix, name)
                    map = x.group(1)
                    reg = x.group(2)
                    if x.group(1) not in self.json_dict:
                        self.json_dict[map] = {}
                    self.json_dict[map][reg] = {}
                    self.json_dict[map][reg]["addr"] = addr
                    self.json_dict[map][reg]["size"] = size if size else 4
                    self.json_dict[map][reg]['readonly'] = "STATUS" in reg
                
                elif name.endswith("_B"):
                    x = re.search(reg_name_prefix, name)

                    field = x.group(2)
                    if field.startswith(reg):
                        # removes the prefix
                        field = field[len(reg + "_"):]
                        if "fields" not in self.json_dict[map][reg]:
                            self.json_dict[map][reg]["fields"] = {}
                        self.json_dict[map][reg]["fields"][field] = addr if not size or size == 1 else (addr, addr + size-1)
                    else:
                        # if the field is for whatever reason not in the correct order
                        pass
        
        with open("reg_def.json", "w") as outfile:
            json.dump(self.json_dict, outfile)





if __name__ == "__main__":
    print("Reading CSV File: ")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    mapper = RegisterMapperJson("/u/wbd45595/adxdma_doc/reg_def.csv")