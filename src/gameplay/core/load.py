def merge_dict(target: dict, source: dict) -> dict:
    for key, value in source.items():
        if isinstance(value, dict) and key in target and isinstance(target[key], dict):
            merge_dict(target[key], value)
        else:
            target[key] = value
    return target


# TODO: add types
# TODO: add unit tests
def loadContextFromConfig(config, context):
    if not config:
        return context
    return merge_dict(context, config)
