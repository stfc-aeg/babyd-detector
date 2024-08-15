from cffi import FFI
import sys


libdirs = ['/aeg_sw/work/projects/alpha-data/adxdma-driver-linux-0.11.0/api/linux/obj']
include_dirs = ['/aeg_sw/work/projects/alpha-data/adxdma-driver-linux-0.11.0/include']
libs = ['adxdma']

ffibuilder = FFI()

ffibuilder.set_source("xdma_cffi",
                      r"""
                      #define LINUX
                      #include "adxdma.h"
                      #include <stdint.h>
                      """,
                    libraries=libs,
                    include_dirs=include_dirs, library_dirs=libdirs
                      )

if __name__ == "__main":
    with open("pyxdma.h", "r") as header:
        header_info = header.read()
else:
    with open("../lib/pyxdma.h", "r") as header:
        header_info = header.read()

ffibuilder.cdef(header_info)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True, debug=False)