import time
import logging
from statemachine import State, StateMachine
from tornado.concurrent import run_on_executor

from .capture_manager import CaptureManager

class CaptureStateMachine(StateMachine):
    # states
    idle = State('Idle', initial=True)
    preparing = State('Preparing')
    executing = State('Executing')
    writing = State('Writing')

    # transitions between the states
    start_preparing = idle.to(preparing)
    start_executing = preparing.to(executing)
    writing_file = executing.to(writing)
    return_to_idle = writing.to(idle)

    # additional transitions 
    abort = preparing.to(idle)
    prepare_another = writing.to(preparing)

    def __init__(self, capture_manager: CaptureManager):
        #self.controller = BabyDController(controller)
        self.capture_manager = capture_manager
        self.capture = None
        super().__init__()


    def on_start_preparing(self):
        """Prepare the controller by allowing it to grab the next capture,
        or handle there being no captures and return to idle."""
        logging.debug(f'Entered on_start_preparing, current state: {self.current_state}')
        if self.capture_manager.has_captures():
            self.capture = self.capture_manager.get_next_capture()
            self.start_executing()
            logging.debug(f"Capture returned from capture_manager, Executing: {self.capture}")
        else:
            logging.debug("No Captures, returning to idle through abort")
            self.abort()

    def on_start_executing(self):
        """Tell the controller to use the capture parameters and set the munir adapter 
        with those parameters, start the capture and wait for file writing."""
        logging.debug(f'Entered on_start_executing, current state: {self.current_state}')
        capture = self.capture
        if capture:
            self.capture_manager.execute_on_munir(
                capture.file_path, capture.file_name, capture.num_intervals
                )
            self.writing_file()

    def on_writing_file(self):
        """Tell the controller to grab another capture if one exists it and 
        return tothe preparing state, else return to idle."""
        logging.debug(f'Entered on_writing_file, current state: {self.current_state}')
        self.capture_manager.poll_file_writing()
        if self.capture_manager.has_captures():
            time.sleep(self.capture.delay)
            self.prepare_another()
        else:
            self.return_to_idle()


# import logging

# from statemachine import State, StateMachine

# class CaptureStateMachine(StateMachine):
#     # states
#     idle = State('Idle', initial=True)  # Initial state, waiting to start
#     preparing = State('Preparing')
#     executing = State('Executing')
#     writing = State('Writing')

#     # transitions between the states
#     start_preparing = idle.to(preparing)
#     start_executing = preparing.to(executing)
#     writing_file = executing.to(writing)
#     prepare_another = writing.to(preparing)
#     return_to_idle = writing.to(idle)


#     def __init__(self):
#         self.capture = None
#         self.manual_state = True
#         super().__init__()

        
#     def on_start_preparing(self):
#         """Prepare the controller by allowing it to grab the next capture,
#         or handle there being no captures and return to idle."""
#         self.current_state = self.preparing if self.manual_state else self.current_state
#         print(f'Entered on_start_preparing, current state: {self.current_state}')
#         self.start_executing()
    
#     def on_start_executing(self):
#         """Tell the controller to use the capture parameters and set the munir adapter 
#         with those parameters, start the capture and wait for file writing."""
#         self.current_state = self.executing if self.manual_state else self.current_state
#         print(f'Entered on_start_executing, current state: {self.current_state}')
#         self.writing_file()

#     def on_writing_file(self):
#         self.current_state = self.writing if self.manual_state else self.current_state
#         print(f'Entered on_writing_file, current state: {self.current_state}')
#         self.return_to_idle()

# # Create an instance of the state machine
# statemachine = CaptureStateMachine()

# # Start the state transitions
# statemachine.start_preparing()

# # Print the final state after all transitions
# print(f'Final state: {statemachine.current_state}')