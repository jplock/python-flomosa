#!/usr/bin/env python

import os.path
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

KEY = 'test-key'
SECRET = 'test-secret'

client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)

team = flomosa.Team('Test Team', description='this is a test')
team.members = ['jplock@gmail.com']

print(team)

resp = client.add_team(team)