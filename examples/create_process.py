#!/usr/bin/env python

import os.path
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

KEY = 'test-key'
SECRET = 'test-secret'

client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)

process = flomosa.Process('Test Process', description='this is a test',
    key='test')

resp = client.add_process(process)

team = client.get_team('test')

step1 = process.add_step('1st Approval')
step1.teams = [team]

step2 = process.add_step('2nd Approval')
step2.teams = [team]

step3 = process.add_step('3rd Approval')
step3.teams = [team]

step1.add_action('Approved', step2)
step1.add_action('Declined', step1)
step2.add_action('Approved', step3)
step2.add_action('Declined', step1)
step3.add_action('Approved', is_complete=True)
step3.add_action('Declined', step1)

print(process)

resp = client.add_process(process)