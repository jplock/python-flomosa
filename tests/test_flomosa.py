#!/usr/bin/env python

import os
import sys
import unittest
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

try:
    import json
except ImportError:
    import simplejson as json

import flomosa

class TestError(unittest.TestCase):
    def setUp(self):
        self.headers = {'header1': 'test1'}
        self.code = 200
        self.message = 'Test Message'
        self.body = 'Test Body'
        self.api_error = flomosa.APIError(code=self.code, message=self.message,
            headers=self.headers)
        self.decode_error = flomosa.DecodeError(headers=self.headers,
            body=self.body)

    def test_api(self):
        try:
            raise self.api_error
        except flomosa.APIError, e:
            self.assertEqual(str(e), '%s (#%s)' % (self.message, self.code))
            self.assertEqual(unicode(e), '%s (#%s)' % (self.message, self.code))
        self.assertEqual(self.api_error['code'], self.code)
        self.assertEqual(self.api_error['header1'], self.headers['header1'])
        self.assertEqual(self.api_error['missing'], None)

    def test_decode(self):
        try:
            raise self.decode_error
        except flomosa.DecodeError, e:
            self.assertEqual(str(e), "{'header1': 'test1'} - Test Body")
            self.assertEqual(unicode(e), "{'header1': 'test1'} - Test Body")
            self.assertEqual(self.decode_error['code'], 0)
            self.assertEqual(self.decode_error['header1'],
                self.headers['header1'])
            self.assertEqual(self.decode_error['missing'], None)

class TestProcess(unittest.TestCase):
    def setUp(self):
        self.key = 'test-id'
        self.name = 'test process'
        self.description = 'test description'
        self.process = flomosa.Process(name=self.name, key=self.key,
            description=self.description)

    def test_init(self):
        self.assertEqual(self.process.name, self.name)
        self.assertEqual(self.process.description, self.description)
        self.assertEqual(self.process.key, self.key)

    def test_basic(self):
        self.assertRaises(TypeError, lambda: flomosa.Process())
        self.assertRaises(ValueError, lambda: flomosa.Process(name=None))
        self.assertRaises(ValueError, lambda: flomosa.Process(name=''))
        process2 = flomosa.Process(name=self.name, key=self.key,
            description=self.description)
        self.assertEqual(self.process, process2)

    def test_fromdict(self):
        self.assertRaises(TypeError, lambda: flomosa.Process.from_dict())
        self.assertEqual(flomosa.Process.from_dict(None), None)
        self.assertEqual(flomosa.Process.from_dict(data=[]), None)
        self.assertEqual(flomosa.Process.from_dict(data={}), None)
        data = {'name': self.name, 'description': self.description,
            'key': self.key}
        self.assertEqual(flomosa.Process.from_dict(data), self.process)
        data = {'description': self.description}
        self.assertRaises(ValueError, lambda: flomosa.Process.from_dict(data))

    def test_todict(self):
        data = self.process.to_dict()
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('id', None), self.key)

    def test_tojson(self):
        data = json.loads(self.process.to_json())
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('id', None), self.key)
        process_str = '{"kind": "Process", "description": "test description",' \
            ' "actions": [], "steps": [], "id": "test-id", "name": ' \
            '"test process"}'
        self.assertEqual(unicode(self.process), unicode(process_str))
        self.assertEqual(str(self.process), str(process_str))

    def test_addstep(self):
        step = flomosa.Step(process=self.process, name='test step',
            key='test-step-id')
        step2 = self.process.add_step(name='test step', key='test-step-id')
        self.assertEqual(len(self.process._steps), 1)
        self.assertEqual(step, step2)
        step3 = self.process.add_step(name='test step', key='test-step-id3')
        self.assertEqual(len(self.process._steps), 2)

class TestTeam(unittest.TestCase):
    def setUp(self):
        self.key = 'test-id'
        self.name = 'test team'
        self.description = 'test description'
        self.members = ['test member']
        self.team = flomosa.Team(name=self.name, description=self.description,
            members=self.members, key=self.key)

    def test_init(self):
        self.assertEqual(self.team.name, self.name)
        self.assertEqual(self.team.description, self.description)
        self.assertEqual(self.team.key, self.key)
        self.assertEqual(self.team.members, self.members)

    def test_basic(self):
        self.assertRaises(TypeError, lambda: flomosa.Team())
        self.assertRaises(ValueError, lambda: flomosa.Team(name=None))
        self.assertRaises(ValueError, lambda: flomosa.Team(name=''))
        team2 = flomosa.Team(name=self.name, key=self.key,
            description=self.description)
        self.assertEqual(self.team, team2)

    def test_fromdict(self):
        self.assertRaises(TypeError, lambda: flomosa.Team.from_dict())
        self.assertEqual(flomosa.Team.from_dict(None), None)
        self.assertEqual(flomosa.Team.from_dict(data=[]), None)
        self.assertEqual(flomosa.Team.from_dict(data={}), None)
        data = {'name': 'test team', 'description': 'test description',
            'members': ['test member'], 'key': 'test-id'}
        self.assertEqual(flomosa.Team.from_dict(data), self.team)
        data = {'description': self.description}
        self.assertRaises(ValueError, lambda: flomosa.Team.from_dict(data))

    def test_todict(self):
        data = self.team.to_dict()
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('key', None), self.key)
        self.assertEqual(data.get('members', None), self.members)

    def test_tojson(self):
        data = json.loads(self.team.to_json())
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('key', None), self.key)

class TestStep(unittest.TestCase):
    def setUp(self):
        self.key = 'test-id'
        self.process = flomosa.Process(name='test process',
            key='test-process-id')
        self.name = 'test step'
        self.description = 'test description'
        self.teams = [flomosa.Team(key='test-team-id', name='test team')]
        self.step = flomosa.Step(process=self.process, name=self.name,
            description=self.description, teams=self.teams, key=self.key)

    def test_init(self):
        self.assertEqual(self.step.name, self.name)
        self.assertEqual(self.step.process, self.process)
        self.assertEqual(self.step.description, self.description)
        self.assertEqual(self.step.key, self.key)

    def test_basic(self):
        self.assertRaises(TypeError, lambda: flomosa.Team())
        self.assertRaises(ValueError, lambda: flomosa.Team(name=None))
        self.assertRaises(ValueError, lambda: flomosa.Team(name=''))
        step2 = flomosa.Step(process=self.process, name=self.name, key=self.key,
            description=self.description)
        self.assertEqual(self.step, step2)

    def test_fromdict(self):
        self.assertRaises(TypeError, lambda: flomosa.Step.from_dict())
        self.assertEqual(flomosa.Step.from_dict(None), None)
        self.assertEqual(flomosa.Step.from_dict(data=[]), None)
        self.assertEqual(flomosa.Step.from_dict(data={}), None)
        data = {'name': self.name, 'process': self.process,
            'description': self.description, 'key': self.key}
        self.assertEqual(flomosa.Step.from_dict(data), self.step)
        data = {'description': self.description}
        self.assertRaises(ValueError, lambda: flomosa.Step.from_dict(data))

    def test_todict(self):
        data = self.step.to_dict()
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('key', None), self.key)

    def test_tojson(self):
        data = json.loads(self.step.to_json())
        self.assertEqual(data.get('name', None), self.name)
        self.assertEqual(data.get('description', None), self.description)
        self.assertEqual(data.get('key', None), self.key)

    def test_addaction(self):
        action = flomosa.Action(process=self.process, name='test action',
            key='test-action-id')
        action.add_incoming_step(self.step)
        action2 = self.step.add_action(name='test action', key='test-action-id')
        self.assertEqual(action, action2)
        self.assertEqual(len(self.process._actions), 1)
        action3 = self.step.add_action(name='test action', key='test-action-id3')
        self.assertEqual(len(self.process._actions), 2)

class TestAction(unittest.TestCase):
    def setUp(self):
        self.key = 'test-id'
        self.process = flomosa.Process(name='test process',
            key='test-process-id')
        self.name = 'test step'
        self.is_complete = False
        self.action = flomosa.Action(process=self.process, name=self.name,
            is_complete=self.is_complete, key=self.key)

    def test_init(self):
        self.assertEqual(self.action.name, self.name)
        self.assertEqual(self.action.key, self.key)
        self.assertEqual(self.action.process, self.process)
        self.assertEqual(self.action.is_complete, self.is_complete)

    def test_basic(self):
        self.assertRaises(TypeError, lambda: flomosa.Action())
        self.assertRaises(ValueError, lambda: flomosa.Action(name=None,
            process=None))
        self.assertRaises(ValueError, lambda: flomosa.Action(name=None,
            process=self.process))
        self.assertRaises(ValueError, lambda: flomosa.Action(name=self.name,
            process=None))
        action2 = flomosa.Action(process=self.process, name=self.name, key=self.key,
            is_complete=self.is_complete)
        self.assertEqual(self.action, action2)

    def test_fromdict(self):
        self.assertRaises(TypeError, lambda: flomosa.Action.from_dict())
        self.assertEqual(flomosa.Action.from_dict(None), None)
        self.assertEqual(flomosa.Action.from_dict(data=[]), None)
        self.assertEqual(flomosa.Action.from_dict(data={}), None)
        data = {'name': self.name, 'process': self.process,
            'is_complete': self.is_complete, 'key': self.key}
        self.assertEqual(flomosa.Action.from_dict(data), self.action)
        data = {'is_complete': self.is_complete}
        self.assertRaises(ValueError, lambda: flomosa.Action.from_dict(data))

if __name__ == '__main__':
    unittest.main()
