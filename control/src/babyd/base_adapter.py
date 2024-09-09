from odin.adapters.adapter import (ApiAdapter, ApiAdapterResponse, response_types, wants_metadata)
from odin.adapters.parameter_tree import ParameterTreeError
from odin.util import decode_request_body


from babyd.alphadata_ctrl import AlphaDataController
from babyd.adxdma import AdxdmaException

import logging


class BaseAdapter(ApiAdapter):

    xdma_control = AlphaDataController

    def __init__(self, **kwargs):

        super(BaseAdapter, self).__init__(**kwargs)

        self.controller = self.xdma_control(self.options.get("register_map_file"))

        # self.param_tree = ParameterTree(self.xdma_control._params)
        self.controller.init_tree()

    @response_types('application/json', default='application/json')
    def get(self, path, request):
        metadata = wants_metadata(request)
        try:
            response = self.controller.param_tree.get(path, metadata)
            content_type = 'application/json'
            status = 200
        except ParameterTreeError as param_error:
            response = {"response": "BabyD GET Error: {}".format(param_error)}
            content_type = 'application/json'
            status = 400

        except AdxdmaException as xdma_err:
            response = {"response": "Adxdma API Error: {}".format(xdma_err.message)}
            content_type = "application/json"
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)

    @response_types('application/json', default='application/json')
    def put(self, path, request):
        try:
            data = decode_request_body(request)
            self.controller.param_tree.set(path, data)

            response = self.controller.param_tree.get(path)
            content_type = 'application/json'
            status = 200

        except ParameterTreeError as param_error:
            response = {'response': 'BabyD PUT error: {}'.format(param_error)}
            content_type = 'application/json'
            status = 400

        except AdxdmaException as xdma_err:
            response = {'response': 'Adxdma API Error: {}'.format(xdma_err.message)}
            content_type = 'application/json'
            status = 400

        return ApiAdapterResponse(response, content_type=content_type, status_code=status)