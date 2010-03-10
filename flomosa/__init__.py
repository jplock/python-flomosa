import uuid
import oauth2 as oauth
from httplib2 import Http
from urlparse import urljoin

try:
    import simplejson as json
except ImportError:
    import json

API_VERSION = '0.1'


def generate_id():
    """Generate a unique UUID"""
    return str(uuid.uuid4())


class APIError(Exception):
    """Base exception for all API errors."""

    def __init__(self, code, message, headers):
        self._code = code
        self._message = message
        self._headers = headers

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
    def __init__(self, name, description=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self._steps = {}
        self._actions = {}

        if not self.name or not self.id:
            raise ValueError('Name and ID must be set.')

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Process) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        name = data.get('name', None)
        description = data.get('description', None)
        id = data.get('id', None)

        process = cls(name=name, description=description, id=id)
        return process

    def to_dict(self):
        return {
            'kind': 'Process',
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'steps': [step.to_dict() for step in self._steps],
            'actions': [action.to_dict() for action in self._actions]
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def add_step(self, name, teams=None, is_start=False, id=None):
        """Add a step to this process."""
        if not self._steps:
            is_start = True
        step = Step(self, name, is_start=is_start, teams=teams, id=id)
        self._steps[step.id] = step
        return step


class Team(object):
    def __init__(self, name, description=None, members=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self.members = members or []

        if not self.name or not self.id:
            raise ValueError('Name and ID must be set.')

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Team) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        name = data.get('name', None)
        description = data.get('description', None)
        members = data.get('members', None)
        id = data.get('id', None)

        team = cls(name=name, description=description, members=members, id=id)
        return team

    def to_dict(self):
        return {
            'kind': 'Team',
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'members': self.members
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Step(object):
    def __init__(self, process, name, description=None, is_start=False,
        teams=None, id=None):
        self.id = id or generate_id()
        self.process = process
        self.name = name
        self.description = description
        self.is_start = bool(is_start)
        self.teams = teams or []

        if not self.process or not self.name or not self.id:
            raise ValueError('Process, Name and ID must be set.')
        elif not isinstance(self.process, Process):
            raise ValueError('Process must be a valid Process instance.')
        else:
            self.process._steps[self.id] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Step) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        id = data.get('id', None)
        process = data.get('process', None)
        name = data.get('name', None)
        description = data.get('description', None)
        is_start = data.get('is_start', None)
        teams = data.get('teams', None)

        step = cls(process=process, name=name, description=description,
            is_start=is_start, teams=teams, id=id)
        return step

    def to_dict(self):
        return {
            'kind': 'Step',
            'id': self.id,
            'process': self.process.id,
            'name': self.name,
            'description': self.description,
            'is_start': bool(self.is_start),
            'teams': [team.to_dict() for team in self.teams]
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def add_action(self, name, next_step=None, is_complete=False, id=None):
        """Add an action after this step."""
        action = Action(self.process, name, is_complete=is_complete, id=id)
        action.add_incoming_step(self)
        if isinstance(next_step, Step):
            action.outgoing.append(next_step)
        return action


class Action(object):
    def __init__(self, process, name, is_complete=False, id=None):
        self.id = id or generate_id()
        self.process = process
        self.name = name
        self.is_complete = bool(is_complete)
        self._incoming = {}
        self._outgoing = {}

        if not self.process or not self.name or not self.id:
            raise ValueError('Process, Name and ID must be set.')
        elif not isinstance(self.process, Process):
            raise ValueError('Must be a valid Process instance.')
        else:
            self.process._actions[self.id] = self

    def __unicode__(self):
        return self.to_json()

    def __str__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Action) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        """Create an Action object from a dict object."""
        if not data or not isinstance(data, dict):
            return None

        process = data.get('process', None)
        name = data.get('name', None)
        is_complete = data.get('is_complete', None)
        id = data.get('id', None)

        action = cls(process=process, name=name, is_complete=is_complete, id=id)
        return action

    def add_incoming_step(self, step):
        """Add an incoming Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self._incoming[step.id] = step

    def add_outgoing_step(self, step):
        """Add an outgoing Step to this Action."""
        if not isinstance(step, Step):
            raise ValueError('Must be a valid Step instance.')
        self._outgoing[step.id] = step

    def to_dict(self):
        """Return the Action as a dict object."""
        return {
            'kind': 'Action',
            'id': self.id,
            'process': self.process.id,
            'name': self.name,
            'is_complete': bool(self.is_complete),
            'incoming': [step.to_dict() for step in self._incoming],
            'outgoing': [step.to_dict() for step in self._outgoing]
        }

    def to_json(self):
        """Return the Action as a JSON object."""
        return json.dumps(self.to_dict())

class Client(object):
    realm = 'http://flomosa.appspot.com'
    debug = True
    endpoints = {
        'processes': 'processes/%(id)s.json',
        'requests': 'requests/%(id)s.json',
        'teams': 'teams/%(id)s.json'
    }

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

    def add_process(self, process):
        if not hasattr(process, 'name'):
            raise Exception('Process has no name.')

        endpoint = self.endpoint('processes', id=process.id)
        self._request(endpoint, 'PUT', process.to_json())

    def update_process(self, process):
        return self.add_process(process)

    def get_process(self, id):
        endpoint = self.endpoint('processes', id=id)
        return Process.from_dict(self._request(endpoint, 'GET'))

    def delete_process(self, id):
        if isinstance(id, Process):
            id = id.id
        endpoint = self.endpoint('processes', id=id)
        self._request(endpoint, 'DELETE')

    def add_team(self, team):
        if not hasattr(team, 'name'):
            raise Exception('Team has no name.')
        if not hasattr(team, 'members') or not team.members:
            raise Exception('Team has no members assigned.')

        endpoint = self.endpoint('teams', id=team.id)
        self._request(endpoint, 'PUT', team.to_json())

    def update_team(self, team):
        return self.add_team(team)

    def get_team(self, id):
        endpoint = self.endpoint('teams', id=id)
        return Team.from_dict(self._request(endpoint, 'GET'))

    def delete_team(self, id):
        if isinstance(id, Team):
            id = id.id
        endpoint = self.endpoint('teams', id=id)
        self._request(endpoint, 'DELETE')

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
            print(resp)
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