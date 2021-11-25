import pytest

from gistapi import gistapi


@pytest.fixture
def client(request):
    # db_fd, gistapi.app.config['DATABASE'] = tempfile.mkstemp()
    gistapi.app.config['TESTING'] = True
    client = gistapi.app.test_client()

    # with gistapi.app.app_context():
    #    gistapi.init_db()

    # def teardown():
    #    os.close(db_fd)
    #    os.unlink(flaskr.app.config['DATABASE'])
    # request.addfinalizer(teardown)

    return client
