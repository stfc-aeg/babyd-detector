from dataclasses import dataclass
import logging

from odin.adapters.proxy import ProxyAdapter

from ..utilities.util import iac_set

@dataclass
class LokiParams:
    _loki_proxy: ProxyAdapter
    _param_tree: dict = None

    def update_param_tree(self, params):
        """Update the entire param_tree/applicaiton using a single IAC_GET"""
        self._param_tree = params

    def _get_from_param_tree(self, *keys):
        """Return a value from the param_tree dict"""
        data = self._param_tree
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data

    @property
    def connected(self):
        return self._get_from_param_tree('system_state', 'MAIN_EN')
    
    @connected.setter
    def connected(self, value):
        path = 'node_1/application/system_state/'
        param = 'MAIN_EN'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def initialised(self):
        return self._get_from_param_tree('system_state','BD_INITIALISE', 'DONE')
    
    @initialised.setter
    def initialised(self, value):
        path = 'node_1/application/system_state/BD_INITIALISE/'
        param = 'TRIGGER'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def sync(self):
        return self._get_from_param_tree('system_state', 'SYNC')
    
    @sync.setter
    def sync(self, value):
        path = 'node_1/application/system_state/'
        param = 'SYNC'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def row_range(self):
        return self._get_from_param_tree('readout', 'row_range')
    
    @row_range.setter
    def row_range(self, value):
        logging.warning(f"Row range is non-mutable, Ignoring {value}")


    @property
    def ready(self):
        main_en = self._get_from_param_tree('system_state', 'MAIN_EN')
        bd_initialise_done = self._get_from_param_tree('system_state', 'BD_INITIALISE', 'DONE')
        sync = self._get_from_param_tree('system_state', 'SYNC')
        
        return all([main_en, bd_initialise_done, sync])
    
# Make controller handle updating of loki params
# Have updating of iac adapters handled in executor
# Have the execting function called in executor
# Use a state machine to handle the calling of captures