from dataclasses import dataclass

from odin.adapters.proxy import ProxyAdapter

from .util import iac_get, iac_set

@dataclass
class LOKI_Params:
    _loki_proxy: ProxyAdapter
    _system_state: dict = None

    def _update_system_state(self):
        """Update the entire system state using a single IAC_GET"""
        self._system_state = iac_get(self._loki_proxy, 'node_1/application/system_state')

    def _get_from_system_state(self, *keys):
        """Return a value from the system state dict"""
        self._update_system_state()
        
        data = self._system_state
        for key in keys:
            if isinstance(data, dict) and key in data:
                data = data[key]
            else:
                return None
        return data

    @property
    def loki_connected(self):
        return self._get_from_system_state('MAIN_EN')

    @loki_connected.setter
    def loki_connected(self, value):
        path = 'node_1/application/system_state/'
        param = 'MAIN_EN'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def loki_initialised(self):
        return self._get_from_system_state('BD_INITIALISE', 'DONE')

    @loki_initialised.setter
    def loki_initialised(self, value):
        path = 'node_1/application/system_state/BD_INITIALISE/'
        param = 'TRIGGER'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def loki_sync(self):
        return self._get_from_system_state('SYNC')

    @loki_sync.setter
    def loki_sync(self, value):
        path = 'node_1/application/system_state/'
        param = 'SYNC'
        iac_set(self._loki_proxy, path, param, value)

    @property
    def loki_ready(self):
        self._update_system_state()
        main_en = self._system_state.get('MAIN_EN')
        bd_initialise_done = self._system_state.get('BD_INITIALISE', {}).get('DONE')
        sync = self._system_state.get('SYNC')
        
        return all([main_en, bd_initialise_done, sync])