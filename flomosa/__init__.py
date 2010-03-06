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
    """ Generate a UUID """
    return str(uuid.uuid4)


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
    def __init__(self, name, desciption=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self.steps = []

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None

        process = cls(data['name'], data['description'], data['id'])
        return process

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def add_step(self, step):
        if not isinstance(step, Step):
            return False

        return self.steps.append(step)

    def remove_step(self, step):
        if not isinstance(step, Step):
            return False

        try:
            self.steps.remove(step)
        except ValueError:
            return False
        return True


class Team(object):
    def __init__(self, name, description=None, members=None, id=None):
        self.id = id or generate_id()
        self.name = name
        self.description = description
        self.members = members or {}

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None

        team = cls(data['name'], data['description'], data['members'],
            data['id'])
        return team

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'members': self.members
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def add_member(self, member):
        return self.members.append(member)

    def remove_member(self, member):
        try:
            self.members.remove(member)
        except ValueError:
            return False
        return True

    def set_members(self, members):
        self.members = members


class Step(object):
    def __init__(self, name, description=None, is_start=False, teams=None,
        id=None, process=None):
        self.id = id or generate_id()
        if isinstance(process, Process):
            self.process = process
        self.name = name
        self.description = description
        self.is_start = bool(is_start)
        self.teams = teams or []

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None

        step = cls(data['name'], data['description'], data['is_start'],
            data['teams'], data['id'])
        return step

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_start': bool(self.is_start),
            'teams': self.teams,
            'process': self.process
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id

    def add_team(self, team):
        if not isinstance(team, Team):
            return False
        return self.teams.append(team)

    def remove_team(self, team):
        if not isinstance(team, Team):
            return False
        try:
            self.teams.remove(team)
        except ValueError:
            return False
        return True

    def set_teams(self, teams):
        self.teams = teams


class Action(object):
    def __init__(self, name, is_complete=False, id=None, process=None):
        self.id = id or generate_id()
        if isinstance(process, Process):
            self.process = process
        self.name = name
        self.is_complete = bool(is_complete)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None

        action = cls(data['name'], data['is_complete'], data['id'])
        return action

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_complete': bool(self.is_complete),
            'process': self.process
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id


class Client(object):
    realm = 'http://127.0.0.1:8080'
    debug = True
    endpoints = {
        'processes': 'processes/%(id)s.json',
        'steps': 'steps/%(id)s.json',
        'teams': 'teams/%(id)s.json',
        'actions': 'actions/%(id)s.json',
        'requests': 'requests/%(id)s.json'
    }

    def __init__(self, key, secret, api_version=API_VERSION, host='127.0.0.1',
        port=8080):
        self.host = host
        self.port = port
        self.consumer = oauth.Consumer(key, secret)
        self.key = key
        self.secret = secret
        self.api_version = api_version
        self.signature = oauth.SignatureMethod_HMAC_SHA1()
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
        self._request(endpoint, 'POST', process.to_json())

    def delete_process(self, id):
        endpoint = self.endpoint('processes', id=id)
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