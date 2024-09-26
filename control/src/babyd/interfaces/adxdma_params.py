from dataclasses import dataclass
import ipaddress
import logging

from babyd.adxdma.adapter import BabyDAdapter

from ..utilities.util import iac_get, iac_set

@dataclass
class AlphaDataParams:
    _adxdma: BabyDAdapter

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
    def link0_status(self):
        return iac_get(self._adxdma, "control/link_status/link0")
    
    @link0_status.setter
    def link0_status(self, value):
        logging.error("Link0_status is non mutable, ignoring value provided")

    @property
    def link1_status(self):
        return iac_get(self._adxdma, "control/link_status/link1")
    
    @link1_status.setter
    def link1_status(self, value):
        logging.error("Link1_status is non mutable, ignoring value provided")

    @property
    def ch0_fc(self):
        """Channel 0 Frame count"""
        return iac_get(self._adxdma, "control/frame_count/ch0")
    
    @ch0_fc.setter
    def ch0_fc(self, value):
        logging.error("ch0_fc is non mutable, ignoring value provided")

    @property
    def ch1_fc(self):
        return iac_get(self._adxdma, "control/frame_count/ch1")
    
    @ch1_fc.setter
    def ch1_fc(self, value):
        logging.error("ch1_fc is non mutable, ignoring value provided")

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
