import logging

from odin.adapters.adapter import ApiAdapterRequest

def iac_get(adapter, path, **kwargs):
    """Generic inter-adapter-communication get method for odin_control adapters.
    
    This method handles sending an HTTP style GET request to another adapter using the 
    targets GET method implementation to request a value from its parameter tree. 

    :param adapter: Adapter object to target
    :param path: Parameter tree path to target, must also include the parameter itself
    :param **kwargs as_dict: Used to tell the function to return the response as a dict
    :return: Value of the parameter requested, or {param:value}

    Example usage :\n
    iac_get(self.adapters.munir, 'subsystems/babyd/status/executing', as_dict=True)\n
    iac_get(self.adapters.munir, 'subsystems/babyd/status/executing')\n
    """
    as_dict = kwargs.get('as_dict', False)
    param = path.split('/')[-1]
    request = ApiAdapterRequest(None, accept="application/json")
    response = adapter.get(path, request)
    if response.status_code != 200:
        logging.debug(f"IAC GET failed for adapter {adapter}, path {path}: {response.data}")
    return response.data if as_dict else response.data.get(param)

def iac_set(adapter, path, *args):
    """Generic inter-adapter-communication set method for odin_control adapters.
    
    This method handles sending an HTTP style PUT request to another adapter using the target's
    PUT method implementation to update its parameter tree values.

    :param adapter: Adapter object to target
    :param path: Parameter tree path to target, to not include the parameter itself
    :param *args: Accepts either a key-value pair (param, data) or a dictionary of key-value pairs

    Example usage :\n
    self.iac_set(self.adapters.munir, 'args/', 'file_path', '/tmp')\n
    self.iac_set(self.adapters.munir, 'args/', {'file_path':'/tmp/josh/', 'file_name':'test_01_josh'})\n
    For values at the root of the tree provide an empty string as the path
    """
    # Check if the first argument is a dictionary
    if len(args) == 1 and isinstance(args[0], dict):
        data_dict = args[0]
    elif len(args) == 2:
        param, data = args
        data_dict = {param: data}
    else:
        logging.error("Invalid arguments provided. Provide either (param, data) or a dictionary of values.")
        return

    # Create the request with the constructed data dictionary
    request = ApiAdapterRequest(data_dict, content_type="application/vnd.odin-native")
    response = adapter.put(path, request)
    if response.status_code != 200:
        logging.error(f"IAC SET failed for adapter {adapter}, path {path}: {response.data}")
    return response.data
