# /orchestrator/services/converters.py

"""
This module provides converter functions to standardize cryptographic key metadata from various
cloud providers (AWS, Azure, GCP) into a common `KeyMetadata` model. Each function is
responsible for parsing the provider-specific API response and mapping its fields to the
unified model, ensuring consistent data representation across the system.
"""

from models import KeyMetadata
from datetime import datetime, timezone

def from_aws_key(key: dict) -> KeyMetadata:
    """
    Converts an AWS KMS key dictionary representation into a KeyMetadata object.

    Args:
        key (dict): A dictionary representing a single key from the AWS KMS API response
                    (e.g., from `list_keys` and `describe_key` calls).

    Returns:
        KeyMetadata: An instance of the KeyMetadata model populated with the AWS key's data.
    """
    return KeyMetadata(
        key_id=key['KeyId'],
        key_arn=key['Arn'],
        cloud_provider='aws',
        # The CreationDate from AWS is already a timezone-aware datetime object.
        created_at=key['CreationDate'],
        # Map the boolean 'Enabled' status to a more descriptive string.
        status='Enabled' if key['Enabled'] else 'Disabled',
        # Safely get rotation status; default to False if not present.
        rotation_enabled=key.get('RotationEnabled', False),
        # AWS uses 'Tags' for key-value labels.
        labels=key.get('Tags', {}),
        origin=key.get('Origin'),
        # The region is extracted from the ARN (Amazon Resource Name).
        # ARN format: arn:partition:service:region:account-id:resource-type/resource-id
        region=key['Arn'].split(':')[3],
        # The describe_key API response for AWS KMS doesn't include specific version information.
        version=None,
        usage=key.get('KeyUsage'),
        # In AWS, this is referred to as the CustomerMasterKeySpec.
        algorithm=key.get('CustomerMasterKeySpec'),
        # Determine protection level based on whether 'HSM' is in the key spec.
        protection_level='HSM' if 'HSM' in key.get('KeySpec', '') else 'SOFTWARE',
        description=key.get('Description'),
        # This field is not directly available in the AWS response; set to a default.
        is_primary=False,
    )

def from_azure_key(key: dict) -> KeyMetadata:
    """
    Converts an Azure Key Vault key dictionary representation into a KeyMetadata object.

    Args:
        key (dict): A dictionary representing a single key from the Azure Key Vault API response.

    Returns:
        KeyMetadata: An instance of the KeyMetadata model populated with the Azure key's data.
    """
    # Azure key attributes are nested within an 'attributes' dictionary.
    attributes = key.get('attributes', {})
    # Convert the Unix timestamp 'created' time to a timezone-aware datetime object.
    created_at = datetime.fromtimestamp(attributes.get('created'), timezone.utc) if attributes.get('created') else None

    # The Key URI (kid) contains the vault name, key name, and key version.
    # Example URI: https://my-vault.vault.azure.net/keys/my-key/1234abcd5678efgh
    key_uri = key['key']['kid']
    key_id_parts = key_uri.split('/')
    # Create a simplified, readable key_id from the last two parts of the URI (e.g., "my-key/1234abcd...").
    key_id = f"{key_id_parts[-2]}/{key_id_parts[-1]}"

    return KeyMetadata(
        key_id=key_id,
        # The full Key URI serves as the ARN equivalent.
        key_arn=key_uri,
        cloud_provider='azure',
        created_at=created_at,
        status='Enabled' if attributes.get('enabled') else 'Disabled',
        # Rotation is considered enabled if a 'rotationPolicy' object exists.
        rotation_enabled='rotationPolicy' in key,
        # Azure uses 'tags' for key-value labels.
        labels=key.get('tags', {}),
        # Origin is not directly provided, so we assume it's Azure-provided for Key Vault keys.
        origin='azure_provided',
        # The 'location' field specifies the region. Default to 'unknown' if not present.
        region=key.get("location", "unknown"),
        # The key version is the last part of the Key URI.
        version=key_id_parts[-1],
        # The 'key_ops' field is a list of allowed operations; join them into a string.
        usage=','.join(key['key'].get('key_ops', [])),
        # 'kty' represents the key type (e.g., 'RSA', 'EC').
        algorithm=key['key'].get('kty'),
        # Protection level is HSM if the key type string includes 'hsm'.
        protection_level='HSM' if 'hsm' in key['key'].get('kty', '').lower() else 'SOFTWARE',
        # Azure Key Vault API doesn't provide a dedicated description field for keys.
        description=None,
        # This field is not directly available in the Azure response; set to a default.
        is_primary=False,
    )

def from_gcp_key(key_data: dict) -> KeyMetadata:
    """
    Converts a GCP Cloud KMS key dictionary representation into a KeyMetadata object.
    This function expects the primary key version data to be included.

    Args:
        key_data (dict): A dictionary representing a single key from the GCP KMS API,
                         which must include details of its 'primary' version.

    Returns:
        KeyMetadata: An instance of the KeyMetadata model populated with the GCP key's data.

    Raises:
        ValueError: If the 'primary' version information is missing from the input data.
    """
    # GCP's API response for a key includes information about its primary version.
    version = key_data.get('primary')

    # The primary version is essential for populating most of the metadata.
    if not version:
        raise ValueError("GCP key data is missing 'primary' version information.")

    # Convert the ISO 8601 formatted timestamp string to a timezone-aware datetime object.
    created_at = datetime.strptime(version['createTime'], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

    return KeyMetadata(
        # The key's full resource name is used as its unique identifier.
        # Format: projects/.../locations/.../keyRings/.../cryptoKeys/...
        key_id=key_data['name'],
        key_arn=key_data['name'],
        cloud_provider='gcp',
        created_at=created_at,
        status='Enabled' if version.get('state') == 'ENABLED' else 'Disabled',
        # Rotation is enabled if a 'rotationPeriod' is defined for the key.
        rotation_enabled='rotationPeriod' in key_data,
        labels=key_data.get('labels', {}),
        # This information is not standard; it might exist on custom keys.
        origin=key_data.get('origin'),
        # Extract the region (location) from the key's full resource name.
        region=key_data['name'].split('/')[3],
        # Extract the version number from the version's full resource name.
        version=version['name'].split('/')[-1],
        # GCP uses 'purpose' to define the key's usage (e.g., ENCRYPT_DECRYPT).
        usage=key_data.get('purpose'),
        # The algorithm is defined in the key's version template.
        algorithm=key_data['versionTemplate'].get('algorithm'),
        protection_level=version.get('protectionLevel'),
        # GCP KMS API doesn't provide a dedicated description field for keys.
        description=None,
        # Check if the version being processed is the designated primary version for the key.
        is_primary=version.get('name') == key_data.get('primary', {}).get('name'),
    )