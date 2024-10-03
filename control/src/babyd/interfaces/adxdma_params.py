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
        # Fetch the current configuration
        control_data = iac_get(self._adxdma, "control", as_dict=True)
        logging.debug(f'control data: {control_data}')
        
        # Initialise frame count properties
        frame_count_data = control_data.get('control', {}).get('frame_count', {})
        self._frame_count_cores = list(frame_count_data.keys())
        logging.debug(f"Frame count cores: {self._frame_count_cores}")
        for core in self._frame_count_cores:
            logging.debug(f"Creating frame count property for core {core}")
            self._create_frame_count_property(core)

        # Initialise link status properties
        link_status_data = control_data.get('control', {}).get('link_status', {})
        self._link_status_cores = list(link_status_data.keys())
        logging.debug(f"Link status cores: {self._link_status_cores}")
        for core in self._link_status_cores:
            logging.debug(f"Creating link status property for core {core}")
            self._create_link_status_property(core)

    def _create_frame_count_property(self, core):
        def getter(core):
            return iac_get(self._adxdma, f"control/frame_count/{core}")
        setter = lambda self, value: logging.error(f"Frame count for core {core} is non-mutable")
        prop = property(partial(getter, core), setter)
        setattr(self.__class__, f"frame_count_{core}", prop)
        self._dynamic_properties[f"frame_count_{core}"] = prop

    def _create_link_status_property(self, core):
        def getter(core):
            return iac_get(self._adxdma, f"control/link_status/{core}")
        setter = lambda self, value: logging.error(f"Link status for core {core} is non-mutable")
        prop = property(partial(getter, core), setter)
        setattr(self.__class__, f"link_status_{core}", prop)
        self._dynamic_properties[f"link_status_{core}"] = prop

    def get_dynamic_properties(self) -> Dict[str, property]:
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

    def set_ip(self, ip, path):
        try:
            # Attempt to create an ipaddress object to check if ip address is valid
            ipaddress.ip_address(ip)
            iac_set(self._adxdma, "control/", path, ip)
        except ValueError:
            logging.error(f'Ipaddress: {ip}, is invalid')
