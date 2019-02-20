#!/usr/bin/env python3

"""
The R2lab sidecar is a websocket service that runs on
``wss://r2lab.inria.fr:999/`` and that exposes the status of the testbed.

This module implements client classes, for interacting with the sidecar service.

The core of the implementation is ``asyncio``-friendly and accessible
through the :class:`~r2lab.sidecar.SidecarAsyncClient` class, but for
convenience some features are also available to synchronous code through
the :class:`~r2lab.sidecar.SidecarSyncClient` class.
"""

# pylint: disable=w1203

import logging

import asyncio
import websockets

from .sidecar_payload import SidecarPayload as Payload


default_sidecar_url = 'wss://r2lab.inria.fr:999/'

# provide a simpler way to turn on debugging
logging.basicConfig(level=logging.INFO)

def _websockets_logging_to_stdout(level):
    logger = logging.getLogger('sidecar')
    logger.setLevel(level)
    channel = logging.StreamHandler()
    channel.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%m-%d %H:%M:%S")
    channel.setFormatter(formatter)
    logger.addHandler(channel)
    return logger


# when doing
# async with AsyncSidecarProxy(url) as proxy:
# the proxy variable actually points at the underlying protocol
# so that's where to add our send / receive methods

class SidecarProtocol(websockets.client.WebSocketClientProtocol):

    """
    The SidecarProtocol class is an asyncio-compliant implementation
    of the R2lab sidecar system.

    It inherits ``websockets.client.WebSocketClientProtocol``
    as documented here:
    https://websockets.readthedocs.io/en/stable/api.html#module-websockets.client
    """

    async def send_payload(self, payload):
        """
        Send a :class:`~r2lab.sidecar_payload.SidecarPayload`
        object.
        """
        return await self.send(payload.string)

    async def recv_payload(self):
        """
        Receives and returns a
        :class:`~r2lab.sidecar_payload.SidecarPayload` object.
        """
        wired = await self.recv()
        return Payload(string=wired)

    # for historical reasons, if 'incremental' is not present
    # then its a full info message
    @staticmethod
    def is_not_incremental(umbrella):
        return ('incremental' not in umbrella
                or not umbrella['incremental'])

    async def send_umbrella(self, category, action, message):
        """
        Set one payload, constructed from its parts
        """
        return await self.send_payload(
            Payload(
                umbrella=dict(category=category, action=action, message=message)))

    async def recv_umbrella(self):
        """
        Read one payload, and returns it as a dict with 3 keys.
        """
        payload = await self.recv_payload()
        return payload.umbrella


    async def _probe_category(self, category):
        # send a request and wait for answer
        # as opposed to socketio, we may receive other traffic here
        # since all goes into the same pipe
        # so, wait until we receive corresponding 'info'
        # improvement could be to repeat the 'request' after a timeout
        infos = None
        await self.send_umbrella(category, 'request', "PLEASE")
        while True:
            umbrella = await self.recv_umbrella()
            logging.debug(f"receives answer={umbrella}")
            if (umbrella['category'] == category
                    and umbrella['action'] == 'info'
                    and self.is_not_incremental(umbrella)):
                infos = umbrella['message']
                info_by_id = {info['id']: info for info in infos}
                return info_by_id

    async def _set_triples(self, category, triples):
        # build the corresponding infos - a list of the form
        # [ { 'id' : id, 'attibute' : value, ..}, ...]
        # and emit that on the proper channel
        # for that we start with a hash id -> info
        # send infos on proper channel and json-encoded
        payload = Payload().fill_from_triples(category, triples)
        await self.send_payload(payload)


    # nodes

    async def nodes_status(self):
        """
        A function call that returns the JSON nodes status for the complete testbed.

        Returns:
            A python dictionary indexed by integers 1 to 37, whose values are
            dictionaries with keys corresponding to each node's attributes at that time.

        Example:
            Get the complete testbed status::

                async with SidecarAsyncClient() as sidecar:
                    nodes_status = await sidecar.nodes_status()
                print(nodes_status[1]['usrp_type'])

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

                await sidecar.set_nodes_triples(
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

                await sidecar.set_node_attribute(1, 'available', 'ko')
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

                await sidecar.set_phone_attribute(2, 'airplane_mode', 'on')
        """
        return await self.set_phones_triples((id, attribute, value))



class SidecarAsyncClient(websockets.connect):

    """
    This class behaves as an asynchronous context manager for
    talking with the R2lab sidecar server.

    Optional arguments `args` and `kwds` are passed as-is to
    `websockets.client.connect`, see
    https://websockets.readthedocs.io/en/stable/api.html#websockets.client.connect

    Example:
        Set a node as available from some asynchronous code::

            async with SidecarSyncClient() as sidecar:
                await sidecar.set_node_attribute(1, 'available', 'ok')

        In this example, the ``sidecar`` object is
        a :class:`~r2lab.sidecar.SidecarProtocol` instance.

    Note:
        **About SSL server certificate verification:**
        Verifying server certificates relies on a set of "trusted" CAs.
        Web browsers do come with a maintained set of such trust anchors,
        however the standard Python installation has no such knowledge;
        and for that reason attempting to check for the testbed's certificate
        will fail unless you've taken the time to somehow configure all this.

        If you just want to probe the testbed though, this looks like a lot
        of hassle. In that case you can turn off server verification as foolows::

            import ssl
            ssl_context = ssl.SSLContext()
            # this is where we ask for no verification
            ssl_context.verify_mode = ssl.CERT_NONE
            async with SidecarSyncClient(ssl=ssl_context) as sidecar:
                await sidecar.set_node_attribute(1, 'available', 'ok')


    """

    def __init__(self, url=default_sidecar_url, *args, **kwds):
        if 'create_protocol' in kwds:
            logging.error("should not overwrite create_protocol")
        super().__init__(url, create_protocol=SidecarProtocol,
                         *args, **kwds)



# -------- synchronous wrapper

class SidecarSyncClient:
    """
    A synchronous wrapper to perform the same operations
    from sequential code without having to worry about the
    event loop, asynchronous context manager and coroutine business.

    Example:
        Set a node as available from some synchronous code::

            with SidecarSyncClient() as sidecar:
                sidecar.set_node_attribute(1, 'available', 'ok')

    .. warning::
      This is a convenience only, it would be unwise, obviously,
      to call this from asynchronous code; if it works at all.
      Use :class:`~r2lab.sidecar.SidecarAsyncClient` instead
      in this use case.
    """

    def __init__(self, url=default_sidecar_url, *args, **kwds):
        self.aclient = SidecarAsyncClient(url, *args, **kwds)
        self.proto = None

    def connect(self):
        if self.proto:
            logging.warning("SyncClient already connected")
        async def coro():
            self.proto = await self.aclient
        asyncio.get_event_loop().run_until_complete(coro())

    def close(self):
        if not self.proto:
            logging.warning("SyncClient not connected")
        else:
            async def coro():
                await self.proto.close()
                self.proto = None
            asyncio.get_event_loop().run_until_complete(coro())


    # of course we can't inherit from the async class as-is
    # so let's wrap the async methods
    def __getattr__(self, method):
        #print(f"SyncClient resolving method {method}")
        if method not in dir(SidecarProtocol):
            raise AttributeError(f"no such method {method} in SidecarProtocol")
        def wrapper(*args, **kwds):
            async def coro():
                return await getattr(self.proto, method)(*args, **kwds)
            return asyncio.get_event_loop().run_until_complete(coro())
        return wrapper

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
