"""
The MIT License

Copyright (c) 2010 Flomosa, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

import uuid
import urllib
import time
import oauth2 as oauth
from httplib2 import Http
from urlparse import urljoin

try:
    import json
except ImportError:
    import simplejson as json

API_VERSION = '0.1'

_PROCESSES = {}
_TEAMS = {}

def generate_key():
    """Generate a unique UUID"""
    return str(uuid.uuid4())


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(self, code, message, headers):
        self._code = code
        self._message = message
        self._headers = headers
        Exception.__init__(self, message)

    def __getitem__(self, key):
        if key == 'code':
            return self._code

        try:
            return self._headers[key]
        except KeyError:
            return None

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '%s (#%s)' % (self._message, self._code)


class DecodeError(APIError):
    """There was a problem decoding the API's JSON response."""

    def __init__(self, headers, body):
        APIError.__init__(self, 0, 'Could not decode JSON.', headers)
        self._body = body

    def __unicode__(self):
        return '%s - %s' % (self._headers, self._body)


class Process(object):
    """Flomosa Process object"""

    def __init__(self, name, description=None, collect_stats=False, key=None):
        self.key = key or generate_key()
        self.name = name
        self.description = description
        self.collect_stats = collect_stats
        self._steps = {}
        self._actions = {}

        if not self.name or not self.key:
            raise ValueError('Name and Key must be set.')

        _PROCESSES[self.key] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    @classmethod
    def from_dict(cls, data):
        """Return a new Process instance from a dict object."""
        if not data or not isinstance(data, dict):
            return None

        name = data.get('name', None)
        description = data.get('description', None)
        process_key = data.get('key', None)
        collect_stats = data.get('collect_stats', False)

        process = cls(name=name,
            description=description,
            collect_stats=collect_stats,
            key=process_key)
        for step_data in data.get('steps', []):
            step = Step.from_dict(step_data)
            process._steps[step.key] = step
        for action_data in data.get('actions', []):
            action = Action.from_dict(action_data)
            process._actions[action.key] = action

        return process

    def to_dict(self):
        """Return process as a dict object."""
        return {
            'kind': 'Process',
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'collect_stats': self.collect_stats,
            'steps': [step.to_dict() for step in self._steps.itervalues()],
            'actions': [action.to_dict() for action in
                self._actions.itervalues()]
        }

    def to_json(self):
        """Return process as a JSON string."""
        return json.dumps(self.to_dict())

    def to_dot(self):
        """Return process as a Dot graph string."""
        nodes = ''
        for step_key, step in self._steps.iteritems():
            nodes += '"%s" [label="%s"]\n' % (step_key, step.name)
        nodes += '"finish" [label="Finish"]\n'

        actions = ''
        for action_key, action in self._actions.iteritems():
            for incoming_key, incoming in action._incoming.iteritems():
                if action.is_complete:
                    actions += '"%s" -> "finish" [label="%s"]\n' % \
                        (incoming_key, action.name)
                else:
                    for outgoing_key, outgoing in action._outgoing.iteritems():
                        actions += '"%s" -> "%s" [label="%s"]\n' % \
                            (incoming_key, outgoing_key, action.name)

        return 'digraph "%s" {\n%s\n%s}' % (self.name, nodes, actions)

    def add_step(self, name, team=None, members=None, is_start=False, key=None):
        """Add a step to this process."""
        if not self._steps:
            is_start = True
        step = Step(self, name, is_start=is_start, team=team, members=members,
            key=key)
        self._steps[step.key] = step
        return step

    def get_steps_by_name(self, name):
        """Return the steps matching a given name."""
        steps = []
        for step in self._steps.values():
            if isinstance(step, Step) and step.name == name:
                steps.append(step)
        if len(steps) == 1:
            return steps[0]
        return steps

    def delete_steps_by_name(self, name):
        """Delete all steps matching the given name."""
        for step in self.get_steps_by_name(name):
            try:
                del self._steps[step.key]
                del step
            except:
                pass


class Team(object):
    """Flomosa Team object"""

    def __init__(self, name, description=None, members=None, key=None):
        self.key = key or generate_key()
        self.name = name
        self.description = description
        self.members = members or []

        if not self.name or not self.key:
            raise ValueError('Name and Key must be set.')

        _TEAMS[self.key] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    @classmethod
    def from_dict(cls, data):
        """Return a new Team instance from a dict object."""
        if not data or not isinstance(data, dict):
            return None

        name = data.get('name', None)
        description = data.get('description', None)
        members = data.get('members', [])
        team_key = data.get('key', None)

        team = cls(name=name, description=description, members=members,
            key=team_key)
        return team

    def to_dict(self):
        """Return team as a dict object."""
        return {
            'kind': 'Team',
            'key': self.key,
            'name': self.name,
            'description': self.description,
            'members': self.members
        }

    def to_json(self):
        """Return team as a JSON string."""
        return json.dumps(self.to_dict())


class Step(object):
    """Flomosa Step object"""

    def __init__(self, process, name, description=None, is_start=False,
        team=None, members=None, key=None):
        self.key = key or generate_key()
        self.process = process
        self.name = name
        self.description = description
        self.is_start = bool(is_start)
        self.members = members or []
        self.team = team

        if not self.process or not self.name or not self.key:
            raise ValueError('Process, Name and Key must be set.')
        elif not isinstance(self.process, Process):
            raise ValueError('Process must be a valid Process instance.')
        else:
            self.process._steps[self.key] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    @classmethod
    def from_dict(cls, data):
        """Return a new Step instance from a dict object."""
        if not data or not isinstance(data, dict):
            return None

        key = data.get('key', None)
        process_key = data.get('process', None)
        name = data.get('name', None)
        description = data.get('description', None)
        is_start = data.get('is_start', None)
        members = data.get('members', [])
        team = data.get('team', None)

        process = _PROCESSES.get(process_key, None)
        if not process:
            raise ValueError('Process "%s" not found.' % process_key)

        step = cls(process=process, name=name, description=description,
            is_start=is_start, team=team, members=members, key=key)
        return step

    def to_dict(self):
        """Return step as a dict object."""
        data = {
            'kind': 'Step',
            'key': self.key,
            'process': self.process.key,
            'name': self.name,
            'description': self.description,
            'is_start': bool(self.is_start),
            'members': self.members
        }
        if isinstance(self.team, Team):
            data['team'] = self.team.key
        else:
            data['team'] = self.team
        return data

    def to_json(self):
        """Return step as a JSON string."""
        return json.dumps(self.to_dict())

    def add_action(self, name, next_step=None, is_complete=False, key=None):
        """Add an action after this step."""
        action = Action(self.process, name, is_complete=is_complete, key=key)
        action.add_incoming_step(self)
        if next_step and isinstance(next_step, Step):
            action.add_outgoing_step(next_step)
        return action

    def get_actions_by_name(self, name=None):
        """Return a list object of any actions following this step."""
        step_actions = []
        for action in self.process._actions.itervalues():
            if name is not None and action.name != name:
                continue
            for step in action._incoming.itervalues():
                if step == self:
                    step_actions.append(action)
        return step_actions

    def delete_actions_by_name(self, name):
        """Delete all actions matching a given name from this step."""
        for action in self.get_actions_by_name(name):
            del self.process._actions[action.key]
            del action

    def update_action(self, old_name, new_name, next_step=None,
        is_complete=None):
        """Update an existing action after this step."""
        for action in self.get_actions_by_name(old_name):
            action.name = new_name
            if is_complete is not None:
                action.is_complete = bool(is_complete)
            if next_step and isinstance(next_step, Step):
                action.add_outgoing_step(next_step)


class Action(object):
    """Flomosa Action object"""

    def __init__(self, process, name, is_complete=False, key=None):
        self.key = key or generate_key()
        self.process = process
        self.name = name
        self.is_complete = bool(is_complete)
        self._incoming = {}
        self._outgoing = {}

        if not self.process or not self.name or not self.key:
            raise ValueError('Process, Name and Key must be set.')
        elif not isinstance(self.process, Process):
            raise ValueError('Must be a valid Process instance.')
        else:
            self.process._actions[self.key] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.key == other.key

    @classmethod
    def from_dict(cls, data):
        """Return a new Action instance from a dict object."""
        if not data or not isinstance(data, dict):
            return None

        process_key = data.get('process', None)
        name = data.get('name', None)
        is_complete = data.get('is_complete', None)
        key = data.get('key', None)

        process = _PROCESSES.get(process_key, None)
        if not process:
            raise ValueError('Process "%s" not found.' % process_key)

        action = cls(process=process, name=name, is_complete=is_complete,
            key=key)
        for step_key in data.get('incoming', []):
            step = process._steps.get(step_key, None)
            action.add_incoming_step(step)
        for step_key in data.get('outgoing', []):
            step = process._steps.get(step_key, None)
            action.add_outgoing_step(step)

        return action

    def add_incoming_step(self, step):
        """Add an incoming Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self._incoming[step.key] = step

    def add_outgoing_step(self, step):
        """Add an outgoing Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self.is_complete = False
        self._outgoing[step.key] = step

    def to_dict(self):
        """Return action as a dict object."""
        return {
            'kind': 'Action',
            'key': self.key,
            'process': self.process.key,
            'name': self.name,
            'is_complete': bool(self.is_complete),
            'incoming': [step_key for step_key in self._incoming.iterkeys()],
            'outgoing': [step_key for step_key in self._outgoing.iterkeys()]
        }

    def to_json(self):
        """Return action as a JSON string."""
        return json.dumps(self.to_dict())


class Client(object):
    realm = 'http://flomosa.appspot.com'
    debug = True
    endpoints = {
        'processes': 'processes/%(key)s.json',
        'process_search': 'search/process/%(key)s.json',
        'teams': 'teams/%(key)s.json',
        'requests': 'requests/%(key)s.json',
        'step_search': 'search/step/%(key)s.json',
        'stats_year': 'stats/by-year/%(key)s.json',
        'stats_month': 'stats/by-month/%(key)s.json',
        'stats_week': 'stats/by-week/%(key)s.json',
        'stats_day': 'stats/by-day/%(key)s.json'
    }
    stats = (
        'num_requests',
        'num_requests_completed',
        'min_request_seconds',
        'max_request_seconds',
        'avg_request_seconds',
        'total_request_seconds'
    )

    def __init__(self, key, secret, api_version=API_VERSION,
        host='flomosa.appspot.com', port=80):
        self.host = host
        self.port = port
        self.consumer = oauth.Consumer(key, secret)
        self.key = key
        self.secret = secret
        self.api_version = api_version
        self.signature = oauth.SignatureMethod_HMAC_SHA1()
        if port == 443:
            self.uri = 'https://%s' % host
        else:
            self.uri = 'http://%s:%s' % (host, port)
        self.http = Http()

    def __unicode__(self):
        return '%s (%s, %s)' % (self.uri, self.secret, self.key)

    def __str__(self):
        return self.__unicode__()

    def endpoint(self, name, **kwargs):
        try:
            endpoint = self.endpoints[name]
        except KeyError:
            raise Exception('No endpoint named "%s"' % name)
        try:
            endpoint = endpoint % kwargs
        except KeyError, e:
            raise TypeError('Missing required argument "%s"' % (e.args[0],))
        return urljoin(urljoin(self.uri, '/'), endpoint)

    def filter(self, filter):
        """Filter statistics returned."""
        if filter:
            if filter in self.stats:
                return filter
            elif isinstance(filter, list):
                new_filter = []
                for key in filter:
                    if key in self.stats:
                        new_filter.append(key)
                if new_filter:
                    return ','.join(new_filter)
        return None

    def add_process(self, process):
        endpoint = self.endpoint('processes', key=process.key)
        return self._request(endpoint, 'PUT', process.to_json())

    def get_process(self, key):
        endpoint = self.endpoint('processes', key=key)
        return Process.from_dict(self._request(endpoint, 'GET'))

    def get_request(self, key):
        endpoint = self.endpoint('requests', key=key)
        return self._request(endpoint, 'GET')

    def delete_process(self, key):
        endpoint = self.endpoint('processes', key=key)
        return self._request(endpoint, 'DELETE')

    def add_team(self, team):
        endpoint = self.endpoint('teams', key=team.key)
        return self._request(endpoint, 'PUT', team.to_json())

    def get_team(self, key):
        endpoint = self.endpoint('teams', key=key)
        return Team.from_dict(self._request(endpoint, 'GET'))

    def delete_team(self, key):
        endpoint = self.endpoint('teams', key=key)
        return self._request(endpoint, 'DELETE')

    def get_year_stats(self, key, year, filter=None):
        data = {
            'year': year
        }
        if filter is not None:
            data['filter'] = self.filter(filter)
        endpoint = self.endpoint('stats_year', key=key)
        return self._request(endpoint, 'GET', data)

    def get_month_stats(self, key, year, month, filter=None):
        data = {
            'year': year,
            'month': month
        }
        if filter is not None:
            data['filter'] = self.filter(filter)
        endpoint = self.endpoint('stats_month', key=key)
        return self._request(endpoint, 'GET', data)

    def get_week_stats(self, key, year, week_num, filter=None):
        data = {
            'year': year,
            'week_num': week_num,
        }
        if filter is not None:
            data['filter'] = self.filter(filter)
        endpoint = self.endpoint('stats_week', key=key)
        return self._request(endpoint, 'GET', data)

    def get_day_stats(self, key, year, month, day, filter=None):
        data = {
            'year': year,
            'month': month,
            'day': day
        }
        if filter is not None:
            data['filter'] = self.filter(filter)
        endpoint = self.endpoint('stats_day', key=key)
        return self._request(endpoint, 'GET', data)

    def search_process(self, key, start=None, end=None, limit=None):
        data = {}
        if start is not None:
            data['start'] = start
            if end is None:
                data['end'] = time.time()
            else:
                data['end'] = end
        if limit is None:
            data['limit'] = limit
        else:
            data['limit'] = 25
        endpoint = self.endpoint('process_search', key=key)
        return self._request(endpoint, 'GET', data)

    def search_step(self, key, start=None, end=None, limit=None):
        data = {}
        if start is not None:
            data['start'] = start
            if end is None:
                data['end'] = time.time()
            else:
                data['end'] = end
        if limit is None:
            data['limit'] = limit
        else:
            data['limit'] = 25
        endpoint = self.endpoint('step_search', key=key)
        return self._request(endpoint, 'GET', data)

    def _request(self, endpoint, method, data=None):
        body = None
        params = {}
        if method == 'GET' and isinstance(data, dict):
            params = data
            endpoint = endpoint + '?' + urllib.urlencode(data)
        else:
            if isinstance(data, dict):
                body = urllib.urlencode(data)
            else:
                body = data

        request = oauth.Request.from_consumer_and_token(self.consumer,
            http_method=method, http_url=endpoint, parameters=params)

        request.sign_request(self.signature, self.consumer, None)
        headers = request.to_header(self.realm)
        headers['User-Agent'] = 'Flomosa Python Client v%s' % API_VERSION

        resp, content = self.http.request(endpoint, method, body=body,
            headers=headers)

        if self.debug:
            print(headers)
            print('-------------')
            print(resp)
            print('-------------')
            print(content)

        if content: # Empty body is allowed.
            try:
                content = json.loads(content)
            except ValueError:
                raise DecodeError(resp, content)

        if resp['status'][0] != '2':
            code = resp['status']
            message = content
            if isinstance(content, dict):
                code = content['code']
                message = content['message']
            raise APIError(code, message, resp)

        return content
