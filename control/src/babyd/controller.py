from concurrent.futures import ThreadPoolExecutor
from tornado.concurrent import run_on_executor
from functools import partial
import logging
import time

from odin.adapters.parameter_tree import ParameterTree

from .capture_state_machine import CaptureStateMachine
from .capture_manager import CaptureManager
from .loaded_adapters import Adapters
from .loki_params import LokiParams
from .util import iac_get, iac_set

class BabyDController:
    """Class to manage the other adapters in the system."""
    executor = ThreadPoolExecutor(max_workers=1) 

    def __init__(self):
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

        # Frame rate of babd to use for converting time based capture definiton into frames
        self.frame_rate = 30

    def initialize_adapters(self, adapters):
        """Get access to all of the other adapters."""
        try:
            self.adapters = Adapters(**adapters)
            logging.info(f"Adapters loaded: {self.adapters}")
        except Exception as e:
            logging.error(f"Failed to initialize adapter: {e}")

        self.loki_params = LokiParams(self.adapters.loki_proxy)
        self.capture_manager = CaptureManager(self.adapters.munir, self.frame_rate)
        self.state_machine = CaptureStateMachine(self.capture_manager)
        self.background_task()

        args = {'file_path':'/tmp/josh', 'file_name':'2108_0911_1', 'num_frames':12345}
        iac_set(self.adapters.munir, 'subsystems/babyd/args/', args)

        #grab munir default params here so that below paramtree holds valid settings if none are provided?

        def get_arg(name):
            return getattr(self, name)

        def set_arg(name, value):
            setattr(self, name, value)

        def arg_param(name):
            return (partial(get_arg, name), partial(set_arg, name))
        
        # lambda value: setattr(self.loki_params, 'loki_connected', value))
        # partial(self.set_loki_state,'MAIN_EN')
        # lambda value: self.set_loki_state('MAIN_EN', value)

        loki_tree = ParameterTree({
                'connected': (lambda: self.loki_params.loki_connected, lambda value: self.set_loki_state('MAIN_EN', value)),
                'initialised': (lambda: self.loki_params.loki_initialised, partial(self.set_loki_state,'BD_INITIALISE/TRIGGER')),
                'sync': (lambda: self.loki_params.loki_sync, partial(self.set_loki_state,'SYNC')),
                'ready': (lambda: self.loki_params.loki_ready, None)
            })

        munir_tree = ParameterTree({
            'args': {
                arg: arg_param(arg) for arg in [
                    'file_path', 'file_name', 'num_intervals', 'delay', 'frame_based_capture'
                ]
            },
            'captures': (self.capture_manager.get_capture_list, None),
            'stage_capture': (lambda: None, self.stage_capture),
            'execute': (lambda: self.executing, self.execute_captures),
            'remove_capture': (lambda: None, self.remove_capture),
            'duplicate_capture': (lambda: None, self.duplicate_capture)
        })

        self.param_tree = ParameterTree({
            'munir': munir_tree,
            'loki': loki_tree
        })

    def get(self, path):
        """Get the parameter tree from the controller."""
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree of the controller."""
        self.param_tree.set(path, data)
    
    @run_on_executor
    def background_task(self):
        """Background task that periodically updates Loki state."""
        while self.background_task_en:
            self.update_loki_state()
            time.sleep(0.2)  # Polling interval
            # Use the executing variable to act as trigger to begin captures
            if self.executing:
                if self.capture_manager.has_captures():
                    logging.debug("Telling statemachine to begin")
                    self.state_machine.start_preparing()
                else:
                    logging.debug("No captures in the capture manager")
            self.executing = False

    # def poll_file_writing(self):
    #     """Wait until the current capture has finished being written to file."""
    #     logging.debug(f"Returned: {iac_get(self.adapters.munir, 'subsystems/babyd/status/frames_written')}")
    #     while iac_get(self.adapters.munir, 'subsystems/babyd/status/executing'):
    #         logging.debug("Waiting for file writing")
    #         time.sleep(1)

    def set_on_munir(self, path, name, frames):
        iac_set(self.adapters.munir, 'subsystems/babyd/args/', 'file_path', path)
        iac_set(self.adapters.munir, 'subsystems/babyd/args/', 'file_name', name)
        iac_set(self.adapters.munir, 'subsystems/babyd/args/', 'num_frames', frames)
        iac_set(self.adapters.munir, 'execute', 'babyd', True)

    def execute_captures(self, value=None):
        """Check if captures are already being executed and start if not, check relevant parts of system and datapaths
        are ready for capturing"""
        if not self.loki_params.loki_ready:
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

    def stage_capture(self, value=None):
        """Stage a new capture with current parameters."""
        self.capture_manager.add_capture(
            self.file_path, self.file_name, self.num_intervals, self.delay, self.frame_based_capture
        )

    def remove_capture(self, capture_id):
        """Remove a capture from the queue by ID."""
        self.capture_manager.remove_capture(capture_id)

    def duplicate_capture(self, capture_id):
        """Duplicate a capture from the queue by ID."""
        self.capture_manager.duplicate_capture(capture_id)

    def update_loki_state(self):
        """Update the Loki state by performing an IAC GET."""
        params = iac_get(self.adapters.loki_proxy, "node_1/application/system_state")
        self.loki_params.update_system_state(params)

    def set_loki_state(self, param, value):
        """Set a value in the Loki state and update the system state."""
        path = f'node_1/application/system_state/'
        iac_set(self.adapters.loki_proxy, path, param, value)

    def cleanup(self):
        """Cleanly shutdown adapter services"""
        logging.info(f'Stopping background task')
        self.background_task_en = False

class BabyDControllerError(Exception):
    """Simple exception class to wrap lower-level exceptions."""
    pass