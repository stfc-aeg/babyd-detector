import logging
from odin.adapters.adapter import ApiAdapter, ApiAdapterResponse, request_types, response_types
from odin.adapters.parameter_tree import ParameterTreeError
from tornado.escape import json_decode

from babyd.controller import BabyDController, BabyDControllerError

class BabyDAdapter(ApiAdapter):
    """Prototype DAQ adapter class for inter-adapter communication."""

    def __init__(self, **kwargs):
        """Initialise the BabyD object."""
        super(BabyDAdapter, self).__init__(**kwargs)
        logging.debug("BabyD Adapter Loading")
        self.BabyDController = BabyDController(self.options)
        logging.debug("BabyD Adapter Loaded")

    def initialize(self, adapters):
        """Initialize the adapter after it has been loaded."""
        self.adapters = dict((k, v) for k, v in adapters.items() if v is not self)
        self.BabyDController.initialize_adapters(self.adapters)

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        try:
            response = self.BabyDController.get(path)
            status_code = 200
        except ParameterTreeError as e:
            response = {'error': str(e)}
            status_code = 400

        content_type = 'application/json'
        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)

    @request_types('application/json',"application/vnd.odin-native")
    @response_types('application/json', default='application/json')
    def put(self, path, request):
        content_type = 'application/json'
        try:
            data = json_decode(request.body)
            self.BabyDController.set(path, data)
            response = self.BabyDController.get(path)
            status_code = 200
        except BabyDControllerError as e:
            response = {'error': str(e)}
            status_code = 400
        except (TypeError, ValueError) as e:
            response = {'error': 'Failed to decode PUT request body: {}'.format(str(e))}
            status_code = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status_code)
    
    def cleanup(self):
        self.BabyDController.cleanup()