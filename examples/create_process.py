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

process = flomosa.Process('Test Process', description='this is a test',
    collect_stats=True, key='test')

resp = client.add_process(process)

team = client.get_team('test')

step1 = process.add_step('1st Approval')
step1.team = team

step2 = process.add_step('2nd Approval')
step2.members = ['jplock@gmail.com']

step3 = process.add_step('3rd Approval')
step3.team = team
step3.members = ['jplock@gmail.com']

step1.add_action('Approved', step2)
step1.add_action('Declined', step1)
step1.add_action('Close', is_complete=True)
step2.add_action('Approved', step3)
step2.add_action('Declined', step1)
step3.add_action('Approved', is_complete=True)
step3.add_action('Declined', step1)

print(process)

resp = client.add_process(process)