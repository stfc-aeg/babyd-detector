import logging
from odin.adapters.parameter_tree import ParameterTree
from odin.adapters.adapter import ApiAdapterRequest
from dataclasses import dataclass

@dataclass
class Adapters:
    system_info: object

class BabyDController:
    """Class to manage the other adapters in the system."""

    def __init__(self):
        """Initialize the controller object."""
        # Adjusting logging level of the requests library, to prevent connectionpool debugging on every proxy request
        logging.getLogger("urllib3").setLevel(logging.WARNING)

        # Initialize the parameter tree and adpater dataclass after adapters are loaded
        self.adapters = None 
        self.param_tree = None

    def initialize_adapters(self, adapters):
        """Get access to all of the other adapters."""
        self.adapters = Adapters(**adapters)
        logging.debug(f"Adapters loaded: {self.adapters}")      

        self.param_tree = ParameterTree({
        })

    def get(self, path):
        """Get the parameter tree from the controller."""
        return self.param_tree.get(path)

    def set(self, path, data):
        """Set parameters in the parameter tree of the controller."""
        self.param_tree.set(path, data)

    def iac_get(self, adapter, path, **kwargs):
        """Generic IAC get method for synchronous adapters."""
        request = ApiAdapterRequest(None, accept="application/json")
        response = adapter.get(path, request)
        if response.status_code != 200:
            logging.debug(f"IAC GET failed for adapter {adapter}, path {path}: {response.data}")
        return response.data.get(kwargs['param']) if 'param' in kwargs else response.data

    def iac_set(self, adapter, path, param, data):
        """Generic IAC set method for synchronous adapters."""
        request = ApiAdapterRequest({param: data}, content_type="application/vnd.odin-native")
        response = adapter.put(path, request)
        if response.status_code != 200:
            logging.debug(f"IAC SET failed for adapter {adapter}, path {path}: {response.data}")


class BabyDControllerError(Exception):
    """Simple exception class to wrap lower-level exceptions."""
    pass