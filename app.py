import json
import re
import requests

from bs4 import BeautifulSoup

COMPLETE_STATUSES = ['End of cycle', 'Available']

class Machine:
    def __init__(self, **kwargs):
        self.title = kwargs['name']
        self.type = kwargs['type']
        self.status = kwargs['status']
        self.time = kwargs['time'] if kwargs['status'] not in COMPLETE_STATUSES else kwargs['status']

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'{self.type} ({self.time}) - {self.title}'

    def get_status(self):
        time_remaining = None
        if self.status == 'Out of order':
            time_remaining = 3000
        elif self.status not in COMPLETE_STATUSES:
            time_remaining = None
            try:
                time_remaining = int(re.search(r'^\d+', self.time).group())
            except Exception as err:
                # Awful practice, but the laundry site has some
                # weird cases that I haven't seen and haven't
                # prepared for, so if something goes wrong just
                # say the machine is out for a very long time.
                time_remaining = 3000

        return time_remaining


def get_machines(url):
    req = requests.get(url)

    soup = BeautifulSoup(req.text, 'html.parser')

    machines = []

    for row in soup.find_all('tr'):
        if not row.has_attr('class'): continue

        machine_data = {}

        for cell in row.find_all('td'):
            attr = cell.get('class')[0]
            machine_data[attr] = cell.text

        machines.append(Machine(**machine_data))

    washers = [x for x in machines if x.type == 'Washer']
    dryers = [x for x in machines if x.type == 'Dryer']

    return (washers, dryers)


def status_message(machines):
    messages = []

    for i, machine_set in enumerate(machines):
        machine_type = 'washer' if i == 0 else 'dryer'
        statuses = list(zip(machine_set, [x.get_status() for x in machine_set]))

        if not all([x[1] for x in [*statuses]]):
            available = [x[0] for x in [*statuses] if not x[1]]
            quan = len(available)
            messages.append(f'There {"is" if quan == 1 else "are"} {quan} {machine_type}{"s" if quan > 1 else ""} available')
        else:
            shortest = min([x[1] for x in [*statuses] if x[1]])
            messages.append(f'There is a {machine_type} available in {shortest} minute{"s" if shortest > 1 else ""}')

    return messages


from flask import Flask, request, jsonify, after_this_request
app = Flask(__name__)

@app.route('/fulfillment', methods=['POST', 'GET'])
def fulfill():
    @after_this_request
    def add_header(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    machines = get_machines('http://washalert.washlaundry.com/washalertweb/calpoly/WASHALERtweb.aspx?location=676b5302-485a-4edb-8b36-a20d82a3ae20')
    messages = status_message(machines)

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

    machines = get_machines('http://washalert.washlaundry.com/washalertweb/calpoly/WASHALERtweb.aspx?location=676b5302-485a-4edb-8b36-a20d82a3ae20')
    messages = status_message(machines)

    one_dimensional = []
    for category in machines:
        one_dimensional += category

    result = {
        'machines': [[x.type, x.title, x.time] for x in one_dimensional],
        'messages': messages

    }

    return jsonify(result)


if __name__ == '__main__':
    machines = get_machines('http://washalert.washlaundry.com/washalertweb/calpoly/WASHALERtweb.aspx?location=676b5302-485a-4edb-8b36-a20d82a3ae20')
    print(machines)
    status_message(machines)

