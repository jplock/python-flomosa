#!/usr/bin/env python

import flomosa

team = flomosa.Team('Flomosa Test Team', members=['jplock@gmail.com'])

client = flomosa.Client('test_key', 'test_secret', host='127.0.0.1', port=8080)

print(team)

try:
    client.add_team(team)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print('---------------------------')

team.name = 'Updated Team Name'
team.description = 'Here is a test description'
team.members = ['jplock@gmail.com','wdthem@gmail.com']

try:
    client.update_team(team)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print('---------------------------')

try:
    team2 = client.get_team(team.id)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)

print(team)
print(team2)

if team == team2:
    print("team IS EQUAL TO team2")
else:
    print("team IS NOT EQUAL TO team2")

print('---------------------------')

try:
    client.delete_team(team.id)
except flomosa.APIError, e:
    print(e)
except flomosa.DecodeError, e:
    print(e)