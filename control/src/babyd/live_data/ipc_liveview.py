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
        self.rendered_frames = {}
        self.superframe_size = superframe_size
        self.dark_correct_active = False
        self.dark_correct_capture = False
        self.dark_data = {}

        # Initialise the SubSocket to handle continuous listening
        self.sub_socket = SubSocket(self, endpoint)
        logging.info(f"Listening for frames on endpoint: {self.endpoint}")

    def _split_pixel_values(self, frame):
        """
        Split a NumPy array of 16-bit pixel values into three arrays: fine, coarse, overflow.
        Using the bit shifts and masks:
          - fine = data & 0b1111111  (bits [0..6])
          - coarse = ((data >> 7) & 0b111111110) >> 1  (bits [8..15], ignoring the overflow bit)
          - overflow = (data >> 7) & 0b000000001       (bit [7] in the shifted domain)

        :param frame: A numpy array of shape [frame_height, frame_width] (16-bit).
        :return: Tuple of (fine_arr, coarse_arr, overflow_arr) uint16 arrays.
        """
        # fine: bits [0..6]
        fine = (frame & 0b1111111).astype(np.uint16)
        # coarse: bits [8..15], after ignoring overflow bit [7]
        coarse = (((frame >> 7) & 0b111111110) >> 1).astype(np.uint16)
        # overflow: single bit [7] after shifting by 7
        overflow = ((frame >> 7) & 0b000000001).astype(np.uint16)

        return fine, coarse, overflow
    
    def _apply_dark_correction(self, arr, dark_arr):
        """
        Subtract stored dark data from incming frames, clamp negative values to zero.
        """
        if dark_arr is None:
            return arr  # Nothing to subtract

        # Convert both to 32-bit int for safe subtraction to handle negative numebrs
        corrected = arr.astype(np.int32) - dark_arr.astype(np.int32)
        # Clamp negative values to 0
        corrected[corrected < 0] = 0
        # Return to uint16
        return corrected.astype(np.uint16)

    def _generate_masked_images(self, frame):
        """
        Take a frame, split it into (fine, coarse, overflow), optionally subtract dark frames,
        and return them as python lists for easy serialisation in the ParameterTree.

        :param frame: A numpy array representing a single frame of shape [frame_height, frame_width].
        :return: A dict containing the F/C/OF.
        """
        fine, coarse, overflow = self._split_pixel_values(frame)

        if self.dark_correct_active:
            if 'fine' in self.dark_data:
                fine = self._apply_dark_correction(fine, self.dark_data['fine'])
            if 'coarse' in self.dark_data:
                coarse = self._apply_dark_correction(coarse, self.dark_data['coarse'])
            if 'overflow' in self.dark_data:
                overflow = self._apply_dark_correction(overflow, self.dark_data['overflow'])

        return {
            'fine': fine.tolist(),
            'coarse': coarse.tolist(),
            'overflow': overflow.tolist()
        }
    
    def _generate_dark_averages(self, super_frame):
        """
        Generate dark averages (coarse/fine/overflow) from the entire superframe,
        all done via integer arithmetic (uint32 sum, then integer divide) to avoid overflow
        and store results as uint16.

        Apply the same bit-splitting approach to each of the 1000 frames, sum them,
        and divide by superframe_size.
        """
        # Extract components in 32-bit form to safely sum
        fine_all     = (super_frame & 0b1111111).astype(np.uint32)
        coarse_all   = (((super_frame >> 7) & 0b111111110) >> 1).astype(np.uint32)
        overflow_all = ((super_frame >> 7) & 0b000000001).astype(np.uint32)

        # Sum across axis=0 => shape [frame_height, frame_width], 32-bit
        sum_fine     = fine_all.sum(axis=0)
        sum_coarse   = coarse_all.sum(axis=0)
        sum_overflow = overflow_all.sum(axis=0)

        # Compute integer average
        avg_fine     = (sum_fine // self.superframe_size).astype(np.uint16)
        avg_coarse   = (sum_coarse // self.superframe_size).astype(np.uint16)
        avg_overflow = (sum_overflow // self.superframe_size).astype(np.uint16)

        # Store these in self.dark_data
        self.dark_data = {
            'fine': avg_fine,
            'coarse': avg_coarse,
            'overflow': avg_overflow
        }

    def create_image_from_socket(self, msg):
        """
        Process incoming messages from the IPC channel, extract and prepare the frame data.
        :param msg: The multipart message containing the frame header and data.
        """
        logging.debug("Create IMG called")
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
            
            super_frame = img_data.reshape((self.superframe_size, frame_height, frame_width))

            if self.dark_correct_capture:
                self._generate_dark_averages(super_frame)
                self.dark_correct_capture = False
            
            self.frame_data = super_frame[0, :, :]

            # Discard a dropped frame and do not send it for preview
            if np.all(self.frame_data == 0):
                logging.debug("Frame data appears to be a dropped frame, discarding")
                return
            else:
                self.rendered_frames = self._generate_masked_images(self.frame_data)

        except Exception as e:
            logging.error(f"Error processing IPC message: {e}")

    def get_rendered_frame(self):
        """
        Get the latest rendered frame data ready for OdinGraph.

        :return: The latest rendered frame, or None if no data is available.
        """
        if self.rendered_frames is not None:
            return self.rendered_frames
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