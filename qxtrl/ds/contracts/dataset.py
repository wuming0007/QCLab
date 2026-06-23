"""DatasetMetadata and related for L5."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    schema_version: Literal["qxtrl.ds.DatasetMetadata/v0.1"] = "qxtrl.ds.DatasetMetadata/v0.1"
    run_id: str
    kind: Literal["raw_iq", "raw_trace", "processed_curve", "analysis_result", "log", "events", "timings"] = "raw_iq"
    format: str = "json"  # json, numpy-list, etc. for MVP
    shape: Optional[list[int]] = None
    dtype: Optional[str] = None
    dims: list[str] = Field(default_factory=list)
    units: dict[str, str] = Field(default_factory=dict)
    content_hash: Optional[str] = None
    lineage: dict[str, Any] = Field(default_factory=dict)  # parent refs etc.

    model_config = {"frozen": True}
