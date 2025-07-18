from qlispc import Architecture

from .code import assembly_code
from .config import QuarkConfig, QuarkLocalConfig
from .data import assembly_data

rcpArchitecture = Architecture('rcp', "", assembly_code, assembly_data,
                               QuarkConfig, QuarkLocalConfig)
