import logging
from dataclasses import dataclass

@dataclass
class Capture:
    id: int
    file_path: str
    file_name: str
    num_intervals: int
    delay: int  # Delay before the NEXT capture in seconds
    frame_based_capture: bool

class CaptureManager:
    """Class to manage multiple staged captures."""

    def __init__(self, frame_rate):
        """Initialize the CaptureManager."""
        self.captures = {}
        self.capture_counter = 0  # Counter for unique capture IDs
        self.frame_rate = frame_rate  # Frame rate of babd to use for converting time based capture definiton into frames

    def add_capture(self, file_path, file_name, num_intervals, delay, frame_based_capture):
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
        if self.captures:
            next_id = min(self.captures)
            return self.captures.pop(next_id)
        return None

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
        """Duplicate a capture by ID and add it to the dictionary."""
        if capture_id in self.captures:
            self.capture_counter += 1
            capture = self.captures[capture_id]
            new_capture = Capture(
                self.capture_counter, capture.file_path, capture.file_name,
                capture.num_intervals, capture.delay, capture.frame_based_capture
            )
            self.captures[self.capture_counter] = new_capture
            logging.debug(f"Duplicated capture with ID: {capture_id} as new ID: {self.capture_counter}")
            return True
        logging.warning(f"Capture with ID: {capture_id} not found.")
        return False
