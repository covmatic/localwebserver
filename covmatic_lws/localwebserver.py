"""LocalWeb Server"""
from .api import LocalWebServerAPI
from .args import Args
from flask import Flask, request
from flask_cors import CORS


class LocalWebServerAPP(Flask):
    def __init__(self, name=__name__, *args, **kwargs):
        super(LocalWebServerAPP, self).__init__(name, *args, **kwargs)
        self.secret_key = b'_5#y2L"s8zxec]/'
        self.config.from_object(Args().__dict__)
        
        CORS(self)
        LocalWebServerAPI().init_app(self)


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


def main():
    app = LocalWebServerAPP()
    
    @app.route('/shutdown', methods=['GET'])
    def shutdown():
        shutdown_server()
        return 'Server shutting down...'
    
    app.run(host='::', port=5001, debug=False)
    

if __name__ == "__main__":
    main()


# Copyright (c) 2020 Covmatic.
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
