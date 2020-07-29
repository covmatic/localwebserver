
def remove_unused_keys(args):
    arguments = args.copy()
    empty_keys = list()
    for key, value in arguments.items():
        if value:
            pass
        else:
            empty_keys.append(key)
    for k in empty_keys:
        arguments.pop(k)
    return arguments
