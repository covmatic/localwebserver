import threading
import tkinter as tk
import tkinter.messagebox
from functools import wraps


def warningbox(foo):
    @wraps(foo)
    def foo_(*args, **kwargs):
        try:
            return foo(*args, **kwargs)
        except Exception as e:
            tk.messagebox.showwarning(type(e).__name__, str(e))
    return foo_


def setIntervalForTimerButton(function):
    '''
    This decorator starts a thread with the decorated function as loop;
    The first argument of the function must contain the _interval property.
    Args:
        function: the decorated function

    Returns:

    '''
    def wrapper(*args, **kwargs):
        stopped = threading.Event()
        interval = args[0]._interval

        def _loop(): # executed in another thread
            while not stopped.wait(interval): # until stopped
                function(*args, **kwargs)

        t = threading.Thread(target=_loop)
        t.daemon = True # stop if the program exits
        t.start()
        return stopped
    return wrapper

# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
