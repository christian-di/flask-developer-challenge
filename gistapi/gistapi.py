# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
import json
import requests_cache
import re

from flask import Flask, jsonify, request
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession


# *The* app object
app = Flask(__name__)

requests_cache.install_cache('github_cache', backend='sqlite', expire_after=180)

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
    # User account might not exist
    # BONUS: Paging? How does this work for users with tons of gists?
    # Paging helps to prevent loading tons of data into the system memory, 
    # which can result into delayed loading time or even timeouts.
    # The CPU is also stressed at the same time.
    # With paging, a few items are retrieved per page and more can be obtained
    # by accessing more pages. This ensures that lesser memory and CPU are used 
    # when retriving data

    return response.json()

def is_user_valid(username):
    """"Checks to see if the provided GitHub user exists.
    Args:
        username (string): the user to be discovered

    Returns:
        boolen indicating whether a username exsits or not. 
    """
    url = f"https://api.github.com/users/{username}"
    res = requests.get(url.format(username))
    user_exist= True if res.status_code == 200  else False

    return user_exist

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
    username = post_data['username']
    pattern  = post_data['pattern']
    errors = []
    errors.clear()
    if not is_user_valid(username):
        errors.append("invalid username")

    try: 
        re.compile(pattern)
    except Exception: 
        errors.append("invalid regex match pattern")
    
    if len(errors) > 0:
        return jsonify({"message": "validation error(s)", "errors": errors}), 400

    result = {}
    gists = gists_for_user(username)
   
    # BONUS: Handle invalid users?
    _gists = []
    futures = []
    session = FuturesSession()

    for gist in gists:
        future = session.get(list(gist['files'].values())[0]['raw_url'])
        
        username = gist['owner']['login']
        my_url = gist['html_url']
        html_url = f"/{username}/".join(my_url.rsplit('/', 1))
        future.html_url = html_url
        futures.append(future)
    
    for future in as_completed(futures):
        res = future.result()
        _gists.append((res.text, future.html_url))

    matching_gists = [html_url for _gist, html_url in _gists if re.search(pattern, _gist)]
    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern
    result['matches'] = matching_gists

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
