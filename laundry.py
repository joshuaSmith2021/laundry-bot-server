import json
import re
import requests
from urllib.parse import urlparse, parse_qs

from bs4 import BeautifulSoup

LOCATION_BASE_PATH = 'http://washalert.washlaundry.com/washalertweb/calpoly/washalertweb.aspx?location='
COMPLETE_STATUSES = ['End of cycle', 'Available']
BROKEN_STATUSES = ['Out of order', 'Not online']

#################################
# These functions get the UUIDs #
# for each location on campus.  #
#################################

def get_villages():
    '''Get the links to each village's list of sites. This
    returns a list of tuples, with each tuple following this model.
    [0]: The name of the village (ie Cerro Vista)
    [1]: The url to the village's list of sites
    '''

    villages = requests.get('http://washalert.washlaundry.com/washalertweb/calpoly/cal-poly.html')

    soup = BeautifulSoup(villages.text, 'html.parser')

    hrefs = []

    for cell in soup.find_all('td'):
        links = cell.findChildren('a')

        if len(links) != 1 or not links[0].has_attr('href'):
            continue

        href = links[0]['href']
        url = f'http://washalert.washlaundry.com/washalertweb/calpoly/{href}'
        village_name = re.sub(r'\s+', ' ', links[0].text)

        hrefs.append((village_name, url))

    return hrefs


def get_sites(village):
    '''Gets the UUID for each site in a given
    village. Returns a list of UUIDs.
    '''

    sites = requests.get(village)
    soup = BeautifulSoup(sites.text, 'html.parser')

    uuids = []

    for cell in soup.find_all('td'):
        links = cell.findChildren('a')

        if len(links) != 1 or not links[0].has_attr('href') or links[0].text == 'Back to Villages':
            continue

        url = links[0]['href']
        parsed_url = urlparse(url)
        uuids.append((links[0].text, parse_qs(parsed_url.query)['location'][0]))

    return uuids


def get_all_sites():
    '''Returns a list of tuples representing each village. Each tuple follows the following model.
    [0]: Name of village (ie cerro vista)
    [1]: List of tuples, each representing a site in the village.
        [0]: Name of site (ie bishop)
        [1]: Location UUID for site (ie 5e329a63-5806-4b19-9290-5b155de27eb1)
    '''

    villages = [(village_name, get_sites(url)) for village_name, url in get_villages()]

    return villages


#######################################
# The following functions and classes #
# work together to fetch the current  #
# webpages on the website and parse   #
# the data into machine-readable and  #
# human-readable formats.             #
#######################################

class Machine:
    '''Class representing one machine. It can be a
    washer or a dryer.
    '''
    def __init__(self, **kwargs):
        self.title = kwargs['name']
        self.type = kwargs['type']
        self.status = kwargs['status']
        self.time = kwargs['time'] \
            if re.search(r'\d+', kwargs['time']) else kwargs['status']

        self.available = self.status in COMPLETE_STATUSES

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f'{self.type} ({self.time}) - {self.title}'

    def get_status(self):
        time_remaining = None
        if self.status in BROKEN_STATUSES:
            time_remaining = 3000
        elif self.status not in COMPLETE_STATUSES:
            time_remaining = None
            try:
                time_remaining = int(re.search(r'^\d+', self.time).group())
            except Exception:
                # Awful practice, but the laundry site has some
                # weird cases that I haven't seen and haven't
                # prepared for, so if something goes wrong just
                # say the machine is out for a very long time.
                time_remaining = 3000

        return time_remaining


def get_machines(location):
    '''Returns a tuple containing two lists of machines.
    [0]: List of machines, this is all of the washers.
    [1]: List of machines, this is all of the dryers.
    '''
    req = requests.get(f'{LOCATION_BASE_PATH}{location}')

    soup = BeautifulSoup(req.text, 'html.parser')

    machines = []

    for row in soup.find_all('tr'):
        if not row.has_attr('class'):
            continue

        machine_data = {}

        for cell in row.find_all('td'):
            attr = cell.get('class')[0]
            machine_data[attr] = cell.text

        machines.append(Machine(**machine_data))

    washers = [x for x in machines if x.type == 'Washer']
    dryers = [x for x in machines if x.type == 'Dryer']

    return (washers, dryers)


def status_message(machines):
    '''This function accepts input from get_machines.
    machines: Tuple containing two lists of machines.
              See get_machines for more.
    '''
    messages = []

    for i, machine_set in enumerate(machines):
        machine_type = 'washer' if i == 0 else 'dryer'
        statuses = list(zip(machine_set,
                            [x.get_status() for x in machine_set]))

        if not all([x[1] for x in [*statuses]]):
            available = [x[0] for x in [*statuses] if not x[1]]

            quan = len(available)
            verb = "is" if quan == 1 else "are"
            plural = "s" if quan > 1 else ""

            messages.append(f'There {verb} {quan} {machine_type}{plural} available')
        else:
            shortest = min([x[1] for x in [*statuses] if x[1]])
            plural = "s" if shortest > 1 else ""
            messages.append(f'There is a {machine_type} available in {shortest} minute{plural}')

    return messages


if __name__ == '__main__':
    all_sites = get_all_sites()
    print(json.dumps(all_sites))
    exit()

