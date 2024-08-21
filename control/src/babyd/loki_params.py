from dataclasses import dataclass

@dataclass
class LokiParams:
    _system_state: dict = None

    def update_system_state(self, params):
        """Update the entire system state using a single IAC_GET"""
        self._system_state = params

    def _get_from_system_state(self, *keys):
        """Return a value from the system state dict"""
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

    @property
    def loki_initialised(self):
        return self._get_from_system_state('BD_INITIALISE', 'DONE')

    @property
    def loki_sync(self):
        return self._get_from_system_state('SYNC')

    @property
    def loki_ready(self):
        main_en = self._get_from_system_state('MAIN_EN')
        bd_initialise_done = self._get_from_system_state('BD_INITIALISE', 'DONE')
        sync = self._get_from_system_state('SYNC')
        
        return all([main_en, bd_initialise_done, sync])
    
# Make controller handle updating of loki params
# Have updating of iac adapters handled in executor
# Have the execting function called in executor
# Use a state machine to handle the calling of captures