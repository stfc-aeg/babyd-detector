from xdma_cffi import ffi, lib

import logging
import numpy as np

import sys
import struct
from functools import partial

from BabyD.xdma import xdma, XdmaException
# import struct


class AdxdmaException(XdmaException):
    message_lookup = {
            lib.ADXDMA_SUCCESS:                "success",
            lib.ADXDMA_STARTED:                "Asynchronous operation started without error",
            lib.ADXDMA_TRUNCATED:              "Operation transferred some, but not all of the requested bytes",
            lib.ADXDMA_INTERNAL_ERROR:         "An error in the API logic was detected",
            lib.ADXDMA_UNEXPECTED_ERROR:       "An unexpected error caused the operation to fail",
            lib.ADXDMA_BAD_DRIVER:             "The driver might not be correctly installed",
            lib.ADXDMA_NO_MEMORY:              "Couldn't allocate memory required to complete operation",
            lib.ADXDMA_ACCESS_DENIED:          "The calling process does not have permission to perform the operation",
            lib.ADXDMA_DEVICE_NOT_FOUND:       "Failed to open the device with the specified index",
            lib.ADXDMA_CANCELLED:              "The operation was aborted due to software-requested cancellation",
            lib.ADXDMA_HARDWARE_ERROR:         "The operation failed due to an error in the hardware",
            lib.ADXDMA_HARDWARE_RESET:         "The operation was aborted the hardware being reset",
            lib.ADXDMA_HARDWARE_POWER_DOWN:    "The operation was aborted due to a hardware power-down event",
            lib.ADXDMA_INVALID_PARAMETER:      "The primary parameter to the function was invalid",
            lib.ADXDMA_INVALID_FLAG:           "A flag was invalid or not recognized",
            lib.ADXDMA_INVALID_HANDLE:         "The device handle was invalid",
            lib.ADXDMA_INVALID_INDEX:          "The index parameter was invalid",
            lib.ADXDMA_NULL_POINTER:           "A NULL pointer was passed where non-NULL was required",
            lib.ADXDMA_NOT_SUPPORTED:          "The hardware or the ADXDMA driver does not support the requested operation",
            lib.ADXDMA_WRONG_HANDLE_TYPE:      "The wrong kind of handle was supplied for an API function",
            lib.ADXDMA_TIMEOUT_EXPIRED:        "The user-supplied timeout value was exceeded",
            lib.ADXDMA_INVALID_SENSITIVITY:    "At least one bit in the sensitivity parameter refers to a non-existent User Interrupt",
            lib.ADXDMA_INVALID_MAPPING:        "The virtual base address to be unmapped from the process' address space was not recognized",
            lib.ADXDMA_INVALID_WORD_SIZE:      "The word size specified was not valid",
            lib.ADXDMA_INVALID_REGION:         "The requested region was partially or completely out of bounds",
            lib.ADXDMA_REGION_OS_LIMIT:        "The requested region exceeded a system-imposed limit",
            lib.ADXDMA_LOCK_LIMIT:             "The limit on the number of locked buffers has been reached",
            lib.ADXDMA_INVALID_BUFFER_HANDLE:  "An invalid locked buffer handle was supplied",
            lib.ADXDMA_NOT_BUFFER_OWNER:       "Attempt to unlock a buffer owned by a different device handle",
            lib.ADXDMA_DMAQ_NOT_IDLE:          "Attempt to change DMA queue configuration when it was not idle",
            lib.ADXDMA_INVALID_DMAQ_MODE:      "Invalid DMA Queue mode requested",
            lib.ADXDMA_DMAQ_OUTSTANDING_LIMIT: "Maximum outstanding DMA transfer count reached",
            lib.ADXDMA_INVALID_DMA_ALIGNMENT:  "Invalid address alignment, or length is not an integer multiple of length granularity",
            lib.ADXDMA_EXISTING_MAPPING:       "At least one Window mapping exists, preventing safe reset",
            # lib.ADXDMA_ALREADY_CANCELLING:   "Currently not used",
            lib.ADXDMA_DEVICE_BUSY:            "Attempting to perform an operation while there is already one in progress",
            lib.ADXDMA_DEVICE_IDLE:            "Attempting to join a non-existent operation",
            lib.ADXDMA_C2H_TLAST_ASSERTED:     "At least one DMA descriptor was closed early by C2H user logic asserting TLAST"
    }

    def __init__(self, error_code) -> None:
        message = AdxdmaException.message_lookup[error_code]
        super().__init__(error_code, message)

    def __str__(self) -> str:
        return self.message


class adxdma(xdma):

    def __init__(self, **kwargs):
        super(adxdma, self).__init__(**kwargs)

        self.device = ffi.new("ADXDMA_HDEVICE *")
        self.window = ffi.new("ADXDMA_HWINDOW *")
        self.dma_engine = ffi.new("ADXDMA_HDMA *")

        self.device_index = kwargs.get('device_index', 0)

    def connect(self):
        status = lib.ADXDMA_Open(0, False, self.device)
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)
        else:
            self.is_connected = True
        self._openWindow()
        self._openDMAEngine()

    def disconnect(self):
        self._closeWindow()
        self._closeDMAEngine()

        status = lib.ADXDMA_Close(self.device[0])
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)
        else:
            self.is_connected = False

    def read(self, addr, length, word_size=4):
        if not self.is_connected or self.window == -1:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)
        complete = ffi.new("ADXDMA_COMPLETION *")
        # 4 is the standard word size for reading
        # word_size = 4
        buf_length = length//word_size
        if not buf_length:
            buf_length = 1
        if word_size == 4:
            dtype = np.uint32
        elif word_size == 2:
            dtype = np.uint16
        else:
            dtype = np.uint8
        buf = np.zeros(int(buf_length), dtype=dtype)
        point = ffi.from_buffer("uint32_t[]", buf)

        status = lib.ADXDMA_ReadWindow(self.window[0], 0, word_size, addr, length, point, complete)
        if status >= 0x100:
            # error occur
            raise AdxdmaException(status)
        elif status == lib.ADXDMA_TRUNCATED:
            # didnt read all the data asked for. check the complete struct for info
            logging.error("Read only {} of {} bytes".format(complete.Transferred, length))
            raise AdxdmaException(complete.Reason)

        return buf.tolist()
    
    def write(self, addr, value, length=0, word_size=4):
        if not self.is_connected or self.window == -1:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)
        if word_size == 4:
            struct_string = "I"  # 4 byte word
            buf_string = "uint32_t[]"
        elif word_size == 2:
            struct_string = "H"  # 2 byte word
            buf_string = "uint16_t[]"
        else:
            struct_string = "B"  # 1 byte word
            buf_string = "uint8_t[]"
        byte_data = struct.pack("@" + (struct_string * len(value)), *value)
        logging.debug(byte_data)

        point = ffi.from_buffer(byte_data)
        complete = ffi.new("ADXDMA_COMPLETION *")
        # word_size = 4
        length = len(byte_data) if length == 0 else length
        # logging.debug(length)

        logging.debug("Performing Write at {} of length {}, with a word length of {}".format(addr, byte_data, word_size))
        logging.debug("The start of data is aligned? {}".format(addr % word_size))
        logging.debug("The End of data is aligned?   {}".format((addr + length) % word_size))



        status = lib.ADXDMA_WriteWindow(self.window[0], 0, word_size, addr, length, point, complete)
        if status >= 0x100:
            raise AdxdmaException(status)
        elif status == lib.ADXDMA_TRUNCATED:
            logging.error("Wrote only {} of {} bytes".format(complete.Transferred, length))
            raise AdxdmaException

    def read_dma(self, addr, length):
        # return super().read_dma(addr, length)
        if not self.is_connected or self.dma_engine == -1:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)

        complete = ffi.new("ADXDMA_COMPLETION *")
        word_size = 4
        buf_length = length // word_size
        buf = np.zeros(int(buf_length), dtype=np.uint32)
        point = ffi.from_buffer("uint32_t[]", buf)

        status = lib.ADXDMA_ReadDMA(self.dma_engine[0], 0, addr, point, length, complete)

        if status >= 0x100:
            # error occur
            raise AdxdmaException(status)
        elif status == lib.ADXDMA_TRUNCATED:
            # didnt read all the data asked for. check the complete struct for info
            logging.error("Read only {} of {} bytes".format(complete.Transferred, length))
            raise AdxdmaException(complete.Reason)

        return buf.tolist()

    def write_dma(self, addr, value, length=0):
        if not self.is_connected or self.dma_engine == -1:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)
        
        byte_data = struct.pack("@" + ("I" * len(value)), *value)

        point = ffi.from_buffer("uint32_t[]", byte_data)
        complete = ffi.new("ADXDMA_COMPLETION *")
        length = len(byte_data) if length == 0 else length

        status = lib.ADXDMA_WriteDMA(self.dma_engine[0], 0, addr, point, length, complete)
        if status >= 0x100:
            raise AdxdmaException(status)
        elif status == lib.ADXDMA_TRUNCATED:
            logging.error("Wrote only {} of {} bytes".format(complete.Transferred, length))
            raise AdxdmaException

    def get_device_info(self):
        if not self.is_connected:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)

        device_info = ffi.new("ADXDMA_DEVICE_INFO *")

        status = lib.ADXDMA_GetDeviceInfo(self.device[0], device_info)
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)

        info = self._get_values_dict(device_info)

        return info

    def _openWindow(self, index=2):
        if not self.is_connected:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)
        status = lib.ADXDMA_OpenWindow(self.device[0], 0, False, index, self.window)
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)

    def _closeWindow(self):
        status = lib.ADXDMA_CloseWindow(self.window[0])
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)

    def _openDMAEngine(self, index=0, openH2C=False):
        if not self.is_connected:
            raise AdxdmaException(lib.ADXDMA_DEVICE_NOT_FOUND)
        status = lib.ADXDMA_OpenDMAEngine(self.device[0], 0, False, openH2C, index, self.dma_engine)
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)

    def _closeDMAEngine(self):
        status = lib.ADXDMA_CloseDMAEngine(self.dma_engine[0])
        if status != lib.ADXDMA_SUCCESS:
            raise AdxdmaException(status)

    def _get_values_dict(self, c_struct):
        return_val = {}
        type = ffi.typeof(c_struct)
        if type.kind == "pointer":
            type = type.item
        for field, fieldtype in type.fields:
            if fieldtype.type.kind == "struct":
                return_val[field] = self._get_values_dict(getattr(c_struct, field))
            elif fieldtype.type.kind == "array":
                return_val[field] = list(getattr(c_struct), field)
            else:
                return_val[field] = getattr(c_struct, field)
        return return_val


class Register():

    # length in bytes
    def __init__(self, addr: int, length: int, readonly=False, bitmap=None):
        self.addr = addr
        self.length = length
        if length % 4:
            if length % 2:
                self.word_size = 1
            else:
                self.word_size = 2
        else:
            self.word_size = 4
        self.value = [0] * int(length//self.word_size)
        self.readonly = readonly

        self.fields = bitmap

        self.param_tree = {
            "addr": (lambda: self.addr, None),
            "length": (lambda: self.length, None),
            "readonly": (lambda: self.readonly, None)
        }


class BitMapEntry():

    def __init__(self, bit: int, name: str, readonly=False):
        self.bit = bit
        self.name = name
        self.readonly = readonly


class DetailedRegister():

    def __init__(self, addr: int, length: int, read, write, bitmap: list = None, readonly=False):
        self.addr = addr
        self.length = length
        self.value = [0] * int(length // 4)
        self.bitmap = bitmap  # bitmap is assumed to be a list of BitMapEntry

        self.read = read
        self.write = write

        self.readonly = readonly

        self.bits_param_tree = None
        if self.bitmap:
            self.bits_param_tree = {
                entry.name: (partial(self.get_bit, bit=entry.bit),
                             None if entry.readonly else partial(self.set_bit, bit=entry.bit))
                for entry in self.bitmap
            }
        self.param_tree = {
            "addr": (lambda: self.addr, None),
            # "length": (lambda: self.length, None),
            "value": (self.read_val, self.set_val if not readonly else None),
            "bits": self.bits_param_tree,
            "readonly": (lambda: self.readonly, None)
        }

    def read_val(self):
        try:
            self.value = self.read(addr=self.addr, length=self.length)
        except XdmaException:
            pass
        return self.value

    def set_val(self, value: int):
        if self.readonly:
            return
        self.value = value
        self.write(addr=self.addr, value=self.value)
        self.read_val()

    def set_bit(self, value, bit: int):
        # https://stackoverflow.com/questions/12173774/how-to-modify-bits-in-an-integer
        if self.readonly or bit not in [x.bit for x in self.bitmap]:
            return
        reg_val_list = self.read_val()
        struct_format_string = "@" + ('I' * len(reg_val_list))
        reg_val = struct.pack(struct_format_string, *reg_val_list)
        # logging.debug(struct_format_string)
        reg_val = int.from_bytes(reg_val, "little")

        if isinstance(bit, tuple):
            lo, hi = bit
            val_bit_len = value.bit_length()
            if val_bit_len > (1 + hi - lo):
                # value is too big to fit into the bitspace given
                return
            # get mask for just the bits we're interested in
            mask = ~(~0 << hi << 1) & (~0 << lo)
            #get original val
            org_val = reg_val & mask
            #XOR orignal val, to set all bits we're interested in to zero
            reg_val = reg_val ^ org_val
            # or with new val to set the required bits
            reg_val = reg_val | (value << lo)
        else:
            # modify bit. If val = true, or with the bit to set it to 1. else, and with the inverse of the bit
            reg_val = (reg_val | (1 << bit)) if value else (reg_val & ~(1 << bit))
            
        # write value back
        reg_val = reg_val.to_bytes(self.length, 'little')
        logging.debug(reg_val)
        reg_val = list(struct.unpack(struct_format_string, reg_val))
        logging.debug(reg_val)
        self.set_val(reg_val)

    def get_bit(self, bit):
        value = int.from_bytes(struct.pack("<" + ("I" * len(self.value)), *self.value), "little")
        if isinstance(bit, tuple):
            lo, hi = bit
            
            value = value >> lo

            mask = ~(~0 << (1+hi-lo))
            extract_bits = value & mask

            return extract_bits
        else:
            return True if (1 << bit) & value else False

    def get_bitmap(self):
        return self.bitmap


if __name__ == "__main__":
    print("oooo test")

    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    # np.set_printoptions(formatter={"int":hex})

    libClass = adxdma()

    libClass.connect()
    libClass._openWindow()

    info = libClass.get_device_info()
    logger.debug(info)

    if sys.argv[1].startswith("0x"):
        addr = int(sys.argv[1][2:], 16)
    else:
        addr = int(sys.argv[1])

    if sys.argv[2].startswith("0x"):
        length = int(sys.argv[2][2:], 16)
    else:
        length = int(sys.argv[2])

    buf = libClass.readFromWindow(addr, length)
    with np.printoptions(formatter={"int": hex}):
        logger.debug(buf)
        # logger.debug(buf.astype(np.uint8).tostring().decode("ascii"))

    libClass._closeWindow()
    libClass.disconnect()
