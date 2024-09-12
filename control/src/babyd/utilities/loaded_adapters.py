from dataclasses import dataclass

from odin.adapters.proxy import ProxyAdapter
from munir.adapter import MunirAdapter

@dataclass
class Adapters:
    munir: MunirAdapter
    loki_proxy: ProxyAdapter