"""ID, schema_version and governance validators for L0 / CC Core Contracts.

Implements rules from QXtrl_L0契约层命名与编码规则.md (R-001 to R-016).
All IDs are canonical, stable, lowercase, dot-separated.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final, Set

from .errors import QXtrlValidationError

if TYPE_CHECKING:
    from .models import DataQuality

# Allowed characters for canonical IDs
ID_CHAR_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_.]+$")

# Element kinds
QUBIT_RE: Final[re.Pattern[str]] = re.compile(r"^q\d{3}$")  # q000-q999
RESONATOR_RE: Final[re.Pattern[str]] = re.compile(r"^rr_q\d{3}$")
COUPLER_RE: Final[re.Pattern[str]] = re.compile(r"^(tc|fc)_q\d{3}_q\d{3}$")
BIAS_RE: Final[re.Pattern[str]] = re.compile(r"^bias_.+$")

# Line kinds (logical)
LINE_RE: Final[re.Pattern[str]] = re.compile(r"^line\.(xy|ro|z|pump|trig|lo|marker)\..+$")

# Device / channel / rg
DEVICE_RE: Final[re.Pattern[str]] = re.compile(r"^dev\.[a-z]+\.[a-z0-9_]+$")
CHANNEL_RE: Final[re.Pattern[str]] = re.compile(r"^chan\.[a-z]+\.[a-z0-9_]+\.[a-z0-9]+$")
RG_RE: Final[re.Pattern[str]] = re.compile(r"^rg\.[a-z0-9_.]+$")

# Schema version
SCHEMA_VERSION_RE: Final[re.Pattern[str]] = re.compile(r"^qxtrl\.cc\.[A-Za-z0-9_]+/v\d+\.\d+$")

# Known units (MVP set, extend only after rule review)
KNOWN_UNITS: Final[Set[str]] = {
    "Hz", "kHz", "MHz", "GHz",
    "s", "ms", "us", "ns", "ps",
    "V", "mV", "uV",
    "A", "mA", "uA",
    "W", "mW", "dBm",
    "Sa/s", "GSa/s", "MSa/s",
    "a.u.",  # arbitrary units for normalized amp etc.
    "fraction",
    "K", "mK",
    "rad", "deg",
    "ohm",
}


def _check_chars(s: str, field: str) -> None:
    if not ID_CHAR_RE.match(s):
        raise QXtrlValidationError(
            f"ID '{s}' contains illegal characters (only a-z0-9_. allowed)",
            field=field,
            rule="R-002",
        )


def validate_element_id(element_id: str) -> str:
    """Validate chip element ID (qubit, rr, coupler, bias etc).

    Rules: R-001, R-003, R-004. Never encode frequency etc into ID.
    """
    _check_chars(element_id, "element_id")
    if QUBIT_RE.match(element_id):
        return element_id
    if RESONATOR_RE.match(element_id):
        return element_id
    if COUPLER_RE.match(element_id):
        # enforce sorted endpoints for tc/fc (see naming rule)
        parts = element_id.split("_")
        if len(parts) >= 3:
            a = parts[-2]
            b = parts[-1]
            if a > b:
                raise QXtrlValidationError(
                    f"Coupler ID must have sorted endpoints: got {element_id}, expected {'_'.join(parts[:-2])}_{b}_{a}",
                    field="element_id",
                    rule="R-003-coupler-order",
                )
        return element_id
    if BIAS_RE.match(element_id):
        return element_id
    raise QXtrlValidationError(
        f"Invalid chip element_id '{element_id}'. Expected qNNN, rr_qNNN, (tc|fc)_qAAA_qBBB or bias_*",
        field="element_id",
        rule="R-ELEMENT-ID",
    )


def validate_line_id(line_id: str) -> str:
    """Validate logical line ID. line.<kind>.<target>"""
    _check_chars(line_id, "line_id")
    if not LINE_RE.match(line_id):
        raise QXtrlValidationError(
            f"Invalid line_id '{line_id}'. Must match line.(xy|ro|z|pump|trig|lo|marker).<target>",
            field="line_id",
            rule="R-LINE-ID",
        )
    return line_id


def validate_device_id(device_id: str) -> str:
    """Validate device installation position ID (not physical asset)."""
    _check_chars(device_id, "device_id")
    if not DEVICE_RE.match(device_id):
        raise QXtrlValidationError(
            f"Invalid device_id '{device_id}'. Format: dev.<type>.<name> e.g. dev.awg.awg01",
            field="device_id",
            rule="R-DEVICE-ID",
        )
    return device_id


def validate_channel_id(channel_id: str) -> str:
    """Validate hardware channel ID (port level)."""
    _check_chars(channel_id, "channel_id")
    if not CHANNEL_RE.match(channel_id):
        raise QXtrlValidationError(
            f"Invalid channel_id '{channel_id}'. Format: chan.<type>.<dev>.<port> e.g. chan.awg.awg01.out01",
            field="channel_id",
            rule="R-CHANNEL-ID",
        )
    return channel_id


def validate_resource_group_id(rg_id: str) -> str:
    """Validate resource group ID (for scheduler conflict modeling)."""
    _check_chars(rg_id, "resource_group_id")
    if not RG_RE.match(rg_id):
        raise QXtrlValidationError(
            f"Invalid resource_group_id '{rg_id}'. Format: rg.<type>.<name>",
            field="resource_group_id",
            rule="R-RG-ID",
        )
    return rg_id


def validate_identity_id(identity_id: str) -> str:
    """Validate top-level Identity.id (for HardwareInventory, ChipModel, SafetyPolicy, snapshots, etc.).

    Follows L0 naming rules: stable, lowercase, dot-separated, only a-z0-9_.
    Must not contain spaces, uppercase, Chinese, etc.
    """
    if not identity_id or len(identity_id) < 3:
        raise QXtrlValidationError(
            "identity id must be non-empty stable identifier (min length 3)",
            field="id",
            rule="R-001",
        )
    _check_chars(identity_id, "id")
    return identity_id



def validate_schema_version(
    version: str, *, expected: str | None = None, expected_prefix: str = "qxtrl.cc."
) -> str:
    """Validate schema_version string.

    - Always checks format (qxtrl.cc.<Name>/vX.Y)
    - If `expected` is provided, also enforces exact match (used for type safety).
    """
    if not SCHEMA_VERSION_RE.match(version):
        raise QXtrlValidationError(
            f"Invalid schema_version '{version}'. Must be qxtrl.cc.<Name>/v<major>.<minor>",
            field="schema_version",
            rule="R-015",
        )
    if not version.startswith(expected_prefix):
        raise QXtrlValidationError(
            f"schema_version '{version}' does not start with expected prefix '{expected_prefix}'",
            field="schema_version",
            rule="R-015-prefix",
        )
    if expected is not None and version != expected:
        raise QXtrlValidationError(
            f"schema_version mismatch: got '{version}', expected exact '{expected}' for this object type",
            field="schema_version",
            rule="L0-SCHEMA-NAME-MISMATCH",
        )
    return version


def is_usable_for_control(data_quality: dict | DataQuality) -> bool:
    """Central helper.

    Returns True only when the object is fully approved for control.

    For dict input (e.g. from JSON/config snapshots), requires:
        - usable_for_control is True
        - status == "approved"
        - approved_by is truthy

    For DataQuality model, delegates to the canonical is_approved_for_control().
    """
    if isinstance(data_quality, dict):
        # Revocation check first
        if data_quality.get("revoked_by") or data_quality.get("revoked_at"):
            return False
        return (
            bool(data_quality.get("usable_for_control"))
            and data_quality.get("status") == "approved"
            and bool(data_quality.get("approved_by"))
            and bool(data_quality.get("approved_at"))
        )
    # DataQuality model: use the authoritative method
    if hasattr(data_quality, "is_approved_for_control"):
        return data_quality.is_approved_for_control()
    # Fallback for raw objects
    if getattr(data_quality, "revoked_by", None) or getattr(data_quality, "revoked_at", None):
        return False
    return (
        bool(getattr(data_quality, "usable_for_control", False))
        and getattr(data_quality, "status", None) == "approved"
        and bool(getattr(data_quality, "approved_by", None))
        and bool(getattr(data_quality, "approved_at", None))
    )
