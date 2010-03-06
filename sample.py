#!/usr/bin/env python

import flomosa

process = flomosa.Process('Test Process')

team = flomosa.Team('Flomosa Test Team', members=['jplock@gmail.com'])

step1 = process.add_step('1st Approval', teams=[team])
step2 = process.add_step('2nd Approval', teams=[team])
step3 = process.add_step('3rd Approval', teams=[team])

step1.add_action('Approve', step2)
step1.add_action('Decline', step1)

step2.add_action('Approve', step3)
step2.add_action('Decline', step1)

step3.add_action('Approve', is_complete=True)
step3.add_action('Decline', step1)

#print(process)

client = flomosa.Client('test_key', 'test_secret')

print(process)

try:
    client.add_process(process)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print('---------------------------')

process.name = 'Updated Process'
process.description = 'Here is a test description'

try:
    client.update_process(process)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print('---------------------------')

try:
    process2 = client.get_process(process.id)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print(process2)

if process != process2:
    print("process IS NOT EQUAL TO process2")
else:
    print("process IS EQUAL TO process2")

print('---------------------------')

try:
    client.delete_process(process.id)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)