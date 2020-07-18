from flask import Flask, request
from flask_cors import CORS
import json
import time
import subprocess
# from opentronsA import execute

app = Flask(__name__)
CORS(app)

@app.route('/barcode', methods = ['GET'])
def barcodeReader():
  if request.method == 'GET':
    return json.dumps({'res':"123456"}) , 200, {'ContentType':'application/json'}

@app.route('/automation', methods = ['GET'])
def executeAutomation():
  if request.method == 'GET':
    import os
    subprocess.Popen('explorer')
    #res = execute()
    return json.dumps({'res': 1}), 200, {'ContentType':'application/json'}

if __name__ == '__main__':
  app.debug = True
  app.run(host='localhost', port=5001, threaded=True, use_reloader=False)