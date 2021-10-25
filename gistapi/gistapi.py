# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""
import re

import requests
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = 'https://api.github.com/users/{username}/gists'.format(
            username=username)
    response = requests.get(gists_url)
    # BONUS: What failures could happen?
    # Network failure can occur, username may not exist, api may deprecate
    # BONUS: Paging? How does this work for users with tons of gists?
    # Paging can be use optimize the memory in conjunction with yield

    return response.json()


@app.route("/api/v1/search", methods=['POST'])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments?
    # We can use marshmallow to serialize the post data for validation

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    # BONUS: Handle invalid users?
    # raise 404 for invalid users by checking status of the response
    session = requests.Session()
    matches = []
    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        for file in gist['files'].values():
            gist_content = session.get(file['raw_url']).text
            if re.search(pattern, gist_content):
                matches.append('https://gist.github.com/{username}/{gist_id}'.format(
                    username=username, gist_id=gist['id']))
        # BONUS: What about huge gists?
        # As per documentation, truncate key can be used to identify such cases and handle them accordingly
        # BONUS: Can we cache results in a datastore/db?
        # Yes, we can use the gist updated_at to invalidate cache

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matches

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
