# /orchestrator/services/cbom_service.py

import uuid
from datetime import datetime, timezone
from models import KeyMetadata
from cyclonedx.model.bom import Bom, BomMetaData
from cyclonedx.model import Property
from cyclonedx.model.component import Component, ComponentType
from cyclonedx.model.tool import Tool
from cyclonedx.model.crypto import (
    CryptoProperties, CryptoAssetType, 
    RelatedCryptoMaterialProperties,
    RelatedCryptoMaterialType, 
    RelatedCryptoMaterialState,
)

# --- Helper Functions ---

def _add_prop(props, name, value):
    if value is not None:
        props.append(Property(name=name, value=str(value)))

def _status_to_rcm_state(status: str | None):
    """
    Maps an internal key status string to a standard RelatedCryptoMaterialState enum.
    Returns None if the status is not recognized.
    """
    # Sanitize the input string to be lowercase and free of leading/trailing whitespace
    s = (status or "").strip().lower()

    if not s:
        return None

    if s == "enabled":
        return RelatedCryptoMaterialState.ACTIVE
    
    if s in {"disabled", "inactive"}:
        return RelatedCryptoMaterialState.DEACTIVATED
    
    # Checks if the status indicates a key is pending deletion
    if s.startswith("pendingdeletion"):
        return RelatedCryptoMaterialState.SUSPENDED
    
    if s == "deleted":
        return RelatedCryptoMaterialState.DESTROYED

    # If no match is found, log it and return None
    raise_alarm('INFO', 'CBOM_KEY_STATUS_UNRECOGNIZED', f"Unrecognized internal key status '{status}'.")
    return None

def _key_to_component(k):
    component = Component(
        type=ComponentType.CRYPTOGRAPHIC_ASSET,
        name=k.key_id,
        group=k.cloud_provider,
        bom_ref=f"urn:kms:key:{k.key_arn}"
    )
    component.crypto_properties = CryptoProperties(
        asset_type=CryptoAssetType.RELATED_CRYPTO_MATERIAL,
        related_crypto_material_properties=RelatedCryptoMaterialProperties(
            type=RelatedCryptoMaterialType.KEY,
            id=k.key_id,
            state=_status_to_rcm_state(k.status),
        )
    )
    props = []
    _add_prop(props, "kms:provider", k.cloud_provider)
    _add_prop(props, "kms:region", k.region)
    _add_prop(props, "kms:arn", k.key_arn)
    _add_prop(props, "kms:status", k.status)
    _add_prop(props, "kms:algorithm", k.algorithm)
    _add_prop(props, "kms:protection_level", k.protection_level)
    _add_prop(props, "kms:rotation_enabled", str(k.rotation_enabled).lower())
    component.properties = props
    return component

# --- Main Service Function ---
def build_cbom_report():
    """Queries all keys and builds a CycloneDX BOM object."""
    
    # Query all keys from the database.
    keys = KeyMetadata.query.order_by(KeyMetadata.cloud_provider).all()
    
    # Construct the main BOM object.
    bom = Bom()
    bom.serial_number = uuid.uuid4()
    bom.metadata = BomMetaData(timestamp=datetime.now(timezone.utc))
    bom.metadata.tools.components.add(Tool(vendor="Key Management Portal", name="CBOM API"))

    for k in keys:
        bom.components.add(_key_to_component(k))

    return bom