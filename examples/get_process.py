#!/usr/bin/env python

import os.path
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

KEY = 'test-key'
SECRET = 'test-secret'

flomosa.Client.debug = False

client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)

process = client.get_process('test')

print(process.to_dot())