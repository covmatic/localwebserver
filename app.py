# from datetime import datetime
# from scp import SCPClient
# import tkinter as tk
# import tkinter.filedialog
# from tkinter import simpledialog
# from tkinter import messagebox
from api import api
from database import init_db
from flask import Flask, app, request
from flask_cors import CORS
from services import task_runner, protocol_gen
# from services.task_runner import OT2_SSH_KEY, OT2_ROBOT_PASSWORD, OT2_REMOTE_LOG_FILEPATH
from views import bp_automation
# import time
# import subprocess


def create_app():
    app = Flask(__name__)
    app.secret_key = b'_5#y2L"s8zxec]/'
    app.config.from_object('config')

    # Init all plugins
    CORS(app)
    init_db(app)
    api.init_app(app)

    # Register all views blueprints
    app.register_blueprint(bp_automation)
    return app


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


if __name__ == "__main__":
    local_app = create_app()

    @local_app.route('/shutdown', methods=['GET'])
    def shutdown():
        shutdown_server()
        return 'Server shutting down...'
    task_runner.start_scheduler(local_app)
    local_app.run(host='127.0.0.1', port=5001, debug=False)

""" Copyright (c) 2020 Covmatic.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 and associated documentation files (the "Software"), to deal in the Software without restriction,
  including without limitation the rights to use, copy, modify, merge, publish, distribute,
   sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies
 or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
"""
