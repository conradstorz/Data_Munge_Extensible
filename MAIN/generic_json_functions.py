import json

# Custom function to serialize unserializable objects
def custom_json_serializer(obj):
    """
    Convert non-serializable objects to strings during JSON serialization.
    """
    # List of common serializable types
    if isinstance(obj, (int, float, str, bool, list, tuple, dict, type(None))):
        return obj
    else:
        return str(obj)  # Convert unserializable objects to string


def prettify_json(json_data):
    """
    Pretty print and return the JSON data with indentation.

    Args:
        json_data (dict): The JSON data to pretty print.

    Returns:
        str: The pretty printed JSON string.
    """
    prty = json.dumps(json_data, default=custom_json_serializer, indent=4)
    return prty


# Example usage
if __name__ == '__main__':
    data = {
        "file_name": "report_2000652216_20240918.pdf",
        "file_size": 47244,
        "compress_size": 43029,
        "modified_time": "2024-09-18T18:45:12"
    }

    print(prettify_json(data))
