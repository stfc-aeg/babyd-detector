from dataclasses import dataclass, field
from functools import partial
import ipaddress
import logging
from typing import Dict, List

from babyd.adxdma.adapter import BabyDAdapter

from ..utilities.util import iac_get, iac_set

@dataclass
class AlphaDataParams:
    _adxdma: BabyDAdapter
    _frame_count_cores: List[str] = field(default_factory=list)
    _link_status_cores: List[int] = field(default_factory=list)
    _dynamic_properties: Dict[str, property] = field(default_factory=dict)

    def __post_init__(self):
        self._initialize_dynamic_properties()

    def _initialize_dynamic_properties(self):
        # Fetch the control structure from adxdma adapter
        control_data = iac_get(self._adxdma, "control", as_dict=True)
        # create a list of the link status entries and the length of this list
        link_status_data = control_data.get('control', {}).get('link_status', {})
        self._link_status_cores = list(link_status_data.keys())
        self.link_status_length = len(self._link_status_cores)
        # for each link status core create a link status property
        for core in self._link_status_cores:
            self._create_link_status_property(core)

        # create a list of the frame count entries
        frame_count_data = control_data.get('control', {}).get('frame_count', {})
        self._frame_count_cores = list(frame_count_data.keys())
        # for each frame count core create a link status property
        for core in self._frame_count_cores:
            self._create_frame_count_property(core)

    def _create_frame_count_property(self, core):
        """
        Create the frame count properties in the AlphaDataParams dataclass for use in
        the adxdma parameter tree.
        
        Creates a getter that uses iac_get and a custom path to the frame count for the 
        core passed to the function, creates a setter that prevents values being set, 
        adjusts the name of the parameter so that it matches up with the link status cores
        and then assigns this to the dynamic properties dict.
        
        :param core: The Frame count core to target
        """
        # create a getter that uses an iac_get and the core path to target
        getter = lambda: iac_get(self._adxdma, f"control/frame_count/{core}")
        # create a setter that blocks values being set
        setter = lambda value: logging.error(f"Frame count for core {core} is non-mutable")
        # create a propety that uses the getter as the fget and setter as the fset
        # Wrapped in partials as property expects its args to behave as functions
        prop = property(partial(getter), partial(setter))
        # adjust the name of core so that it related to the corresponding link status core
        adjusted_core = int(core) - self.link_status_length
        # add the generated property to the list of dynamic properties
        self._dynamic_properties[f"frame_count_{adjusted_core}"] = prop

    def _create_link_status_property(self, core):
        """
        Create the link status properties in the AlphaDataParams dataclass for use in
        the adxdma parameter tree.
        
        Creates a getter that uses iac_get and a custom path to the link status for the 
        core passed to the function, creates a setter that prevents values being set and
        then assigns this to the dynamic properties dict.
        
        :param core: The Frame count core to target
        """
        getter = lambda: iac_get(self._adxdma, f"control/link_status/{core}")
        setter = lambda value: logging.error(f"Link status for core {core} is non-mutable")
        prop = property(partial(getter), partial(setter))
        self._dynamic_properties[f"link_status_{core}"] = prop

    def get_dynamic_properties(self):
        return self._dynamic_properties

    @property
    def available_speeds(self):
        return iac_get(self._adxdma, "control/clock_speed/options" )
    
    @available_speeds.setter
    def available_speeds(self, value):
        logging.error('Clock options are non mutable, ignoring value provided')

    @property
    def clock_speed(self):
        return iac_get(self._adxdma, "control/clock_speed/speed")
    
    @clock_speed.setter
    def clock_speed(self, value):
        if value in self.available_speeds:
            iac_set(self._adxdma, "control/clock_speed/", "speed", value)
        else:
            logging.error("Clock speed invalid")

    @property
    def ip_local(self):
        return iac_get(self._adxdma, "control/ip_local")
    
    @ip_local.setter
    def ip_local(self, value):
        self.set_ip(value, "ip_local")

    @property
    def ip_remote(self):
        return iac_get(self._adxdma, "control/ip_remote")
    
    @ip_remote.setter
    def ip_remote(self, value):
        self.set_ip(value, "ip_remote")
    
    @property
    def connected(self):
        return iac_get(self._adxdma, "control/is_connected")
    
    @connected.setter
    def connected(self, value):
        if value == True:
            iac_set(self._adxdma, "control/", "connect", value)
            logging.info("triggering connected")
        elif value == False:
            iac_set(self._adxdma, "control/", "disconnect", value)
            logging.info("triggering disconnected")
        else:
            logging.error(f'Value: {value} invalid, provide Bool')

    @property
    def available_triggers(self):
        return iac_get(self._adxdma, "control/trigger/options" )
    
    @available_triggers.setter
    def available_triggers(self, value):
        logging.error('Trigger options are non mutable, ignoring value provided')

    @property
    def trigger_mode(self):
        return iac_get(self._adxdma, "control/trigger/mode")
    
    @trigger_mode.setter
    def trigger_mode(self, value):
        if value in self.available_triggers:
            iac_set(self._adxdma, "control/trigger/", "mode", value)
        else:
            logging.error(f"Trigger mode: {value} invalid")

    @property
    def frame_per_event(self):
        return iac_get(self._adxdma, "control/trigger/frame_per_event")
    
    @frame_per_event.setter
    def frame_per_event(self, value):
        if type(value) == int:
            iac_set(self._adxdma, "control/trigger/", "frame_per_event", value)
        else:
            logging.error(f"Value: {value} invalid, provide integer value")

    def set_ip(self, ip, path):
        try:
            # Attempt to create an ipaddress object to check if ip address is valid
            ipaddress.ip_address(ip)
            iac_set(self._adxdma, "control/", path, ip)
        except ValueError:
            logging.error(f'Ipaddress: {ip}, is invalid')
