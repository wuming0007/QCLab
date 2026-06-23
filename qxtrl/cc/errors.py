"""L0 (CC) domain errors.

All L0 validation and governance failures must raise from this module so that
upper layers can catch specifically and produce user/actionable messages.
"""

from typing import Any, Optional


class QXtrlError(Exception):
    """Base exception for all QXtrl L0+ errors.

    Attributes:
        code: machine-readable short code (e.g. "L0_ID_INVALID")
        details: structured context for logging / UI
    """

    def __init__(self, message: str, code: str = "QXTRL_ERROR", details: Optional[dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.details:
            return f"{base} | code={self.code} details={self.details}"
        return f"{base} | code={self.code}"


class QXtrlValidationError(QXtrlError):
    """Schema / ID / value validation failure (missing field, bad format, unit error, etc)."""

    def __init__(self, message: str, field: Optional[str] = None, rule: Optional[str] = None, **kwargs: Any):
        details = {"field": field, "rule": rule, **kwargs}
        super().__init__(message, code="L0_VALIDATION", details=details)
        self.field = field
        self.rule = rule


class SafetyViolation(QXtrlError):
    """Operation or value violates active SafetyPolicy or three-layer limit."""

    def __init__(self, message: str, policy_id: Optional[str] = None, limit_kind: Optional[str] = None, **kwargs: Any):
        details = {"policy_id": policy_id, "limit_kind": limit_kind, **kwargs}
        super().__init__(message, code="L0_SAFETY_VIOLATION", details=details)


class SchemaVersionError(QXtrlError):
    """Incompatible or unknown schema_version encountered."""

    def __init__(self, message: str, expected: Optional[str] = None, got: Optional[str] = None):
        super().__init__(
            message,
            code="L0_SCHEMA_VERSION",
            details={"expected": expected, "got": got},
        )
