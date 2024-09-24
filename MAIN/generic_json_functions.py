import json


# Custom function to serialize the dictionary excluding unserializable objects
def custom_json_serializer(obj):
    # usage example: pretty_dict = json.dumps(dict, default=custom_json_serializer, indent=4)
    if isinstance(obj, (int, float, str, bool, list, tuple, dict, type(None))):
        return obj
    else:
        return str(obj)
    

def prettify_json(json_data):
    return json.dumps(json_data, default=custom_json_serializer, indent=4)