from babyd.adxdma import Register


import csv
import json

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


if __name__ == "__main__":
    print("Reading CSV File: ")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)

    mapper = RegisterMapperJson("/u/wbd45595/adxdma_doc/reg_def.csv")