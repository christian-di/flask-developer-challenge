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
from flask import Flask, jsonify, request
import re

from gistapi.models.gist import Gist

# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"

# Comment by Matthias: This should be moved into an object
# that represents a Github user
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
    #  - github.com not reachable (quite unlikely, but not impossible)
    #  - username non existent
    # BONUS: Paging? How does this work for users with tons of gists?
    #  - see models/gists.py def gist_files_generator, I don't want to copy the code, so left out
    #        clean solution would be a helper function that handles truncation in general, like for a general URL,
    #        maybe as another generator

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
    # ✓ BONUS: Validate the arguments?
    if "username" not in post_data:
        return 'username missing', 422
    if "pattern" not in post_data:
        return 'search pattern missing', 422

    username = post_data['username']
    pattern = post_data['pattern']
    re_pattern = re.compile(pattern)

    result = {}
    result['matches'] = []
    gists = gists_for_user(username)

    # ✓ BONUS: Handle invalid users?
    if 'message' in gists and gists['message'] == "Not Found":
        return "Username unknown to Github", 400

    for gist_json in gists:
        gist_object = Gist(gist_json)
        if gist_object.search_all_gist_files_for_pattern(re_pattern):
            result['matches'].append(gist_object.url())
        # ✓ REQUIRED: Fetch each gist and check for the pattern
        # ✓ BONUS: What about huge gists?
        #    - see models/gist.py def gist_files_generator
        # BONUS: Can we cache results in a datastore/db?
        # Not worked on, steps required theoretically: 
        #    - build a serialiser for class Gist
        #    - build method to check if online version has been updated since date of caching
        #    - search through cache instead of downloaded content

    result['status'] = 'success'
    result['username'] = username
    result['pattern'] = pattern

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
