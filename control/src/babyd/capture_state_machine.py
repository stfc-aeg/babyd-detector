from statemachine import State, StateMachine
import logging
import time

from .capture_manager import CaptureManager, Capture

class CaptureStateMachine(StateMachine):
    # states
    idle = State('Idle', initial=True)
    preparing = State('Preparing')
    executing = State('Executing')
    writing = State('Writing')

    # transitions between the states
    #Two transitions possible for start_preparing
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
        """Function to be called when the statemachine enters the preparing state
        
        This function tells the capture_manager to check for and return the next capture,
        and handles the system state based on whether the capture manager has un-completed 
        captures.
        """
        logging.debug(f'Entered on_start_preparing, current state: {self.current_state}')
        if self.capture_manager.has_captures():
            self.capture = self.capture_manager.get_next_capture()
            self.start_executing()
            logging.debug(f"Capture returned from capture_manager, Executing: {self.capture}")
        else:
            logging.debug("No Captures, returning to idle through abort")
            self.abort()

    def on_start_executing(self):
        """Function to be called when the statemachine enters the executing state 
        
        This function tells the capture manager to apply the values from the currently
        selected capture to the munir adapter, and start the execution process, and then
        progresses the system onto the writing state.
        """
        logging.debug(f'Entered on_start_executing, current state: {self.current_state}')
        capture = self.capture
        if capture:
            self.capture_manager.execute_on_munir(
                capture.file_path, capture.file_name, capture.num_intervals
            )
            self.writing_file()

    def on_writing_file(self):
        """Function to be called when the statemachine enters the writing state
        
        This function begins polling for the file writing process to finish and checks
        for more captures in the capture_manager, it will either return to idle if no
        more captures are queued, or return to the preparing state if another capture is 
        waiting. """
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