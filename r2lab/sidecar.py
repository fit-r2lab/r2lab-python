#!/usr/bin/env python3

"""
The R2lab sidecar server is a socketIO service that runs on https://r2lab.inria.fr:999/
and that exposes the status of the testbed.
"""

import json
from urllib.parse import urlparse

from socketIO_client import SocketIO, LoggingNamespace


default_sidecar_url = 'https://r2lab.inria.fr:999/'

### see also
# https://github.com/invisibleroads/socketIO-client/issues/86
# https://github.com/invisibleroads/socketIO-client/pull/87
# https://stackoverflow.com/questions/37058119/python-and-socket-io-app-hangs-after-connection/37186664#37186664
# for a possible fix about SSL connections

# the attributes of interest, and their possible values
# this for now is for information only
supported_attributes = {
    'node': {
        '__range__': range(1, 38),
        'available': ("on", "off"),
        'usrp_type': ("none", "b210", "n210", "usrp1", "usrp2",
                      "limesdr", "LEAT LoRa", "e3372"),
        # this is meaningful for b210 nodes only
        'usrp_duplexer': ("for UE", "for eNB", "none"),
    },
    'phone': {
        '__range__': range(1, 2),
        'airplane_mode': ("on", "off"),
    }
}

# provide a simpler way to turn on debugging
import logging


def socketio_logging_to_stdout(level):
    logger = logging.getLogger('socketIO-client')
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class R2labSidecar(SocketIO):

    """
    A handler to reach the testbed sidecar server, and to get the
    testbed status through that channel.

    Unfortunately there does not seem to be a async-enabled python
    library for the client side of socketio, so this for now is
    designed as a synchronous context manager, use in a ``with``
    statement.

    """

    def __init__(self, url=default_sidecar_url, *, debug=False):
        self.url = url
        parsed = urlparse(self.url)
        scheme, hostname, port \
            = parsed.scheme, parsed.hostname, parsed.port or 80
        if scheme == 'http':
            host_part = hostname
            extras = {}
        elif scheme == 'https':
            host_part = "https://{}".format(hostname)
            extras = {'verify': False}
        else:
            print("unsupported scheme {}".format(scheme))
        super().__init__(host_part, port, LoggingNamespace, **extras)
        # hack the default logic so that it waits until WE decide
        self._local_stop_waiting = False
        # initialize logger; note that by design of socketIO_client,
        # all instances share the same logger
        level = logging.DEBUG if debug else logging.ERROR
        socketio_logging_to_stdout(level)

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

    def _probe_category(self, category):
        # what's returned when s/t goes wrong
        # xxx should it raise an exception instead ?
        infos = None
        # reset our own short-circuit flag
        self._local_stop_waiting = False

        def callback(*args):
            nonlocal infos
            try:
                string, = args
                infos = json.loads(string)
                self._local_stop_waiting = True
            except Exception as e:
                print("R2labSidecar._probe_category - OOPS {} - {}".format(type(e), e))

        self.once(self.channel_data(category), callback)
        # actual contents sent does not matter here
        self.emit(self.channel_request(category), 'PLEASE')
        self.wait(seconds=1)
        info_by_id = {info['id']: info for info in infos}
        return info_by_id

    def _set_triples(self, category, triples):
        # build the corresponding infos - a list of the form
        # [ { 'id' : id, 'attibute' : value, ..}, ...]
        # and emit that on the proper channel
        # for that we start with a hash id -> info
        info_by_id = {}
        for id, attribute, value in triples:
            # accept strings
            id = int(id)
            if id not in info_by_id:
                info_by_id[id] = {'id': id}
            info_by_id[id][attribute] = value
        infos = list(info_by_id.values())
        # send infos on proper channel and json-encoded
        return self.emit(self.channel_data(category),
                         json.dumps(infos),
                         None)

    # nodes

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

        .. warning::
          As of this rough implementation, it is recommended to use this method
          on a freshly opened object. When used on an older object, you may, and probably
          will, receive a result that is older than the time where you posted a request.

        """
        return self._probe_category('nodes')

    def set_nodes_triples(self, *triples):
        """
        Parameters:
          triples: each argument is expected to be a tuple (or list)
            of the form ``id, attribute, value``. The same node
            id can be used in several triples.

        Example:
            To mark node 1 as unavailable and node 2 as turned off::

                sidecar.set_nodes_triples(
                    (1, 'available', 'ok'),
                    (2, 'cmc_on_off', 'off'),
                   )


        """
        return self._set_triples('nodes', triples)

    def set_node_attribute(self, id, attribute, value):
        """
        Parameters:
            id: a node_id as an int or str
            attribute(str): the name of the attribute to be written
            value(str): the new value

        Example:
            To mark node 1 as unavailable::

                sidecar.set_node_attribute(1, 'available', 'ko')
        """
        return self.set_nodes_triples((id, attribute, value))

    # phones

    def phones_status(self):
        "Just like ``nodes_status`` but on phones"
        return self._probe_category('phones')

    def set_phones_triples(self, *triples):
        "Identical to ``set_nodes_triples`` but on phones"
        return self._set_triples('phones', triples)

    def set_phone_attribute(self, id, attribute, value):
        """
        Similar to ``set_node_attribute`` on a phone

        Example:
            To mark phone 2 as being turned off (although this is constantly
            recomputed by the phones monitor)::

                sidecar.set_phone_attribute(2, 'airplane_mode', 'on')
        """
        return self.set_phones_triples((id, attribute, value))
