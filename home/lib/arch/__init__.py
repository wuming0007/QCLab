from qlispc import register_arch

from .baqis2 import baqis2Architecture
from .rcp import rcpArchitecture

register_arch(rcpArchitecture)
register_arch(baqis2Architecture)
