from qlispc import Architecture
from qlispc.arch.baqis.config import QuarkConfig, QuarkLocalConfig

from .code import assembly_code
from .data import assembly_data

baqis2Architecture = Architecture('baqis2', "", assembly_code, assembly_data,
                                  QuarkConfig, QuarkLocalConfig)
