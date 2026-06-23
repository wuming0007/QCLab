"""Quantity model for L0.

Represents physical values with unit and optional uncertainty.
Follows naming rules: never encode variable physics values into IDs.
"""

import math
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator

from .errors import QXtrlValidationError
from .validators import KNOWN_UNITS


ValueT = Union[float, Literal["unknown"]]


class Quantity(BaseModel):
    """A physical quantity with unit.

    value may be numeric or the string "unknown" (per L0 schema examples).
    unit must be from KNOWN_UNITS for MVP (case sensitive, prefer SI).
    uncertainty is optional; when present must use same unit.

    Examples:
        Quantity(value=5.23e9, unit="Hz", uncertainty=2e6)
        Quantity(value="unknown", unit="V")
    """

    value: ValueT = Field(..., description="Numeric value or 'unknown'")
    unit: str = Field(..., min_length=1, description="Unit string, e.g. Hz, s, V, Sa/s")
    uncertainty: Optional[ValueT] = Field(
        default=None, description="Uncertainty in same unit; None or 'unknown'"
    )
    source: Optional[str] = Field(
        default=None, description="Origin label e.g. 'lab_calibration' or 'public_example'"
    )

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "extra": "forbid",
    }

    @field_validator("unit")
    @classmethod
    def _validate_unit(cls, v: str) -> str:
        if v not in KNOWN_UNITS:
            # Allow future extension but fail visibly for now
            raise QXtrlValidationError(
                f"Unknown unit '{v}'. Use one of {sorted(KNOWN_UNITS)} or extend validators.",
                field="unit",
                rule="R-UNIT-KNOWN",
            )
        return v

    @field_validator("value", "uncertainty", mode="before")
    @classmethod
    def _coerce_unknown(cls, v: Any) -> Any:
        if isinstance(v, str) and v.lower() == "unknown":
            return "unknown"
        if v is None:
            return v
        if isinstance(v, bool):
            # bool is subclass of int, explicitly reject to avoid silent True->1.0 etc.
            raise QXtrlValidationError(
                "Quantity value must not be bool; use explicit number or 'unknown'",
                field="value",
                rule="R-QUANTITY-VALUE",
            )
        try:
            f = float(v)
        except (TypeError, ValueError):
            # Allow only float or explicit unknown at this layer
            if v == "unknown":
                return v
            raise QXtrlValidationError(
                f"Quantity value must be number or 'unknown', got {type(v)}",
                field="value",
                rule="R-QUANTITY-VALUE",
            )
        if math.isnan(f) or math.isinf(f):
            raise QXtrlValidationError(
                "Quantity value must not be NaN or Inf",
                field="value",
                rule="R-QUANTITY-VALUE",
            )
        return f

    def is_unknown(self) -> bool:
        return self.value == "unknown"

    def __repr__(self) -> str:
        unc = f" ±{self.uncertainty}" if self.uncertainty is not None else ""
        src = f" [{self.source}]" if self.source else ""
        return f"Quantity({self.value}{unc} {self.unit}{src})"
