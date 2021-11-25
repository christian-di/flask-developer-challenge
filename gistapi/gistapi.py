# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other development artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""
import logging
import re
from http import HTTPStatus

import requests
from flask import Flask, jsonify, request
from werkzeug.exceptions import InternalServerError, BadRequest, NotFound

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
    if response.status_code != HTTPStatus.OK:
        logging.warning(f"Bad response got from git. Status Code {response.status_code}. Message {response.text}")
        raise InternalServerError()

    # BONUS: Paging? How does this work for users with tons of gists?

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
    username = post_data.get('username')
    pattern = post_data.get('pattern')

    validate_query_params(pattern, username)
    validate_username_on_github(username)

    matches = find_matches(pattern, username)

    return jsonify({
        'status': 'success' if matches else 'not found',
        'username': username,
        'pattern': pattern,
        'matches': matches
    })


def find_matches(pattern, username):
    gists = gists_for_user(username)
    pattern_regex = re.compile(pattern)
    matches = []
    for gist in gists:
        if gist_matches(gist, pattern_regex):
            matches.append(f"https://gist.github.com/{username}/{gist['id']}")
        # BONUS: Can we cache results in a datastore/db?
    return matches


def validate_username_on_github(username):
    github_user = requests.get(f'https://api.github.com/users/{username}')
    if github_user.status_code != HTTPStatus.OK:
        raise NotFound(f"Username {username} not found")


def validate_query_params(pattern, username):
    # Todo add proper library to have a more robust validation
    if not username or not pattern:
        raise BadRequest("Username or pattern not specified")
    if not re.match(r'^[A-Za-z-]*$', username):
        raise BadRequest("Username has a wrong format")


def gist_matches(gist, pattern_regex):
    result = False
    for file in gist.get('files').keys():
        text = requests.get(gist['files'][file]['raw_url'])
        if pattern_regex.match(text.text):
            result = True
            break
    return result


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)


__all__ = ["app"]
