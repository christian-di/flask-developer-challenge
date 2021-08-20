import os
import sys
import json
import tempfile

import pytest

sys.path.append('gistapi/')
import gistapi


@pytest.fixture
def client(request):
    db_fd, gistapi.app.config['DATABASE'] = tempfile.mkstemp()
    gistapi.app.config['TESTING'] = True
    client = gistapi.app.test_client()

    #with gistapi.app.app_context():
    #    gistapi.init_db()
    
    def teardown():
        os.close(db_fd)
        os.unlink(gistapi.app.config['DATABASE'])
    request.addfinalizer(teardown)

    return client


def test_ping(client):
    """Start with a sanity check."""
    rv = client.get('/ping')
    print('ping results', rv.data)
    assert b'pong' in rv.data


def test_search(client):
    """Start with a passing test."""
    post_data = {'username': 'justdionysus', 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    rv = client.post('/api/v1/search', 
                     data=json.dumps(post_data),
                     headers={'content-type':'application/json'})
    result_dict = json.loads(rv.data.decode('utf-8'))
    expected_dict = {'status': 'success', 
                     'username': 'justdionysus',
                     'pattern': 'TerbiumLabsChallenge_[0-9]+',
                     'matches': ['https://gist.github.com/justdionysus/6b2972aa971dd605f524']}
    assert result_dict == expected_dict


def test_invalid_user_name(client):
    """ Check for invalid username tests """
    post_data = {'username': 'invalidUsertest', 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    rv = client.post('/api/v1/search', 
                     data=json.dumps(post_data),
                     headers={'content-type':'application/json'})
    result_dict = json.loads(rv.data.decode('utf-8'))
    expected_dict = {'status': 'failure', 
                     'message': 'No user found'} 
    assert result_dict == expected_dict

