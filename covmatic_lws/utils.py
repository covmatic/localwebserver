from contextlib import contextmanager
from functools import wraps, partial
from threading import Timer


class SingletonMeta(type):    
    def __call__(cls, *args, **kwargs):
        if cls._inst is None:
            cls._inst = super(cls, cls).__new__(cls, *args, **kwargs)
            cls._inst.__init__(*args, **kwargs)
        return cls._inst
        
    def __init__(cls, name, bases, classdict):
        super(SingletonMeta, cls).__init__(name, bases, classdict)
        cls._inst = None
    
    def reset(cls, *args, **kwargs):
        del cls._inst
        cls._inst = None
        if args or kwargs:
            cls._inst = cls(*args, **kwargs)
        return cls._inst


class ClassProperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, inst, cls=None):
        return self.fget.__get__(inst, cls or type(inst))()


def classproperty(foo):
    return ClassProperty(foo if isinstance(foo, (classmethod, staticmethod)) else classmethod(foo))


@contextmanager
def acquire_lock(lock, blocking: bool = True, timeout: int = -1):
    acq = lock.acquire(blocking=blocking, timeout=timeout)
    yield acq
    if acq:
        lock.release()


def locked(lock, blocking: bool = True, timeout: int = -1):
    def _locked(foo):
        @wraps(foo)
        def _foo(*args, **kwargs):
            with acquire_lock(lock=lock, blocking=blocking, timeout=timeout) as acq:
                if acq:
                    r = foo(*args, **kwargs)
                else:
                    r = TimeoutError("lock timeout expired")
            return r
        return _foo
    return _locked


class LoopFunction:
    def __init__(self, interval, func):
        self._interval = interval
        self._func = func
        self._thread = None
    
    def stop(self):
        if self._thread is not None:
            self._thread.cancel()
    
    def start_(self):
        self._func()
        self.start()
    
    def start(self):
        self._thread = Timer(self._interval, self.start_)
        self._thread.start()


def loop(interval):
    def _looped(foo):
        return LoopFunction(interval, foo)
    return _looped


class FunctionCase(dict):
    def __init__(self, key):
        super(FunctionCase, self).__init__()
        self._key = key
    
    def case(self, key, value=None):
        if value is None:
            return partial(self.case, key)
        for k in key if isinstance(key, tuple) else (key,):
            self[k] = value
        return value
        
    def __call__(self, *args, **kwargs):
        try:
            return self[self._key](*args, **kwargs)
        except KeyError:
            raise NotImplementedError("No function implemented for case '{}'. Supported cases are: {}".format(self._key, ", ".join(map("'{}'".format, self.keys()))))    


class FunctionCaseStartWith(FunctionCase):
    def __getitem__(self, item: str):
        try:
            for k in self.keys():
                if item.startswith(k):
                    return super(FunctionCaseStartWith, self).__getitem__(k)
        except AttributeError:
            pass
        return super(FunctionCaseStartWith, self).__getitem__(item)


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
