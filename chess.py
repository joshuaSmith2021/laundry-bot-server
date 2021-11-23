import requests

def get_lichess_games(username, **kwargs):
    req = requests.get(f'https://lichess.org/api/games/user/{username}', params=kwargs)
    return req.text


def get_chesscom_months(username):
    req = requests.get(f'https://api.chess.com/pub/player/{username}/games/archives')
    result = req.json()

    return result['archives']


def get_chesscom_games(username):
    archives = get_chesscom_months(username)
    months = [requests.get(x).json()['games'] for x in archives]

    pgn = []
    for month in months:
        pgn += [x['pgn'] for x in month]

    return '\n\n'.join(pgn)


if __name__ == '__main__':
    username = 'xqcCheckmateSixMoves'
    pgn = get_chesscom_games(username)
    with open('toss.pgn', 'w') as f:
        f.write(pgn)