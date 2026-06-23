"""CC (L0 Core Contracts).

Provides stable, versioned schemas, identifiers, quantity model, safety policy
and governance primitives per QXtrl planning.

All upper layers (L1-L9) must depend on these contracts, not on concrete
implementations or legacy path strings.
"""

from .errors import (
    QXtrlError,
    QXtrlValidationError,
    SafetyViolation,
    SchemaVersionError,
)
from .quantity import Quantity
from .validators import (
    validate_element_id,
    validate_identity_id,
    validate_line_id,
    validate_device_id,
    validate_channel_id,
    validate_resource_group_id,
    validate_schema_version,
    KNOWN_UNITS,
    is_usable_for_control,
)
from .models import (
    L0Base,
    Identity,
    SourceRef,
    DataQuality,
    QuantityField,  # helper for inline quantities
    ChipModel,
    QubitElement,
    ResonatorElement,
    CouplerElement,
    WiringGraph,
    WiringEdge,
    HardwareChannels,
    WiringEndpoint,
    HardwareInventory,
    Device,
    Channel,
    ChannelCapability,
    SafetyPolicy,
    L0SnapshotRef,
)

# Convenience examples for quick start and demos (re-exported for stable import path)
from .examples import minimal_rabi_lab, make_rabi_lab, public_willow_chip_example  # type: ignore


__all__ = [
    # errors
    "QXtrlError",
    "QXtrlValidationError",
    "SafetyViolation",
    "SchemaVersionError",
    # quantity + validators
    "Quantity",
    "validate_element_id",
    "validate_identity_id",
    "validate_line_id",
    "validate_device_id",
    "validate_channel_id",
    "validate_resource_group_id",
    "validate_schema_version",
    "KNOWN_UNITS",
    "is_usable_for_control",
    # models
    "L0Base",
    "Identity",
    "SourceRef",
    "DataQuality",
    "QuantityField",
    "ChipModel",
    "QubitElement",
    "ResonatorElement",
    "CouplerElement",
    "WiringGraph",
    "WiringEdge",
    "HardwareChannels",
    "WiringEndpoint",
    "HardwareInventory",
    "Device",
    "Channel",
    "ChannelCapability",
    "SafetyPolicy",
    "L0SnapshotRef",
    # examples
    "minimal_rabi_lab",
    "public_willow_chip_example",
]
