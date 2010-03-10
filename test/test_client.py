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
        self.host = 'test.flomosa.com'
        self.port = 8080
        self.client = flomosa.Client(key=self.key, secret=self.secret,
            host=self.host, port=self.port)

    def test_init(self):
        self.assertEqual(self.client.key, self.key)
        self.assertEqual(self.client.secret, self.secret)
        self.assertEqual(self.client.host, self.host)
        self.assertEqual(self.client.port, self.port)
        self.assertEqual(self.client.uri, 'http://%s:%s' % \
            (self.host, self.port))
        self.client = flomosa.Client(key=self.key, secret=self.secret,
            host=self.host, port=443)
        self.assertEqual(self.client.uri, 'https://%s' % self.host)

    def test_endpoint(self):
        self.assertRaises(Exception, lambda: self.client.endpoint('test'))
        self.assertRaises(TypeError, lambda: self.client.endpoint('processes'))

    def test_addprocess(self):
        test = []
        self.assertRaises(Exception, lambda: self.client.endpoint('processes',
            process=test))

if __name__ == '__main__':
    unittest.main()
