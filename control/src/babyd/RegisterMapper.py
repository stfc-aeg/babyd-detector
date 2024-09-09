from babyd.adxdma import Register


import csv
import json
import sys

import logging
import re

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


class RegisterMapperHFile(RegisterMapperJson):

    def __init__(self, file_path, out_file, reg_name_prefix="\w*_C_REG_([A-Z]+)_(\w+)_[ABE]"):
        logging.debug("Reading registers from %s", file_path)
        self.json_dict = {}
        with open(file_path, "r") as file:
            map = ""
            reg = ""

            for row in file:
                row = row.split("//", 1)[0]

                parts = row.split()
                parts = list(filter(None, parts))

                #skip parts[0] as it will just be #define
                name = parts[1]
                addr = int(parts[2], 0)

                x = re.search(reg_name_prefix, name)

                if name.endswith("_A"):
                    
                    map = x.group(1)
                    reg = x.group(2)

                    if map not in self.json_dict:
                        self.json_dict[map] = {}
                    
                    self.json_dict[map][reg] = {}
                    self.json_dict[map][reg]["addr"] = addr
                    self.json_dict[map][reg]["size"] = 4
                    self.json_dict[map][reg]["readonly"] = "STATUS" in reg

                elif name.endswith("_B"):
                    field = x.group(2)

                    if field.startswith(reg):
                        # removes the prefix
                        field = field[len(reg + "_"):]
                        if "fields" not in self.json_dict[map][reg]:
                            self.json_dict[map][reg]["fields"] = {}
                        
                        self.json_dict[map][reg]["fields"][field] = addr

                    else:
                        # field is marked as belonging to a different register, find it
                        logging.debug("Searching for register for field %s", field)
                        for exist_reg in self.json_dict[map]:
                            if field.startswith(exist_reg):
                                field = field[len(exist_reg + "_"):]
                                if "fields" not in self.json_dict[map][exist_reg]:
                                    self.json_dict[map][exist_reg]['fields'] = {}
                                
                                self.json_dict[map][exist_reg]['fields'][field] = addr

        with open(out_file, "w") as outfile:
            json.dump(self.json_dict, outfile, indent=2)
            logging.debug("File Output to %s. Remember to go in and edit sizes of registers and fields",
                          out_file)




if __name__ == "__main__":
    print("Reading h File: ")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    input = sys.argv[1]
    output = sys.argv[2]

    mapper = RegisterMapperHFile(input, output)

    # mapper = RegisterMapperJson("/u/wbd45595/adxdma_doc/reg_def.csv")
