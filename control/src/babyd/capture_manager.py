from dataclasses import dataclass
from datetime import datetime
import logging
import time
import re
import os 

from .util import iac_get, iac_set

@dataclass
class Capture:
    id: int
    file_path: str
    file_name: str
    num_intervals: int
    delay: int  # Delay before the NEXT capture in seconds
    frame_based_capture: bool

class CaptureManager:
    """Class to store multiple staged captures and handle providing them to the BabyDController"""

    def __init__(self, munir_adapter, frame_rate):
        """Initialize the CaptureManager."""
        self.munir = munir_adapter
        self.captures = {}
        self.capture_counter = 0  # Counter for unique capture IDs
        self.frame_rate = frame_rate  # Frame rate of babd to use for converting time based capture definiton into frames

    def add_capture(self, file_path, file_name, num_intervals, delay, frame_based_capture, value=None):
        """Add a new capture to the dictionary."""
        self.capture_counter += 1
        if not frame_based_capture:
            num_intervals = int(num_intervals * self.frame_rate)  # Convert seconds to frames required for odin-daa
        capture = Capture(self.capture_counter, file_path, file_name, num_intervals, delay, frame_based_capture)
        self.captures[self.capture_counter] = capture
        logging.debug(f"Added capture: {capture}")

    def get_capture_list(self):
        """Get the list of captures in the dictionary."""
        return {cid: capture.__dict__ for cid, capture in self.captures.items()}

    def get_next_capture(self):
        """Get the next capture from the dictionary by the lowest ID."""
        return self.captures.pop(min(self.captures)) if self.has_captures() else None

    def has_captures(self):
        """Check if there are captures in the dictionary."""
        return bool(self.captures)

    def remove_capture(self, capture_id):
        """Remove a capture from the dictionary by ID."""
        if capture_id in self.captures:
            del self.captures[capture_id]
            logging.debug(f"Removed capture with ID: {capture_id}")
            return True
        logging.warning(f"Capture with ID: {capture_id} not found.")
        return False

    def duplicate_capture(self, capture_id):
        if capture_id in self.captures:
            capture = self.captures[capture_id]
            # Regex to extract the base filename by removing the last underscore and numbers
            base_filename_regex = re.compile(r'(.+?)(_\d+)?$')
            match = base_filename_regex.match(capture.file_name)
            base_file_name = match.group(1) if match else capture.file_name

            # Find the highest suffix number used with this base filename
            suffix_regex = re.compile(rf'^{re.escape(base_file_name)}(?:_(\d+))?$')
            max_suffix = 0
            for cap in self.captures.values():
                suffix_match = suffix_regex.match(cap.file_name)
                if suffix_match and suffix_match.group(1):
                    current_suffix = int(suffix_match.group(1))
                    if current_suffix > max_suffix:
                        max_suffix = current_suffix
            # Form the new file name with the next available suffix
            new_file_name = f"{base_file_name}_{max_suffix + 1}"

            self.add_capture(
                capture.file_path,
                new_file_name,
                capture.num_intervals,
                capture.delay,
                capture.frame_based_capture
            )
            logging.info(f"Duplicated capture with ID: {capture_id} with new filename: {new_file_name}")
            return True
        logging.warning(f"Capture with ID: {capture_id} not found.")
        return False
    
    def poll_file_writing(self):
        """Wait until the current capture has finished being written to file."""
        logging.debug(f"Returned: {iac_get(self.munir, 'subsystems/babyd/status/frames_written')}")
        while iac_get(self.munir, 'subsystems/babyd/status/executing'):
            logging.info("Waiting for file writing")
            time.sleep(1)

    def execute_on_munir(self, file_path, file_name, frames):
        """Set the execution arguments on Munir and start the capture"""
        munir_args = {'file_path': file_path, 'file_name': file_name, 'num_frames': frames}
        iac_set(self.munir, 'subsystems/babyd/args/', munir_args)
        iac_set(self.munir, 'execute', 'babyd', True)