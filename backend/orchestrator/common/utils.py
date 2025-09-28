"""A place for shared, common utility functions."""

from services.converters import from_aws_key, from_azure_key, from_gcp_key

def get_converter(cloud_provider: str):
    """
    Selects the correct data converter function based on the provider name.
    """
    converters = {
        "aws": from_aws_key,
        "azure": from_azure_key,
        "gcp": from_gcp_key
    }
    return converters.get(cloud_provider)