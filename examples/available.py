#!/usr/bin/env python3

"""
This script emits messages to the sidecar server on faraday
to instruct it that some nodes are available or not
(use available.py or unavailable.py)
"""

# xxx todo1 - if needed we could add options too to chose between available and unavailable
# xxx todo2 - more importantly we could consider talking to the OMF inventory on faraday
#             to maintain the same status over there


from argparse import ArgumentParser

from r2lab import SidecarSyncClient

# globals
default_sidecar_url = "wss://r2lab-sidecar.inria.fr:443/"
devel_sidecar_url = "ws://localhost:10000/"

# parse args
parser = ArgumentParser()
parser.add_argument("nodes", nargs='+', type=int)
parser.add_argument("-u", "--sidecar-url", dest="sidecar_url",
                    default=default_sidecar_url,
                    help="url for thesidecar server (default={})"
                    .format(default_sidecar_url))
parser.add_argument("-d", "--devel",
                    default=False, action='store_true')
# parser.add_argument("-v", "--verbose", default=False, action='store_true')
args = parser.parse_args()


# check if run as 'available.py' or 'unavailable.py'
import sys
available_value = 'ko' if 'un' in sys.argv[0] else 'ok'

if args.devel:
    url = devel_sidecar_url
else:
    url = args.sidecar_url


def check_valid(node):
    return 1 <= node <= 37


invalid_nodes = [node for node in args.nodes if not check_valid(node)]

if invalid_nodes:
    print("Invalid inputs {} - exiting".format(invalid_nodes))
    exit(1)

triples = [(node, 'available', available_value) for node in args.nodes]

import websockets
secure, *_ = websockets.uri.parse_uri(url)
kwds = {}
if secure:
    import ssl
    # kwds.update(dict(ssl=ssl.create_default_context()))
    kwds.update(dict(ssl=ssl.SSLContext()))

print("Connecting to sidecar at {}".format(url))

with SidecarSyncClient(url, **kwds) as sidecar:
    sidecar.set_nodes_triples(*triples)
