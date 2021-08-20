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
from flask import Flask, abort, jsonify, request
from marshmallow import Schema, fields, ValidationError

# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


@app.errorhandler(404)
def resource_not_found(e):
    """ Handles all Resource not found errors thrown within the application """
    return jsonify(status='failure',message=str(e.description)), 404


def gists_for_user(username):
    """
    Provides the list of gist metadata for a given user.
    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    per_page = 100
    page = 1
    gists_url = f'https://api.github.com/users/{username}/gists?per_page={per_page}&page='
    result = []
    while True:
        response = requests.get(gists_url+str(page))
        if response.status_code == 404:
            abort(404, description="No user found")
        elif response.json():
            page +=1
            result.extend(response.json())
        else:
            print('Total records', len(result))
            break
    return result


class PayloadSchema(Schema):
    """
    Input payload schema for validation
    """
    username = fields.String(required=True, allow_blank=False, allow_none=False)
    pattern = fields.String(required=True, allow_blank=False, allow_none=False)


@app.route("/api/v1/search", methods=['POST'])
def search():
    """
    Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    schema = PayloadSchema()
    
    # Validate post payload
    try:
        post_data = schema.load(post_data)
    except ValidationError as v_err:
        return jsonify(v_err.messages), 400

    username = post_data['username']
    pattern = post_data['pattern']

    gists = gists_for_user(username)
    if not gists:
        abort(404, description=f"No Gists found for username - {username}")
    
    result = {'username': username, 'pattern': pattern}
    matches = []
    try:
        for gist in gists:
            # iterate over each files and check if pattern exists in raw file
            for file_name, content in gist.get('files', {}).items():
                r = requests.get(content['raw_url'], stream=True)
                for each_chunk in r.iter_content(chunk_size=1024):
                    if re.search(pattern.encode('utf-8'), each_chunk):
                        matches.append("/".join(["https://gist.github.com", username,gist['id']]))
                        # breaking even if one match exists in the file
                        break

        result['status'] = 'success'
        result['matches'] = matches
        status_code = 200
    except Exception as e:
        result['status'] = 'failure'
        result['message'] = 'Internal server error'
        print(e)
        status_code = 500
    return jsonify(result), status_code


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9876)
