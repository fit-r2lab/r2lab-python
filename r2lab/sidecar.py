#!/usr/bin/env python3

"""
The R2lab sidecar server is a websocket service
that runs on wss://r2lab.inria.fr:999/
and that exposes the status of the testbed.
"""

import json

from contextlib import contextmanager

import websockets


default_sidecar_url = 'wss://r2lab.inria.fr:999/'

# the attributes of interest, and their possible values
# this for now is for information only
SUPPORTED = {
    'nodes': {
        '__range__': range(1, 38),
        'available': ("on", "off"),
        'usrp_type': ("none", "b210", "n210", "usrp1", "usrp2",
                      "limesdr", "LEAT LoRa", "e3372"),
        # this is meaningful for b210 nodes only
        'usrp_duplexer': ("for UE", "for eNB", "none"),
    },
    'phones': {
        '__range__': range(1, 2),
        'airplane_mode': ("on", "off"),
    }
}

# provide a simpler way to turn on debugging
import logging
logging.basicConfig(level=logging.INFO)

def websockets_logging_to_stdout(level):
    logger = logging.getLogger('sidecar')
    logger.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger



# when doing
# async with SidecarClient(url) as proxy:
# the proxy variable actually points at the underlying protocol
# so that's where to add our send / receive methods

class SidecarClientProtocol(websockets.client.WebSocketClientProtocol):

    async def _send_umbrella(self, category, action, message):
        blob = dict(category=category, action=action, message=message)
        text = json.dumps(blob)
        return await self.send(text)


    async def _recv_umbrella(self):
        text = await self.connection.recv()
        blob = json.loads(text)
        if 'category' in blob and 'action' in 'blob' and 'message' in blob:
            return blob
        else:
            logging.error("Received message not a r2lab triplet")
            return {}


    async def _probe_category(self, category):
        # send a request and wait for answer
        # as opposed to socketio, we may receive other traffic here
        # since all goes into the same pipe
        # so, wait until we receive corresponding 'info'
        # improvement could be to repeat the 'request' after a timeout
        infos = None
        await self._send_umbrella(category, 'request', "PLEASE")
        while True:
            answer = await self.recv()
            logging.info(f"receives answer={answer}")
            umbrella = json.loads(answer)
            if (umbrella['category'] == category
                    and umbrella['action'] == 'info'):
                infos = umbrella['message']
                info_by_id = {info['id']: info for info in infos}
                return info_by_id

    async def _set_triples(self, category, triples):
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
        await self._send_umbrella(category, 'info', json.dumps(infos))


    # nodes

    async def nodes_status(self):
        """
        A blocking function call that returns the JSON nodes status for the complete testbed.

        Returns:
            A python dictionary indexed by integers 1 to 37, whose values are
            dictionaries with keys corresponding to each node's attributes at that time.

        Example:
            Get the complete testbed status::

                with SidecarClient() as sidecar:
                    nodes_status = sidecar.nodes_status()
                print(nodes_status[1]['usrp_type'])

        .. warning::
          As of this rough implementation, it is recommended to use this method
          on a freshly opened object. When used on an older object, you may, and probably
          will, receive a result that is older than the time where you posted a request.

        """
        return await self._probe_category('nodes')

    async def set_nodes_triples(self, *triples):
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
        return await self._set_triples('nodes', triples)

    async def set_node_attribute(self, id, attribute, value):
        """
        Parameters:
            id: a node_id as an int or str
            attribute(str): the name of the attribute to be written
            value(str): the new value

        Example:
            To mark node 1 as unavailable::

                sidecar.set_node_attribute(1, 'available', 'ko')
        """
        return await self.set_nodes_triples((id, attribute, value))


    # phones

    async def phones_status(self):
        "Just like ``nodes_status`` but on phones"
        return await self._probe_category('phones')

    async def set_phones_triples(self, *triples):
        "Identical to ``set_nodes_triples`` but on phones"
        return await self._set_triples('phones', triples)

    async def set_phone_attribute(self, id, attribute, value):
        """
        Similar to ``set_node_attribute`` on a phone

        Example:
            To mark phone 2 as being turned off (although this is constantly
            recomputed by the phones monitor)::

                sidecar.set_phone_attribute(2, 'airplane_mode', 'on')
        """
        return await self.set_phones_triples((id, attribute, value))



class SidecarClient(websockets.connect):

    """
    A handler to reach the testbed sidecar server, and to get the
    testbed status through that channel.

    The underlying protocol is SidecarProtocol that inherits
    websockets.client.WebSocketClientProtocol
    https://websockets.readthedocs.io/en/stable/api.html#module-websockets.client
    """

    def __init__(self, url, *args, **kwds):
        if 'create_protocol' in kwds:
            logging.error("should not overwrite create_protocol")
        super().__init__(url, create_protocol=SidecarClientProtocol,
                         *args, **kwds)
