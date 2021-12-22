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
import re

from flask import Flask, jsonify, request

# *The* app object
from werkzeug.exceptions import NotFound
from werkzeug.routing import ValidationError

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
    # BONUS: Paging? How does this work for users with tons of gists?

    return response.json()


def check_pattern(gist, pattern):
    files = gist["files"]
    matches = []
    for key, value in files.items():
        raw_url = value["raw_url"]
        res = requests.get(raw_url)
        matched = re.search(pattern, res.text)
        matches.append(True) if matched is not None else False
    return set(matches)


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
    try:
        post_data = request.get_json()
        # BONUS: Validate the arguments?
        for key, value in post_data.items():
            if not isinstance(value, str):
                raise ValidationError(f"The value of {value} should be of type str.")

        username = post_data['username']
        pattern = post_data['pattern']

        result = {}
        gists = gists_for_user(username)
        if not isinstance(gists, list) and gists["message"] == "Not Found":
            raise NotFound("User with that username was not found on Github.")
        # BONUS: Handle invalid users?

        final_list = []

        if len(gists) < 1:
            raise NotFound("That Github user does not have any gists.")
        for gist in gists:
            matches = check_pattern(gist, pattern)
            if True in matches:
                url = f'https://gist.github.com/{gist["owner"]["login"]}/{gist["id"]}'
                final_list.append(url)
            else:
                continue
            # REQUIRED: Fetch each gist and check for the pattern
            # BONUS: What about huge gists?
            # BONUS: Can we cache results in a datastore/db?

        result['status'] = 'success'
        result['username'] = username
        result['pattern'] = pattern
        result['matches'] = final_list
        return jsonify(result)
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except NotFound as e:
        return jsonify({"error": str(e)}), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
