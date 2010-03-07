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

    def __unicode__(self):
        return self.__repr__()

    def __repr__(self):
        return '%s (#%s)' % (self._message, self._code)


class DecodeError(APIError):
    """There was a problem decoding the API's JSON response."""

    def __init__(self, headers, body):
        APIError.__init__(self, 0, 'Could not decode JSON.', headers)
        self._body = body

    def __repr__(self):
        return '%s - %s' % (self._headers, self._body)


class Process(object):
    def __init__(self, name, description=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self._steps = []
        self._actions = []

    def __unicode__(self):
        return self.to_json()

    def __repr__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Process) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        process = cls(data['name'], data['description'], data['id'])
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

    def add_step(self, name, teams=None, is_start=False):
        """Add a step to this process."""
        if not self._steps:
            is_start = True
        step = Step(self, name, is_start=is_start, teams=teams)
        self._steps.append(step)
        return step


class Team(object):
    def __init__(self, name, description=None, members=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self.members = members or []

    def __unicode__(self):
        return self.to_json()

    def __repr__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Team) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        team = cls(data['name'], data['description'], data['members'],
            data['id'])
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
        self._teams = teams or []

    def __unicode__(self):
        return self.to_json()

    def __repr__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Step) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        team = cls(data['process'], data['name'], data['description'],
            data['is_start'], data['teams'], data['id'])
        return team

    def to_dict(self):
        return {
            'kind': 'Step',
            'id': self.id,
            'process': self.process.id,
            'name': self.name,
            'description': self.description,
            'is_start': bool(self.is_start),
            'teams': [team.to_dict() for team in self._teams]
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def add_action(self, name, next_step=None, is_complete=False):
        """Add an action after this step."""
        action = Action(self.process, name, is_complete=is_complete)
        self.process._actions.append(action)
        action._incoming.append(self)
        if isinstance(next_step, Step):
            action._outgoing.append(next_step)
        return action


class Action(object):
    def __init__(self, process, name, is_complete=False, id=None):
        self.id = id or generate_id()
        self.process = process
        self.name = name
        self.is_complete = bool(is_complete)
        self._incoming = []
        self._outgoing = []

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return self.__unicode__()

    def __eq__(self, other):
        return isinstance(other, Action) and self.id == other.id

    @classmethod
    def from_dict(cls, data):
        if not data or not isinstance(data, dict):
            return None

        action = cls(data['process'], data['name'], data['is_complete'],
            data['id'])
        return action

    def to_dict(self):
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

    def __repr__(self):
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