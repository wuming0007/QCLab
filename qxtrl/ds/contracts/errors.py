"""Structured DS errors and codes per design."""

from __future__ import annotations

from typing import Optional


class DSCode:
    """Error codes for L5 (used in DSDiagnostic and exceptions)."""
    SNAPSHOT_NOT_FOUND = "DS-SNAPSHOT-NOT-FOUND"
    SNAPSHOT_NOT_PUBLISHED = "DS-SNAPSHOT-NOT-PUBLISHED"
    RUN_ALREADY_FINALIZED = "DS-RUN-ALREADY-FINALIZED"
    DATASET_WRITE_FAILED = "DS-DATASET-WRITE-FAILED"
    MANIFEST_INCOMPLETE = "DS-MANIFEST-INCOMPLETE"
    MANIFEST_FINALIZE_FAILED = "DS-MANIFEST-FINALIZE-FAILED"
    TIMING_INCOMPLETE = "DS-TIMING-INCOMPLETE"
    RUN_ID_CONFLICT = "DS-RUN-ID-CONFLICT"
    ABSOLUTE_PATH_FORBIDDEN = "DS-ABSOLUTE-PATH-FORBIDDEN"
    SINK_OVERLOAD = "DS-SINK-OVERLOAD"
    CONFIG_WRITE_DENIED = "DS-CONFIG-WRITE-DENIED"


class DSError(Exception):
    """Typed error for L5 operations. Carries diagnostic info."""
    def __init__(self, code: str, message: str, *, run_id: Optional[str] = None,
                 recoverable: bool = False, details: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.run_id = run_id
        self.recoverable = recoverable
        self.details = details or {}

    def to_diagnostic(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "run_id": self.run_id,
            "recoverable": self.recoverable,
            "details": self.details,
        }
