#!/usr/bin/env python3

import random
import json
import time
import datetime

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from r2lab import (SidecarSyncClient, SidecarPayload)

# in seconds
default_cycle = 1
default_runs = 0

# should maybe default to this official one, but mostly it's firewalled
# default_sidecar_url = "https://r2lab-sidecar.inria.fr:443/"
default_sidecar_url = "ws://localhost:10000/"

node_ids = range(1, 38)
default_max_nodes_impacted = 10

######## helper to create float ranges
def drange(start, stop, step):
    result = []
    r = start
    while r < stop:
        result.append(r)
        r += step
    return result

######## the nodes records follow the data model of monitornodes:
# live flags: cmc_on_off, usrp_on_off, control_ping, control_ssh (ssh on any
#          port), control_telnet, ssh_ports (where ssh answers: 22 and/or 2222)
# 'state': one label computed from these, off | bios | booting | telnet |
#          docker-only | container | regular | zombie | unknown
# 'metal': the bare machine - ssh_port, os_release, pretty_name,
#          image_radical, uname, gnuradio_release, docker_version, seen
# 'container': None, or image, running, started, os_release, pretty_name, seen
# 'static': free-form, comes from the inventory, never changes here
# 'availability': status ok|ko, reason, since - comes from the r2lab-api

# (os_release, pretty_name, uname)
distros = [
    ('fedora-41', 'Fedora Linux 41 (Server Edition)', '6.17.9-100.fc41.x86_64'),
    ('ubuntu-24.04', 'Ubuntu 24.04.3 LTS', '6.8.0-60-generic'),
    ('ubuntu-26.04', 'Ubuntu 26.04 LTS', '7.0.0-12-generic'),
    ('debian-12', 'Debian GNU/Linux 12 (bookworm)', '6.1.0-37-amd64'),
    ('rocky-9', 'Rocky Linux 9.5 (Blue Onyx)', '5.14.0-503.el9.x86_64'),
    ('alma-9', 'AlmaLinux 9.5 (Teal Serval)', '5.14.0-503.el9.x86_64'),
    ('alpine-3.24.4', 'Alpine Linux v3.24', '6.12.1-0-lts'),
    ('mint-22', 'Linux Mint 22', '6.8.0-60-generic'),
    ('opensuse-15.6', 'openSUSE Leap 15.6', '6.4.0-150600-default'),
    ('arch-rolling', 'Arch Linux', '6.12.1-arch1-1'),
    ('other', 'Some Other Linux', '5.15.0-foo'),
]

usrp_types = [None, None, 'b205', 'b210', 'n210', 'usrp1', 'usrp2',
              'limesdr', 'e3372', 'Quectel 4G/5G']
duplexers = ['', '2-5G', 'Dup-UE', 'Dup-eNB', 'Dup-UE/2-5G']

unavailable_reasons = ['ssh unreachable after reset', 'broken CMC',
                       'frisbee failed', 'USRP not detected']

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc)\
        .strftime("%Y-%m-%dT%H:%M:%SZ")

def static_record(id):
    "what positions.yaml says about a slot; stable for a given id"
    rnd = random.Random(id)
    record = {'data_interface': rnd.random() > 0.2,
              'images': [f"2026-07/fit{id:02d}.jpg"],
              'images_wifi': [f"{id:02d}-1.JPG", f"{id:02d}-2.JPG"],
              'images_usrp': []}
    usrp_type = rnd.choice(usrp_types)
    if usrp_type:
        record['usrp_type'] = usrp_type
        record['usrp_duplexer'] = rnd.choice(duplexers)
        record['images'].append(f"2026-07/fit{id:02d}-{usrp_type.split()[0].lower()}.jpg")
        if usrp_type.startswith('Quectel'):
            record['usrp_logo'] = 'antenna'
    else:
        record['usrp_type'] = 'none'
    return record

def distro_record(os_release):
    for distro in distros:
        if distro[0] == os_release:
            return distro
    raise ValueError(os_release)

class SimNode:
    """
    the state of one simulated node, that persists across cycles, the way
    monitornodes keeps the last known metal and container of a node that is off
    one node out of 3 is a docker node
    """

    def __init__(self, id):
        self.id = id
        self.docker = id % 3 == 0
        self.static = static_record(id)
        self.state = 'off'
        self.usrp = 'off'
        self.flags = {}
        self.apply_state()
        # until a node has been up, we know nothing about what runs there
        self.metal = None
        self.container = None
        self.availability = {'status': 'ok'}

    # what each state looks like from the outside:
    # cmc, ping, ssh ports (None: no telnet to speak of either)
    SHAPES = {
        'off': ('off', 'off', []),
        'bios': ('on', 'off', []),
        'booting': ('on', 'on', []),
        'zombie': ('on', 'on', []),
        'telnet': ('on', 'on', []),
        'regular': ('on', 'on', [22]),
        'docker-only': ('on', 'on', [2222]),
        'container': ('on', 'on', [22, 2222]),
        'unknown': ('fail', 'off', []),
    }

    def apply_state(self):
        cmc, ping, ports = self.SHAPES[self.state]
        self.flags = {
            'state': self.state,
            'cmc_on_off': cmc, 'usrp_on_off': self.usrp,
            'control_ping': ping,
            'control_ssh': 'on' if ports else 'off',
            'control_telnet': 'on' if self.state == 'telnet' else 'off',
            'ssh_ports': ports,
        }

    def make_metal(self):
        os_release, pretty_name, uname = random.choice(distros)
        if self.docker:
            return {'ssh_port': 2222, 'os_release': os_release,
                    'pretty_name': pretty_name,
                    'image_radical': f"{os_release}+docker-ssh2222",
                    'uname': uname, 'gnuradio_release': 'none',
                    'docker_version': random.choice(['27.3.1', '28.0.4', '29.1.2']),
                    'seen': int(time.time())}
        return {'ssh_port': 22, 'os_release': os_release,
                'pretty_name': pretty_name,
                'image_radical': f"{os_release}-2026-07",
                'uname': uname,
                'gnuradio_release': random.choice(['none', '3.10.9']),
                'docker_version': '',
                'seen': int(time.time())}

    def make_container(self):
        os_release, pretty_name, _ = random.choice(distros)
        return {'image': f"r2lab/{os_release.split('-')[0]}:latest",
                'running': random.random() > 0.2,
                'started': iso_now(),
                'os_release': os_release, 'pretty_name': pretty_name,
                'seen': int(time.time())}

    def up_state(self):
        "where a node that has finished booting ends up"
        if not self.docker:
            return 'regular'
        # the container may not be started yet
        return 'container' if random.random() < 0.7 else 'docker-only'

    def evolve(self):
        """
        one random transition, like monitornodes would observe, along
        off -> bios -> booting -> (telnet -> booting ->) up -> off ...
        """
        r = random.random()
        state = self.state
        if state == 'off':
            if r < 0.4:
                self.state = 'bios'
        elif state == 'bios':
            self.state = 'booting'
        elif state == 'booting':
            if r < 0.25:
                self.state = 'telnet'
            elif r < 0.30:
                self.state = 'zombie'
            elif r < 0.70:
                self.state = self.up_state()
                self.usrp = random.choice(['on', 'on', 'off'])
        elif state == 'telnet':
            # the image is loaded, the node reboots
            if r < 0.4:
                self.state = 'bios'
        elif state in ('zombie', 'unknown'):
            if r < 0.3:
                self.state = 'off'
        else:
            if r < 0.08:
                # off: the flags go off, the last metal and container stay
                self.state = 'off'
                self.usrp = 'off'
            elif r < 0.12:
                # an rload or rsave
                self.state = 'telnet'
            elif r < 0.14:
                self.state = 'unknown'
            elif r < 0.30 and self.docker:
                # the container stops or restarts, the metal stays
                self.state = ('docker-only' if state == 'container'
                              else 'container')
            elif r < 0.34:
                self.usrp = random.choice(['on', 'off'])
        if self.state == 'off':
            self.usrp = 'off'
        if self.state in ('regular', 'container', 'docker-only'):
            if state not in ('regular', 'container', 'docker-only'):
                # we have just got in: a new metal
                self.metal = self.make_metal()
                self.container = None
            if self.state == 'container':
                # the user logs into a running container
                if not self.container or not self.container['running']:
                    self.container = self.make_container()
                    self.container['running'] = True
            elif self.state == 'docker-only':
                # a docker host whose container is stopped, or that has none
                if state == 'container' or (
                        state not in ('docker-only', 'container')
                        and self.docker and random.random() < 0.5):
                    self.container = dict(
                        self.container or self.make_container(),
                        running=False, started=iso_now(),
                        seen=int(time.time()))
            else:
                # a regular node has no container
                self.container = None
        self.apply_state()
        # availability, as set by the nightly script
        if self.availability['status'] == 'ok' and random.random() < 0.03:
            self.availability = {'status': 'ko', 'since': iso_now(),
                                 'reason': random.choice(unavailable_reasons)}
        elif self.availability['status'] == 'ko' and random.random() < 0.2:
            self.availability = {'status': 'ok'}

    def info(self, index=0):
        """
        what monitornodes would report; for index > 0 we leave out some of
        the optional keys, to test incomplete news on the livemap side

        monitornodes always sends together what goes together: the state and
        the flags it derives from (cmc_on_off, control_ping, control_ssh,
        control_telnet, ssh_ports), and metal with container; some of these
        make no sense without the others, so we never drop them
        """
        info = {'id': self.id, 'static': self.static,
                'availability': self.availability, **self.flags}
        if self.metal:
            info['metal'] = self.metal
            info['container'] = self.container
        optional = ['static', 'availability', 'usrp_on_off']
        for key in random.sample(optional, min(index, len(optional))):
            del info[key]
        return info

sim_nodes = {id: SimNode(id) for id in node_ids}

phones_field_possible_values = {
    'wifi_on_off' : [ 'on', 'off' ],
    'airplane_mode' : [ 'on', 'off', 'fail'],
}

####################
def random_ids(max_nodes_impacted):
    how_many = random.randint(1, max_nodes_impacted)
    return [ random.choice(node_ids) for i in range(how_many)]

def random_node_status(id, index=0):
    # index == 0 means we need a complete record
    # otherwise some keys are left out
    node = sim_nodes[id]
    node.evolve()
    return node.info(index)

def random_phone_status(id):
    phone_info = { 'id' : id }
    # fill phone_info with all known keys
    phone_info.update( { field : random.choice(values)
                       for field, values in phones_field_possible_values.items() })
    return phone_info

# too lazy to get this properly (need to turn off server auth)
nightly = 'inria-nightly'
other_slice = 'inria-tutorial'

def get_leases():
    print("WARNING: get_leases returns a hard-wired set of leases today")
    today = datetime.datetime.now()
    slices_specs = [
        # slicename - hour-from - hour-until
        (nightly, 8, 10),
        (nightly, 13, 15),
        (nightly, 17, 18),
        (other_slice, 3, 4),
        (other_slice, 20, 21),
    ]
    return [
        {
            "uuid" : id + 100,
            "slicename" : slicename,
            "ok" : True,
            "valid_from" : "{:%Y-%m-%d}T{:02d}:00:00".format(today, start),
            "valid_until" : "{:%Y-%m-%d}T{:02d}:00:00".format(today, end),
        }
        for (id, (slicename, start, end)) in enumerate(slices_specs)
    ]

def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--cycle', dest='cycle', default=default_cycle,
                        type=float,
                        help="Cycle duration in seconds")
    parser.add_argument('-r', '--runs', dest='runs', default=default_runs,
                        type=int,
                        help="How many runs - means forever")
    parser.add_argument('-n', '--nodes', dest='max_nodes_impacted',
                        default=default_max_nodes_impacted, type=int,
                        help="Maximum number of nodes impacted by each cycle")
    parser.add_argument('-l', '--live', dest='live', action='store_true', default=False,
                        help="If set, only rx/tx data are animated")
    parser.add_argument('-p', '--phone-cycle', default=5, type=int,
                        help='send a random phone status every n cycles')
    parser.add_argument("-u", "--sidecar-url", dest="sidecar_url",
                        default=default_sidecar_url,
                        help="url for the sidecar server")
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    args = parser.parse_args()

    cycle = args.cycle

    if args.live:
        to_remove = [ k for k in field_possible_values
                     if 'rx' not in k and 'tx' not in k]
        for k in to_remove:
            del field_possible_values[k]

    if args.verbose:
        print("Using cycle {}s".format(cycle))

    url = args.sidecar_url
    print("Connecting to sidecar at {}".format(url))

    # for connecting to a https endpoint
    # because by default openssl has no CA installed
    # - contrary to the browser model -
    # we turn off server authentication
    secure = url.startswith('wss:')
    kwds = {}
    if secure:
        import ssl
        # kwds.update(dict(ssl=ssl.create_default_context()))
        kwds.update(dict(ssl=ssl.SSLContext()))

    # the sync client only runs its event loop during calls, so keepalive
    # pings can't be answered while we sleep: disable them on our side,
    # and reconnect transparently whenever the connection is dropped
    kwds.setdefault('ping_interval', None)

    class Session:
        def __init__(self):
            self.client = None

        def connect(self):
            self.close()
            self.client = SidecarSyncClient(url, **kwds)
            self.client.connect()

        def close(self):
            if self.client is not None:
                try:
                    self.client.close()
                except Exception as exc:
                    print(f"ignoring error while closing: {exc!r}")
                self.client = None

        def send(self, payload, retries=3):
            for attempt in range(1, retries + 1):
                try:
                    if self.client is None:
                        self.connect()
                    self.client.send_payload(payload)
                    return True
                except Exception as exc:
                    print(f"send failed (attempt {attempt}/{retries}): {exc!r}")
                    self.close()
                    time.sleep(min(2 ** attempt, 10))
            print("giving up on this payload, will retry next cycle")
            return False

    session = Session()
    try:
        counter = 0
        payload = SidecarPayload()
        while True:
            news_infos = [ random_node_status(id, index)
                           for index, id in enumerate(random_ids(args.max_nodes_impacted)) ]
            if args.verbose:
                print("{} -- on {} nodes (id, len(fields)) : {}"
                      .format(counter, len(news_infos),
                              [ (info['id'], len(info)-1) for info in news_infos]))
                print(news_infos[0])
            payload.fill_from_infos(news_infos, category='nodes')
            session.send(payload)

            # only one phone
            if counter % args.phone_cycle == 0:
                phone_infos = [ random_phone_status(id) for id in [1]]
                if args.verbose:
                    print("phone: emitting {}".format(phone_infos[0]))
                payload.fill_from_infos(phone_infos, 'phones')
                session.send(payload)

            try:
                leases = get_leases()
            except Exception as exc:
                print(f"get_leases failed: {exc!r}")
                leases = None
            if leases:
                if args.verbose:
                    print(f"leases {leases}")
                payload.fill_from_infos(leases, 'leases')
                session.send(payload)
            counter += 1
            if args.runs and counter >= args.runs:
                break
            time.sleep(cycle)
    except KeyboardInterrupt:
        pass
    finally:
        session.close()


if __name__ == '__main__':
    main()
