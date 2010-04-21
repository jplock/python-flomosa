#!/usr/bin/env python

import os
import sys
sys.path[0:0] = [os.path.join(os.path.dirname(__file__), '..'),]

import flomosa

# No one
#KEY = 'test-key'
#SECRET = 'test-secret'

# jplock@gmail.com
#KEY = '1c1d5bbe-02e0-4c91-bac6-99a11307cf2a'
#SECRET = '3cc66e96-829e-4407-801a-b57cfcd14881'

# test@flomosa.com
KEY = '4ef3e685-37c1-43f9-ae03-0a21523051c6'
SECRET = '1913b245-18ae-4caa-a491-cedd2e471a50'

if os.environ['HOST'] == 'philjr.local':
    client = flomosa.Client(KEY, SECRET, host='127.0.0.1', port=8080)
    client.debug = True
else:
    client = flomosa.Client(KEY, SECRET)

filter = ['num_requests']#, 'num_requests_completed']

stats = client.get_year_stats('test', 2010, filter=filter)

stats = client.get_month_stats('test', 2010, 4, filter=filter)

stats = client.get_week_stats('test', 2010, 16, filter=filter)

stats = client.get_day_stats('test', 2010, 4, 20, filter=filter)