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
import requests_cache

# *The* app object
app = Flask(__name__)

requests_cache.install_cache('gistapi_cache', backend='sqlite', expire_after=180)
# no need for redis for this simple project, nor for any custom cache implementation ;)


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
    if response.status_code != 200:
        return "User with that username does not exist"
    
    gists = []
    if response.links:
        while response.links.get("next", False):
            gists.extend(response.json())
            try:
                response = requests.get(response.links['next']['url'])
            except KeyError:
                print("Api no longer contains next/url in response links") # logger..
                return {}
    else:
        gists = response.json()

    # BONUS: What failures could happen?
    # 404
    # BONUS: Paging? How does this work for users with tons of gists?
    # implemented

    return gists


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
    if post_data.get('username', None) is None:
        return jsonify({
            'status': 'failure',
            'message': 'username parameter isn\' provided',
            'username': '',
            'pattern': '',
            'matches': []
        })

    if post_data.get('pattern', None) is None:
        return jsonify({
            'status': 'failure',
            'message': 'matches parameter isn\'t provided',
            'username': '',
            'pattern': '',
            'matches': []
        })

    username = post_data['username']
    pattern = post_data['pattern']

    result = {}
    gists = gists_for_user(username)
    # BONUS: Handle invalid users?
    if type(gists) == str:
        return jsonify({
            'status': 'failure',
            'message': gists,
            'username': '',
            'pattern': '',
            'matches': []
        })

    found_gists = []
    for gist in gists:
        _gist = requests.get(gist['url']).json()
        gist_content = ""
        for filename, value in _gist['files'].items():
            gist_content += value['content']
        if re.search(pattern, gist_content):
            found_gists.append(_gist['html_url'])

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = found_gists

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
