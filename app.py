import json
import re
from flask.wrappers import Response

from flask import Flask, request, jsonify, after_this_request, Response

import chess
import laundry
import spotify

app = Flask(__name__)

with open('secret/spotify.json') as f:
    SPOTIFY_DATA = json.loads(f.read())


@app.route('/laundry_locations', methods=['GET'])
def get_laundry_locations():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    all_sites = laundry.get_all_sites()
    return jsonify(all_sites)


@app.route('/fulfillment', methods=['POST', 'GET'])
def fulfill():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    location = request.args.get('location', '676b5302-485a-4edb-8b36-a20d82a3ae20')

    machines = laundry.get_machines(location)
    messages = laundry.status_message(machines)

    res = {
        'prompt': {
            'override': False,
            'firstSimple': {
                'speech': f'{". ".join(messages)}.'
            }
        }
    }

    return jsonify(res)


@app.route('/raw_status', methods=['POST', 'GET'])
def raw_status():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    location = request.args.get('location', '676b5302-485a-4edb-8b36-a20d82a3ae20')

    machines = laundry.get_machines(location)
    messages = laundry.status_message(machines)

    one_dimensional = []
    for category in machines:
        one_dimensional += category

    result = {
        'machines': [[x.type, x.title, x.time, x.available] for x in one_dimensional],
        'messages': messages
    }

    return jsonify(result)


@app.route('/playback_status', methods=['GET'])
def playback_status():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    status = spotify.get_playback_status(spotify.get_access_token())

    return jsonify(status.json())


@app.route('/search_spotify', methods=['GET'])
def search_spotify():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    query = request.args.get('q')

    search = spotify.search_song(spotify.get_access_token(), query)

    return jsonify(search.json())


@app.route('/queue_song', methods=['GET'])
def queue_song():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    uri = request.args.get('uri')

    queue_request = spotify.queue_song(spotify.get_access_token(), uri)

    return jsonify(spotify.get_playback_status(spotify.get_access_token()).json())


@app.route('/get_pgn', methods=['GET'])
def get_pgn():
    functions = {
        'lc': chess.get_lichess_games,
        'cc': chess.get_chesscom_games
    }

    args = request.args

    pgn = []
    usernames = []
    for site, username in args.items():
        if site not in functions.keys():
            continue

        usernames.append(username)
        pgn.append(functions[site](username))

    pgn = '\n\n'.join(pgn)

    if 'alias' in args.keys():
        pgn = re.sub(f'({"|".join(usernames)})', args['alias'], pgn, flags=re.IGNORECASE)

    return Response(pgn, mimetype='application/x-chess-pgn')

