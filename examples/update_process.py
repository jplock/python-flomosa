#!/usr/bin/env python

import os.path
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

KEY = 'test-key'
SECRET = 'test-secret'

flomosa.Client.debug = False

client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)

team = client.get_team('188259da-75d3-435b-9c07-cead04066025')

process = client.get_process('127cbe46-6235-4e14-89e9-95566dccbeb5')

step1 = process.get_step_by_name('1st Approval')
step2 = process.get_step_by_name('2nd Approval')
step3 = process.get_step_by_name('3rd Approval')
step2.update_action('Approved', '2nd Approved is Approved')

step4 = process.add_step('Bob Approval')
step4.teams = [team]

step2.add_action('Send to Bob', next_step=step4)

step4.add_action('This sucks', next_step=step1)
step4.add_action('F it', next_step=step3)

print(process.to_dot())