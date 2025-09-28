# Service layer for handling KeyMetadata database operations.

from extensions import db
from models import KeyMetadata, ModuleStatus
from services.logic import forward_request
from services.notification_service import send_alarm_email, raise_alarm
from common.utils import get_converter
from datetime import datetime, timezone

def upsert_key(metadata: KeyMetadata):
    """
    Inserts a new key metadata record or updates it if it already exists.
    """
    try:
        # Query for an existing key based on its unique identifiers
        existing_key = KeyMetadata.query.filter_by(
            cloud_provider=metadata.cloud_provider,
            key_id=metadata.key_id
        ).first()

        if existing_key:
            # If it exists, update its attributes from the new metadata object
            existing_key.key_arn = metadata.key_arn
            existing_key.region = metadata.region
            existing_key.created_at = metadata.created_at
            existing_key.status = metadata.status
            existing_key.rotation_enabled = metadata.rotation_enabled
            existing_key.labels = metadata.labels
            existing_key.origin = metadata.origin
            existing_key.version = metadata.version
            existing_key.usage = metadata.usage
            existing_key.algorithm = metadata.algorithm
            existing_key.protection_level = metadata.protection_level
        else:
            # If it does not exist, add the new metadata object to the session
            db.session.add(metadata)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[Error] Failed to upsert key metadata: {e}")


def update_key_status(provider: str, key_id: str, is_enabled: bool):
    """Updates the status of an existing key in the database."""
    key = KeyMetadata.query.filter_by(cloud_provider=provider, key_id=key_id).first()
    if key:
        try:
            key.status = "Enabled" if is_enabled else "Disabled"
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Error] Failed to update key status: {e}")


def update_key_rotation(provider: str, key_id: str, rotation_enabled: bool):
    """Updates the rotation status of an existing key in the database."""
    key = KeyMetadata.query.filter_by(cloud_provider=provider, key_id=key_id).first()
    if key:
        try:
            key.rotation_enabled = rotation_enabled
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Error] Failed to update key rotation: {e}")


def delete_key_metadata(provider: str, key_id: str):
    """Deletes a key's metadata from the local database."""
    key = KeyMetadata.query.filter_by(cloud_provider=provider, key_id=key_id).first()
    if key:
        try:
            db.session.delete(key)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[Error] Failed to delete key metadata: {e}")

def list_local_keys(filters=None):
    """
    Queries the database for KeyMetadata records, applying optional filters.

    Args:
        filters (dict, optional): A dictionary of filter criteria.
                                  e.g., {"cloud_provider": "aws", "status": "Enabled"}

    Returns:
        list: A list of KeyMetadata objects.
    """
    query = KeyMetadata.query

    if filters:
        # Create a dictionary of filters, excluding any None values
        valid_filters = {k: v for k, v in filters.items() if v is not None}
        if valid_filters:
            query = query.filter_by(**valid_filters)

    return query.order_by(KeyMetadata.cloud_provider, KeyMetadata.id).all()

def synchronize_provider_keys(provider: str):
    """
    Fetches keys from a cloud provider, reconciles with the database,
    and correctly handles the lifecycle of keys pending deletion.
    """
    # Step 1: Get the "ground truth" by fetching all keys from the cloud provider.
    cloud_data, status_code = forward_request("list-keys", {"cloud_provider": provider}, method="GET")
    if status_code >= 400:
        raise RuntimeError(f"Failed to fetch keys from {provider}: {cloud_data.get('error', 'Unknown error')}")

    # Step 2: Get the current state from our local database for comparison.
    # We now fetch all keys that are not yet in the final "Deleted" state.
    db_keys = KeyMetadata.query.filter(
        KeyMetadata.cloud_provider == provider,
        KeyMetadata.status != "Deleted"
    ).all()
    db_keys_map = {key.key_arn: key for key in db_keys}

    summary = {"added": 0, "updated": 0, "finalized": 0, "removed": 0}
    seen_cloud_arns = set()
    converter = get_converter(provider)
    if not converter:
        raise RuntimeError(f"No converter found for provider {provider}")

    # Step 3: Loop through every key from the cloud to find adds and updates.
    # This logic remains the same as your original function.
    for key_data in cloud_data.get("keys", []):
        try:
            cloud_key_obj = converter(key_data)
            seen_cloud_arns.add(cloud_key_obj.key_arn)

            if cloud_key_obj.key_arn in db_keys_map:
                db_key = db_keys_map[cloud_key_obj.key_arn]
                
                if (db_key.status != cloud_key_obj.status or 
                    db_key.rotation_enabled != cloud_key_obj.rotation_enabled):
                    
                    if db_key.last_update_source != 'API':
                        message = (f"Out-of-band change detected for key {db_key.key_arn}. "
                                   f"Status changed from '{db_key.status}' to '{cloud_key_obj.status}'.")
                        raise_alarm("HIGH", "OUT_OF_BAND_CHANGE", message)
                    
                    db_key.status = cloud_key_obj.status
                    db_key.rotation_enabled = cloud_key_obj.rotation_enabled
                    db_key.last_updated_by = "system_sync"
                    db_key.last_update_source = "sync"
                    summary["updated"] += 1
            else:
                message = f"Out-of-band key creation detected in {provider.upper()}: {cloud_key_obj.key_arn}."
                raise_alarm("MEDIUM", "OUT_OF_BAND_CREATION", message)

                cloud_key_obj.last_updated_by = "system_sync"
                cloud_key_obj.last_update_source = "sync"
                db.session.add(cloud_key_obj)
                summary["added"] += 1
        except Exception as e:
            print(f"[Sync Warning] Could not process key: {e}")

    # Step 4: Find keys in our DB that were NOT in the cloud, and handle them intelligently.
    db_key_arns = set(db_keys_map.keys())
    missing_key_arns = db_key_arns - seen_cloud_arns
    now = datetime.now(timezone.utc)

    for arn in missing_key_arns:
        key_to_check = db_keys_map[arn]
        
        # Case 1: The key was scheduled for deletion.
        if key_to_check.status.startswith("PendingDeletion"):
            try:
                _, deletion_dt_str = key_to_check.status.split(' ', 1)
                deletion_dt = datetime.fromisoformat(deletion_dt_str)

                # Subcase 1a: Deletion time has passed. This is an EXPECTED deletion.
                if deletion_dt <= now:
                    key_to_check.status = "Deleted"
                    summary["finalized"] += 1
                # Subcase 1b: Deletion time has NOT passed. It was deleted too early.
                else:
                    message = f"Out-of-band early deletion for key {key_to_check.key_arn}. It was not yet due for deletion."
                    raise_alarm("HIGH", "OUT_OF_BAND_DELETION", message)
                    key_to_check.status = "Deleted" # Mark as deleted since it's gone
                    summary["removed"] += 1

            except (ValueError, IndexError):
                 # Fallback for malformed status string
                 message = f"Malformed PendingDeletion status for key {key_to_check.key_arn} which is missing from cloud."
                 raise_alarm("MEDIUM", "DATA_INTEGRITY_ISSUE", message)
                 key_to_check.status = "Deleted"
                 summary["removed"] += 1

        # Case 2: The key was NOT scheduled for deletion. This is a true out-of-band deletion.
        else:
            message = f"Out-of-band key deletion detected for active key in {provider.upper()}: {key_to_check.key_arn}."
            raise_alarm("HIGH", "OUT_OF_BAND_DELETION", message)
            key_to_check.status = "Deleted"
            summary["removed"] += 1

    # Step 5: Update the 'last_synced_at' timestamp for this provider.
    module_status = ModuleStatus.query.filter_by(provider_name=provider).first()
    if module_status:
        module_status.last_synced_at = datetime.now(timezone.utc)

    db.session.commit()
    return summary