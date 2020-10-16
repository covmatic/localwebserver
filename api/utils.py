class SingletonMeta(type):
    def __new__(meta, name, bases, classdict):
        def new(cls, *args, **kwargs):
            if cls._inst is None:
                if super(cls, cls).__new__ is object.__new__:
                    args = []
                    kwargs = {}
                cls._inst = super(cls, cls).__new__(cls, *args, **kwargs)
            return cls._inst
        
        classdict["__new__"] = classdict.get("__new__", new)
        return super(SingletonMeta, meta).__new__(meta, name, bases, classdict)
    
    def __init__(cls, name, bases, classdict):
        super(SingletonMeta, cls).__init__(name, bases, classdict)
        cls._inst = None
    
    def reset(cls, *args, **kwargs):
        del cls._inst
        cls._inst = None
        if args or kwargs:
            cls._inst = cls(*args, **kwargs)
        return cls._inst


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
