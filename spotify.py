import base64
import datetime
import json
from os import access
import requests

with open('secret/spotify.json') as f:
    data = json.loads(f.read())

auth_code_url = f'{data["base_auth_url"]}?client_id={data["client_id"]}&response_type=code&redirect_uri=http://localhost:8080&scope={"%20".join(data["scopes"])}'

# code = input(auth_code_url)

def get_access_token(code):
    req = requests.post('https://accounts.spotify.com/api/token', 
                        headers={
                            'Authorization': f'Basic {base64.urlsafe_b64encode((data["client_id"] + ":" + data["client_secret"]).encode()).decode()}',
                            'Content-Type': 'application/x-www-form-urlencoded'},

                        data={
                            'grant_type': 'authorization_code',
                            'code': code,
                            'redirect_uri': 'http://localhost:8080'
                        })

    print(req.json())


def get_refreshed_access_token(refresh_token):
    req = requests.post('https://accounts.spotify.com/api/token', 
                        headers={
                            'Authorization': f'Basic {base64.urlsafe_b64encode((data["client_id"] + ":" + data["client_secret"]).encode()).decode()}',
                            'Content-Type': 'application/x-www-form-urlencoded'},

                        data={
                            'grant_type': 'refresh_token',
                            'refresh_token': refresh_token,
                        })

    return req.json()


def update_access_token(refresh_token):
    new_token = get_refreshed_access_token(refresh_token)

    access_token = new_token['access_token']
    expiration = datetime.datetime.now().timestamp() + 3600

    data['access_token'] = access_token
    data['expiration'] = expiration

    with open('secret/spotify.json', 'w') as f:
        f.write(json.dumps(data, indent=4, sort_keys=True))


def get_access_token():
    seconds = datetime.datetime.now().timestamp()

    if seconds + 30 > data['expiration']:
        update_access_token(data['refresh_token'])

    return data['access_token']


def get_playback_status(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    req = requests.get('https://api.spotify.com/v1/me/player', headers=headers)

    return req


def queue_song(token, uri):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    req = requests.post(f'https://api.spotify.com/v1/me/player/queue?uri={uri}', headers=headers)

    # 204 is what we want to see for status code
    return req


def search_song(token, query, limit=10, types=['track']):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    req = requests.get('https://api.spotify.com/v1/search', headers=headers, params={
        'q': query,
        'type': types,
        'limit': limit
    })

    return req


if __name__ == '__main__':
    # get_refreshed_access_token(data["refresh_token"])
    # get_playback_status(data['access_token'])
    # queue_song(data['access_token'], 'spotify:track:4zm8xZiV5FxJu62EHEvZaT')
    # search_song(data['access_token'], 'uptown funk')
    # update_access_token(data['refresh_token'])

    print(get_access_token())
