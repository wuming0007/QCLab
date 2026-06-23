"""DS (L5 Data & State) facade.

Public stable surface for MVP:
- RunManifest (Pydantic primary per design)
- FileResultStore + record_runtime_result (preferred over legacy)
- MemoryDataSink
- legacy record_run / LegacyRunManifest (compat, deprecated)
"""

from .manifest import RunManifest as LegacyRunManifest, record_run  # legacy compat (deprecated)
from .contracts import (
    RunManifest,  # primary Pydantic type
    DatasetRef,
    DSDiagnostic,
    DatasetMetadata,
    DSError,
    DSCode,
)
from .result.file_store import FileResultStore
from .sink.memory import MemoryDataSink
from .result.manifest_builder import build_from_runtime_result

# Preferred entry for L4
def record_runtime_result(
    *, runtime_result, spec=None, bundle=None, base_dir: str = "runs"
) -> str:
    """Convenience: create default FileResultStore and record L4 result."""
    store = FileResultStore(base_dir=base_dir)
    return store.record_runtime_result(runtime_result=runtime_result, spec=spec, bundle=bundle)


__all__ = [
    "RunManifest",  # primary (Pydantic)
    "LegacyRunManifest",  # legacy dataclass, deprecated
    "record_run",  # legacy compat (deprecated)
    "DatasetRef",
    "DSDiagnostic",
    "DatasetMetadata",
    "DSError",
    "DSCode",
    "FileResultStore",
    "MemoryDataSink",
    "build_from_runtime_result",
    "record_runtime_result",
]

