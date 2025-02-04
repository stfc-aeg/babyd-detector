from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from functools import partial
import logging
import time
import shutil

from odin.adapters.parameter_tree import ParameterTree

from .capture.capture_state_machine import CaptureStateMachine
from .capture.capture_manager import CaptureManager
from .utilities.loaded_adapters import Adapters
from .interfaces.loki_params import LokiParams
from .interfaces.adxdma_params import AlphaDataParams
from .live_data.ipc_liveview import IpcLiveView
from .utilities.util import iac_get, iac_set

class BabyDController:
    """Class to manage the other adapters in the system."""
    executor = ThreadPoolExecutor(max_workers=1) 

    def __init__(self, options):
        """Initialize the controller object."""
        # Initialize the parameter tree and adapter dataclass after adapters are loaded
        self.adapters = None
        self.param_tree = None
        self.file_path = ''
        self.file_name = ''
        self.num_intervals = 0
        self.delay = 0
        self.frame_based_capture = True
        # Value to indicate if BabyDController is executing a capture/set of captures, seperate from hdf file writing status
        self.executing = False
        self.background_task_en = True
        self.free_space_bytes = 0

        # Frame rate of babd to use for converting time based capture definiton into frames
        self.frame_rate = 533000

    def initialize_adapters(self, adapters):
        """Get access to all of the other adapters."""
        try:
            self.adapters = Adapters(**adapters)
            logging.info(f"Adapters loaded: {self.adapters}")
        except Exception as e:
            logging.error(f"Failed to initialize adapter: {e}")

        self.liveview = IpcLiveView()
        self.loki = LokiParams(self.adapters.loki_proxy)
        self.adxdma = AlphaDataParams(self.adapters.adxdma)
        self.capture_manager = CaptureManager(self.adapters.munir, self.frame_rate)
        self.state_machine = CaptureStateMachine(self.capture_manager)

        logging.debug(f"Adxdma dynamic properties: {self.adxdma.get_dynamic_properties()}")

        self.get_munir_args()
        self.background_task()

        def get_arg(name):
            return getattr(self, name)

        def set_arg(name, value):
            setattr(self, name, value)

        def arg_param(name):
            return (partial(get_arg, name), partial(set_arg, name))

        loki_tree = ParameterTree({
            'connected': (lambda: self.loki.connected, lambda value: setattr(self.loki, 'connected', value)),
            'initialised': (lambda: self.loki.initialised, lambda value: setattr(self.loki, 'initialised', value)),
            'sync': (lambda: self.loki.sync, lambda value: setattr(self.loki, 'sync', value)),
            'ready': (lambda: self.loki.ready, None),
        })

        adxdma_trigger = {
            'available_modes': (lambda: self.adxdma.available_triggers, lambda value: setattr(self.adxdma, 'available_triggers', value)),
            'mode': (lambda: self.adxdma.trigger_mode, lambda value: setattr(self.adxdma, 'trigger_mode', value)),
            'frame_per_event': (lambda: self.adxdma.frame_per_event, lambda value: setattr(self.adxdma, 'frame_per_event', value))
        }

        # create adxdma_tree dict with static properties
        adxdma_tree_dict = {
            'connected': (lambda: self.adxdma.connected, lambda value: setattr(self.adxdma, 'connected', value)),
            'ip_local': (lambda: self.adxdma.ip_local, lambda value: setattr(self.adxdma, 'ip_local', value)),
            'ip_remote': (lambda: self.adxdma.ip_remote, lambda value: setattr(self.adxdma, 'ip_remote', value)),
            'available_clock_speeds': (lambda: self.adxdma.available_speeds, lambda value: setattr(self.adxdma, 'available_speeds', value)),
            'clock_speed': (lambda: self.adxdma.clock_speed, lambda value: setattr(self.adxdma, 'clock_speed', value)),
            'trigger': adxdma_trigger
        }
        
        # Add the dynamic properties to the adxdma_tree_dict
        dynamic_properties = self.adxdma.get_dynamic_properties()
        for name, prop in dynamic_properties.items():
            adxdma_tree_dict[name] = (prop.fget, prop.fset)

        # Create the ParameterTree with all properties
        adxdma_tree = ParameterTree(adxdma_tree_dict)

        munir_tree = ParameterTree({
            'args': {
                arg: arg_param(arg) for arg in [
                    'file_path', 'file_name', 'num_intervals', 'delay', 'frame_based_capture'
                ]
            },
            'captures': (self.capture_manager.get_capture_list, None),
            'stage_capture': (lambda: None, lambda value: self.capture_manager.add_capture(
                    self.file_path, self.file_name, self.num_intervals, self.delay, 
                    self.frame_based_capture, value
                )),
            'execute': (lambda: self.executing, self.execute_captures),
            'remove_capture': (lambda: None, self.capture_manager.remove_capture),
            'duplicate_capture': (lambda: None, self.capture_manager.duplicate_capture),
            'free_space': (lambda: self.free_space_bytes, None)
        })
        
        liveview_tree = ParameterTree({
            'dark_correct_active': (lambda: self.liveview.dark_correct_active, lambda value: setattr(self.liveview, 'dark_correct_active', value)),
            'liveview': (lambda: self.liveview.rendered_frames, None),
        })

        self.param_tree = ParameterTree({
            'loki': loki_tree,
            'adxdma': adxdma_tree,
            'munir': munir_tree,
            'liveview': liveview_tree        
        })

    def get(self, path):
        """Get the parameter tree from the controller."""
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree of the controller."""
        if 'file_name' in data:
            data['file_name'] = data['file_name'].split('.')[0]
        if 'file_path' in data and not data['file_path'].endswith('/'):
            data['file_path'] += '/'
        self.param_tree.set(path, data)
    
    @run_on_executor
    def background_task(self):
        """Background task that periodically updates Loki state and starts executing captures."""
        while self.background_task_en:
            self.update_loki_state()

            try:
                total, used, free = shutil.disk_usage(self.file_path)
                self.free_space_bytes = free
            except:
                logging.error(f"File path {self.file_path} does not exist. Free space check failed.")
                self.free_space_bytes = 0
            time.sleep(0.2)  # Polling interval
            # Use the executing variable to act as trigger to begin captures
            if self.executing:
                if self.capture_manager.has_captures():
                    logging.debug("Telling statemachine to begin with staged captures")
                    self.state_machine.start_preparing()
                else:
                    logging.debug("No captures in the capture manager, adding current parameters to capture, telling statement to begin")
                    self.capture_manager.add_capture(self.file_path, self.file_name, self.num_intervals, self.delay, self.frame_based_capture)
                    self.state_machine.start_preparing()
            self.executing = False

    def execute_captures(self, value=None):
        """Check if captures are already being executed and start if not, check relevant parts of system and datapaths
        are ready for capturing"""
        if not self.loki.ready:
            logging.error("Loki is not ready, Aborting capture execution")
            self.executing = False
            return
        if self.executing:
            logging.error("Captures are already being executed. Cannot start new captures.")
            return
        # acts as a trigger to start the capture process in the background task
        self.executing = True
        

    # @run_on_executor
    # def _execute_captures(self, value=None):
    #     """Execute either staged captures or a single capture in an executor thread to avoid blocking."""
    #     if self.capture_manager.has_captures():
    #         while self.capture_manager.has_captures():
    #             # Use the capture manager to select the next capture based on when it was staged 
    #             capture = self.capture_manager.get_next_capture()
    #             logging.debug(f"Executing capture: {capture}")
                
    #             self.set_on_munir(capture.file_path, capture.file_name, capture.num_intervals)
    #             # Wait for the current capture to finish writing to its file before continuing 

    #             self.poll_file_writing()

    #             logging.debug(f"Waiting for {capture.delay} seconds before next capture.")
    #             time.sleep(capture.delay)
    #     else:
    #         # If no captures are staged, execute the current parameters immediately
    #         num_frames = self.num_intervals
    #         # Convert time to frames if needed
    #         if not self.frame_based_capture:
    #             num_frames = int(self.num_intervals * self.frame_rate) 
    #         self.set_on_munir(self.file_path, self.file_name, num_frames)
    #         self.poll_file_writing()

    #     # logging.debug(f'Calling stop execute:')
    #     # iac_set(self.adapters.munir, "subsystems/babyd/", "stop_execute", True)
    #     self.executing = False

    def update_loki_state(self):
        """Update the Loki state by performing an IAC GET."""
        params = iac_get(self.adapters.loki_proxy, "node_1/application")
        self.loki.update_param_tree(params)

    def get_munir_args(self):
        """Get the latest args from munir, and apply them to own params"""
        args = iac_get(self.adapters.munir, "subsystems/babyd/args")
        self.file_name = args['file_name']
        self.file_path = args['file_path']
        self.num_intervals = args['num_frames']

    def cleanup(self):
        """Cleanly shutdown adapter services"""
        logging.info(f'Stopping background task')
        self.background_task_en = False

class BabyDControllerError(Exception):
    """Simple exception class to wrap lower-level exceptions."""
    pass