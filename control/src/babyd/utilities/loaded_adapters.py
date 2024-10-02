from dataclasses import dataclass

from odin.adapters.proxy import ProxyAdapter
from munir.adapter import MunirAdapter
from babyd.adxdma.adapter import BabyDAdapter

@dataclass
class Adapters:
    munir: MunirAdapter
    loki_proxy: ProxyAdapter
    adxdma: BabyDAdapter