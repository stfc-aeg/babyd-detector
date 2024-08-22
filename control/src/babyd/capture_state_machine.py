import time
import logging
from statemachine import State, StateMachine
from tornado.concurrent import run_on_executor

from .capture_manager import CaptureManager, Capture

class CaptureStateMachine(StateMachine):
    # states
    idle = State('Idle', initial=True)
    preparing = State('Preparing')
    executing = State('Executing')
    writing = State('Writing')

    # transitions between the states
    start_preparing = idle.to(preparing) | writing.to(preparing)
    start_executing = preparing.to(executing)
    writing_file = executing.to(writing)
    return_to_idle = writing.to(idle) 
    abort = preparing.to(idle)

    def __init__(self, capture_manager):
        self.capture_manager: CaptureManager = capture_manager
        self.capture: Capture = None
        super().__init__()

    def on_start_preparing(self):
        logging.debug(f'Entered on_start_preparing, current state: {self.current_state}')
        if self.capture_manager.has_captures():
            self.capture = self.capture_manager.get_next_capture()
            self.start_executing()
            logging.debug(f"Capture returned from capture_manager, Executing: {self.capture}")
        else:
            logging.debug("No Captures, returning to idle through abort")
            self.abort()

    def on_start_executing(self):
        logging.debug(f'Entered on_start_executing, current state: {self.current_state}')
        capture = self.capture
        if capture:
            self.capture_manager.execute_on_munir(
                capture.file_path, capture.file_name, capture.num_intervals
            )
            self.writing_file()

    def on_writing_file(self):
        logging.debug(f'Entered on_writing_file, current state: {self.current_state}')
        self.capture_manager.poll_file_writing()
        logging.debug("File writing finished")
        if self.capture_manager.has_captures():
            logging.debug("Preparing another capture")
            if self.capture:
                logging.debug(f"Waiting for {self.capture.delay} seconds before next capture")
                time.sleep(self.capture.delay)
            self.start_preparing()
            logging.debug(f'After prepare_another, current state: {self.current_state}')
        else:
            logging.debug("Returning to idle")
            self.return_to_idle()