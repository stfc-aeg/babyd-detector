

class XdmaException(Exception):
    
    def __init__(self, code, message) -> None:
        super().__init__(code)
        self.code = code
        self.message = message


class xdma():

    def __init__(self, **kwargs):
        self.is_connected = False

    def connect(self):
        raise XdmaException(code=0, message="Connect Method not initialised")

    def disconnect(self):
        raise XdmaException(code=0, message="Disconnect Method not initialised")

    def read(self, addr, length):
        raise XdmaException(code=0, message="Read Method not initialised")

    def write(self, addr, value, length=0):
        raise XdmaException(code=0, message="Write Method not initialised")

    def read_dma(self, addr, length):
        raise XdmaException(code=0, message="Read DMA Method not initialised")

    def write_dma(self, addr, value, length=0):
        raise XdmaException(code=0, message="Write DMA Method not initialised")

    def __close__(self):
        self.disconnect()

