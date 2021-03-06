#!/usr/bin/env python

import os
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

# test@flomosa.com
KEY = '4ef3e685-37c1-43f9-ae03-0a21523051c6'
SECRET = '1913b245-18ae-4caa-a491-cedd2e471a50'

if os.environ['HOST'] == 'philjr.local':
    client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)
    client.debug = True
else:
    client = flomosa.Client(KEY, SECRET)

resp = client.delete_process('test')