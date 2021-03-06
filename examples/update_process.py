#!/usr/bin/env python

import os.path
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

from pprint import pprint

import flomosa

KEY = 'test-key'
SECRET = 'test-secret'

flomosa.Client.debug = False

client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)

team = client.get_team('test')

process = client.get_process('test')

#pprint(process.to_dict())
print(process.to_dot())

print('###########################')

#step2 = process.get_steps_by_name('2nd Approval'):
#step2.delete_actions_by_name('Send to Bob')

#step4 = process.get_steps_by_name('Bob Approval'):
#step4.delete_actions_by_name('F it')
#step2.update_action('Approved', '2nd Approved is Approved')

#step4 = process.add_step('Bob Approval')
#step4.teams = [team]

#step2.add_action('Send to Bob', next_step=step4)

#step4.add_action('This sucks', next_step=step1)
#step4.add_action('F it', next_step=step3)

#process.delete_steps_by_name('Bob Approval')
#del step4

#print(process.to_dot())
#pprint(process.to_dict())

print('###########################')

#resp = client.add_process(process)

process = client.get_process('test')

print(process.to_dot())
#pprint(process.to_dict())
