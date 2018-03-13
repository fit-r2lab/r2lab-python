#!/usr/bin/env python3

"""
The R2lab sidecar server is a socketIO service that runs on https://r2lab.inria.fr:999/
and that exposes the status of the testbed.
"""

import json
from urllib.parse import urlparse

from socketIO_client import SocketIO, LoggingNamespace


default_sidecar_url = 'https://r2lab.inria.fr:999/'


# the attributes of interest, and their possible values
# this for now is for information only
supported_attributes = {
    'node' : {
        '__range__': range(1, 38),
        'available' : ("on", "off"),
        'usrp_type' : ("none", "b210", "n210", "usrp1", "usrp2",
                       "limesdr", "LEAT LoRa", "e3372"),
        # this is meaningful for b210 nodes only
        'usrp_duplexer' : ("for UE", "for eNB", "none"),
    },
    'phone' : {
        '__range__' : range(1, 2),
        'airplane_mode' : ("on", "off"),
    }
}


class R2labSidecar(SocketIO):

    """
    A handler to reach the testbed sidecar server, and to get the
    testbed status through that channel.

    Unfortunately there does not seem to be a async-enabled python
    library for the client side of socketio, so this for now is
    designed as a synchronous context manager, use in a ``with``
    statement.

    """
    def __init__(self, url=default_sidecar_url):
        self.url = url
        parsed = urlparse(self.url)
        scheme, hostname, port \
            = parsed.scheme, parsed.hostname, parsed.port or 80
        if scheme == 'http':
            host_part = hostname
            extras = {}
        elif scheme == 'https':
            host_part = "https://{}".format(hostname)
            extras = {'verify' : False}
        else:
            print("unsupported scheme {}".format(scheme))
        super().__init__(host_part, port, LoggingNamespace, **extras)
        # hack the default logic so that it waits until WE decide
        self._local_stop_waiting = False


    def channel_data(self, category):
        # The name of the socketio channel used to broadcast data on
        # a given category, which typically is ``nodes`` or ``phones``
        return "info:{}".format(category)

    def channel_request(self, category):
        # ditto for requesting a broadcast about that category
        return "request:{}".format(category)

    
    # so that self.wait() returns when we want it to..
    def _should_stop_waiting(self, *kw):
        return self._local_stop_waiting or SocketIO._should_stop_waiting(self, *kw)

    def _request_category(self, category):
        # what's returned when s/t goes wrong
        # xxx should it raise an exception instead ?
        result = {}
        # reset our own short-circuit flag
        self._local_stop_waiting = False
        def callback(*args):
            nonlocal result
            try:
                string, = args
                parsed = json.loads(string)
                hash = {d['id']: d for d in parsed}
                result = hash
                self._local_stop_waiting = True
            except Exception as e:
                print("OOPS {}".format(type(e)))
                
        self.once(self.channel_data(category), callback)
        # contents does not matter here
        self.emit(self.channel_request(category), 'PLEASE')
        self.wait(seconds=1)
        return result


    def nodes_status(self):
        """
        A blocking function call that returns the JSON nodes status for the complete testbed.

        Returns:
            A python dictionary indexed by integers 1 to 37, whose values are 
            dictionaries with keys corresponding to each node's attributes at that time.

        Example:
            Get the complete testbed status::

                with R2labSidecar() as sidecar:
                    nodes_status = sidecar.nodes_status()
                print(nodes_status[1]['usrp_type'])

        """
        return self._request_category('nodes')

    def set_node(self, id, attribute, value):
        # xxx
        pass

