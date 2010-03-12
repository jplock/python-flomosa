#!/usr/bin/env python

import os
import sys
import unittest
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

try:
    import simplejson as json
except ImportError:
    import json

import flomosa

class TestClient(unittest.TestCase):
    def setUp(self):
        self.key = 'test-key'
        self.secret = 'test-secret'
        self.host = '127.0.0.1'
        self.port = 8080
        self.client = flomosa.Client(key=self.key, secret=self.secret,
            host=self.host, port=self.port)
        self.client.debug = False

    def create_process(self):
        name = 'test process'
        description = 'test description'
        process = flomosa.Process(name=name, description=description)
        return process

    def create_team(self):
        name = 'test team'
        description = 'test description'
        members = ['test@flomosa.com']
        team = flomosa.Team(name=name, description=description, members=members)
        return team

    def test_init(self):
        self.assertEqual(self.client.key, self.key)
        self.assertEqual(self.client.secret, self.secret)
        self.assertEqual(self.client.host, self.host)
        self.assertEqual(self.client.port, self.port)
        self.assertEqual(self.client.uri, 'http://%s:%s' % (self.host,
            self.port))
        self.client = flomosa.Client(key=self.key, secret=self.secret,
            host=self.host, port=443)
        self.assertEqual(self.client.uri, 'https://%s' % self.host)

    def test_endpoint(self):
        self.assertRaises(Exception, lambda: self.client.endpoint('test'))
        self.assertRaises(TypeError, lambda: self.client.endpoint('processes'))

    def test_serialworkflow(self):
        process = self.create_process()
        team = self.create_team()

        resp = self.client.add_process(process)
        self.assertEqual(process.key, resp['key'])

        resp = self.client.add_team(team)
        self.assertEqual(team.key, resp['key'])

        self.assertRaises(flomosa.APIError,
            lambda: self.client.get_process(process.key))

        step1 = process.add_step('1st Approval')
        step1.teams = [team]
        step2 = process.add_step('2nd Approval')
        step2.teams = [team]

        self.assertRaises(flomosa.APIError,
            lambda: self.client.get_process(process.key))

        team2 = self.client.get_team(team.key)
        self.assertEqual(team, team2)

        resp = self.client.delete_process(process.key)
        self.assertEqual(resp, '')

        resp = self.client.delete_team(team.key)
        self.assertEqual(resp, '')

if __name__ == '__main__':
    unittest.main()
