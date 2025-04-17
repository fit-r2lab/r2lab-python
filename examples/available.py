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
DEFAULT_SIDECAR_URL = "wss://r2lab-sidecar.inria.fr:443/"
DEVEL_SIDECAR_URL = "ws://localhost:10000/"

def main():
    # parse args
    parser = ArgumentParser()
    parser.add_argument("nodes", nargs='+', type=int)
    parser.add_argument(
        "-u", "--sidecar-url", dest="sidecar_url",
        default=DEFAULT_SIDECAR_URL,
        help=f"url for thesidecar server (default={DEFAULT_SIDECAR_URL})")
    parser.add_argument(
        "-d", "--devel", default=False, action='store_true')
    parser.add_argument(
        "-s", "--secure", default=False, action='store_true',
        help="trigger SSL server verification")

    # parser.add_argument("-v", "--verbose", default=False, action='store_true')
    args = parser.parse_args()


    # check if run as 'available.py' or 'unavailable.py'
    import sys
    available_value = 'ko' if 'un' in sys.argv[0] else 'ok'

    if args.devel:
        url = DEVEL_SIDECAR_URL
    else:
        url = args.sidecar_url


    def check_valid(node):
        return 1 <= node <= 37


    invalid_nodes = [node for node in args.nodes if not check_valid(node)]

    if invalid_nodes:
        print(f"Invalid inputs {invalid_nodes} - exiting")
        exit(1)

    triples = [(node, 'available', available_value) for node in args.nodes]

    ssl_kwargs = {}
    if args.secure:
        ssl_kwargs['ssl'] = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    print("Connecting to sidecar at {}".format(url))

    with SidecarSyncClient(url, **ssl_kwargs) as sidecar:
        sidecar.set_nodes_triples(*triples)

if __name__ == "__main__":
    main()
