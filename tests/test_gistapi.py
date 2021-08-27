import os
import json
import tempfile

import pytest

import gistapi


@pytest.fixture
def client(request):
    #db_fd, gistapi.app.config['DATABASE'] = tempfile.mkstemp()
    gistapi.app.config['TESTING'] = True
    client = gistapi.app.test_client()

    # with gistapi.app.app_context():
    #    gistapi.init_db()

    # def teardown():
    #    os.close(db_fd)
    #    os.unlink(flaskr.app.config['DATABASE'])
    # request.addfinalizer(teardown)

    return client


def test_ping(client):
    """Start with a sanity check."""
    rv = client.get('/ping')
    assert b'pong' in rv.data

def test_search(client):
    """Start with a passing test."""
    post_data = {'username': 'justdionysus',
                 'pattern': 'TerbiumLabsChallenge_[0-9]+'}
    rv = client.post('/api/v1/search',
                     data=json.dumps(post_data),
                     headers={'content-type': 'application/json'})
    result_dict = json.loads(rv.data.decode('utf-8'))
    expected_dict = {'status': 'success',
                     'username': 'justdionysus',
                     'pattern': 'TerbiumLabsChallenge_[0-9]+',
                     'matches': ['https://gist.github.com/6b2972aa971dd605f524']}
    assert result_dict == expected_dict

    """Deliberately no pattern given"""
    post_data = {'username': 'justdionysus'}
    rv = client.post('/api/v1/search',
                     data=json.dumps(post_data),
                     headers={'content-type': 'application/json'})
    result = rv.data.decode('utf-8')
    assert rv.status_code == 422
    assert result == "search pattern missing"

    """Deliberately no username given"""
    post_data = {'pattern': 'abcdefg'}
    rv = client.post('/api/v1/search',
                     data=json.dumps(post_data),
                     headers={'content-type': 'application/json'})
    result = rv.data.decode('utf-8')
    assert rv.status_code == 422
    assert result == "username missing"
    
    """Deliberately invalid Github username"""
    post_data = {'username': 'ahopefullyneverexistantusername', 'pattern': 'abcdefg'}
    rv = client.post('/api/v1/search',
                     data=json.dumps(post_data),
                     headers={'content-type': 'application/json'})
    result = rv.data.decode('utf-8')
    assert rv.status_code == 400
    assert result == "Username unknown to Github"