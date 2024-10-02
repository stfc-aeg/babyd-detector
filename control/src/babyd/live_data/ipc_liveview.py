import logging
import numpy as np
from odin_data.control.ipc_tornado_channel import IpcTornadoChannel
from odin_data.control.ipc_channel import IpcChannelException
from tornado.escape import json_decode
from odin.util import convert_unicode_to_string

class IpcLiveView:
    """
    A class to handle live view frame data coming through IPC channels, and prepare it
    for visualisation with OdinGraph component.
    """
    def __init__(self, endpoint="tcp://127.0.0.1:5020", frame_height=16, frame_width=16, superframe_size=1000):
        """
        Initialize the IPC Live View object by connecting to the specified endpoint and
        setting the frame dimensions.

        :param endpoint: The IPC channel endpoint (default is localhost at port 5020).
        :param frame_height: The height of the frame (default is 16).
        :param frame_width: The width of the frame (default is 16).
        :parma superframe_size: The frame count of the superframe (defualt of 1000 for babyd)
        """
        self.endpoint = endpoint
        self.frame_height = frame_height
        self.frame_width = frame_width
        self.frame_data = None
        self.header = {}
        self.rendered_frame = None
        self.superframe_size = superframe_size

        # Initialize the SubSocket to handle continuous listening
        self.sub_socket = SubSocket(self, endpoint)
        logging.info(f"Listening for frames on endpoint: {self.endpoint}")

    def create_image_from_socket(self, msg):
        """
        Process incoming messages from the IPC channel, extract and prepare the frame data.
        :param msg: The multipart message containing the frame header and data.
        """
        try:
            header = json_decode(msg[0])
            self.header = convert_unicode_to_string(header)
            # Extract dtype and coerce to uint16 if not specified
            dtype = self.header.get('dtype', 'uint16')
            #logging.debug(f"Image data type: {dtype}")

            # Verify the dimensions match the expected frame_height and frame_width
            if 'shape' in self.header:
                frame_height, frame_width = int(self.header['shape'][0]), int(self.header['shape'][1])
                if frame_height != self.frame_height or frame_width != self.frame_width:
                    logging.warning(f"Frame dimensions in header ({frame_height}, {frame_width}) do not match the expected dimensions ({self.frame_height}, {self.frame_width})")
                    return
            else:
                logging.warning("No shape info in header, exiting")
                return

            # Create a numpy array from the raw image data
            img_data = np.frombuffer(msg[1], dtype=np.dtype(dtype))

            # Check the data size: Expecting a single frame with the specified dimensions
            expected_size =  self.superframe_size * frame_height * frame_width

            if img_data.shape[0] != expected_size:
                logging.error(f"Mismatch in expected and actual data size. Expected: {expected_size}, Got: {img_data.size}")
                return

            # Reshape the data into (frame_height, frame_width)
            self.frame_data = img_data.reshape((self.superframe_size, frame_height, frame_width))
            # Slice first frame and discard the rest 
            self.frame_data = self.frame_data[0, :, :]
            # Discard a dropped frame and do not send it for preview
            if np.all(self.frame_data == 0):
                logging.debug("Frame data appears to be a dropped frame, discarding")
                return
            else:
                self.rendered_frame = self.frame_data.tolist()

        except Exception as e:
            logging.error(f"Error processing IPC message: {e}")

    def get_rendered_frame(self):
        """
        Get the latest rendered frame data ready for OdinGraph.

        :return: The latest rendered frame, or None if no data is available.
        """
        if self.rendered_frame is not None:
            return self.rendered_frame
        else:
            logging.warning("No frame data available yet.")
            return None

    def cleanup(self):
        """
        Clean up the IPC channel connection.
        """
        self.sub_socket.cleanup()


class SubSocket:
    """
    Subscriber Socket class to handle continuous listening on the IPC channel.
    This class registers a callback function to process incoming messages.
    """

    def __init__(self, parent, endpoint):
        """
        Initialize IPC channel as a subscriber, and register the callback.

        :param parent: The parent class (IpcLiveView) that created this object, to reference its methods.
        :param endpoint: The URI address of the socket to subscribe to.
        """
        self.parent = parent
        self.endpoint = endpoint
        self.channel = IpcTornadoChannel(IpcTornadoChannel.CHANNEL_TYPE_SUB, endpoint=self.endpoint)
        self.channel.subscribe()
        self.channel.connect()
        # Register the callback method to be called when a message is received
        self.channel.register_callback(self.callback)

    def callback(self, msg):
        """
        Handle incoming data on the socket.
        This callback method is called whenever data arrives on the IPC channel socket.
        It increments the counter, then passes the message to the parent's `create_image_from_socket` method.

        :param msg: The multipart message from the IPC channel.
        """
        self.parent.create_image_from_socket(msg)

    def cleanup(self):
        """Clean up the IPC channel when the server is closed."""
        self.channel.close()