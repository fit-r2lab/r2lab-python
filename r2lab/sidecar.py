#!/usr/bin/env python3

"""
The R2lab sidecar is a websocket service that runs on
``wss://r2lab-sidecar.inria.fr:443/`` and that exposes the status of the testbed.

This module implements client classes, for interacting with the sidecar service.

The core of the implementation is ``asyncio``-friendly and accessible
through the :class:`~r2lab.sidecar.SidecarAsyncClient` class, but for
convenience some features are also available to synchronous code through
the :class:`~r2lab.sidecar.SidecarSyncClient` class.
"""

# pylint: disable=keyword-arg-before-vararg, logging-fstring-interpolation

import logging
import asyncio

# support for ws>=14 only
import websockets
import websockets.asyncio.client as ws_client

from .sidecar_payload import SidecarPayload as Payload


DEFAULT_SIDECAR_URL = 'wss://r2lab-sidecar.inria.fr:443/'

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


class SidecarConnection(ws_client.ClientConnection):

    """
    The SidecarClient class is an asyncio-compliant implementation
    of the R2lab sidecar system.

    It inherits ``websockets.client.WebSocketClientConnection``
    from websockets 14
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
    def _is_incremental(umbrella):
        return umbrella.get('incremental', None)

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
                    and not self._is_incremental(umbrella)):
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

    async def set_node_attribute(self, id_, attribute, value):
        """
        Parameters:
            id: a node_id as an int or str
            attribute(str): the name of the attribute to be written
            value(str): the new value

        Example:
            To mark node 1 as unavailable::

                await sidecar.set_node_attribute(1, 'available', 'ko')
        """
        return await self.set_nodes_triples((id_, attribute, value))


    # phones

    async def phones_status(self):
        "Just like ``nodes_status`` but on phones"
        return await self._probe_category('phones')

    async def set_phones_triples(self, *triples):
        "Identical to ``set_nodes_triples`` but on phones"
        return await self._set_triples('phones', triples)

    async def set_phone_attribute(self, id_, attribute, value):
        """
        Similar to ``set_node_attribute`` on a phone

        Example:
            To mark phone 2 as being turned off (although this is constantly
            recomputed by the phones monitor)::

                await sidecar.set_phone_attribute(2, 'airplane_mode', 'on')
        """
        return await self.set_phones_triples((id_, attribute, value))



class SidecarAsyncClient(websockets.connect):

    """
    This class behaves as an asynchronous context manager for
    talking with the R2lab sidecar server.

    Optional arguments `args` and `kwds` are passed as-is to
    `websockets.client.connect`, see
    https://websockets.readthedocs.io/en/stable/reference/asyncio/client.html#opening-a-connection

    Example:
        Set a node as available from some asynchronous code::

            async with SidecarAsyncClient() as sidecar:
                await sidecar.set_node_attribute(1, 'available', 'ok')

        In this example, the ``sidecar`` object is
        a :class:`~r2lab.sidecar.SidecarConnection` instance.

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

    def __init__(self, url=DEFAULT_SIDECAR_URL, *args, **kwds):
        if 'create_connection' in kwds:
            logging.error("should not overwrite create_connection")
        super().__init__(url, create_connection=SidecarConnection,
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

    def __init__(self, url=DEFAULT_SIDECAR_URL, *args, **kwds):
        self.aclient = SidecarAsyncClient(url, *args, **kwds)
        self.runner = asyncio.Runner()
        self.connection = None

    def connect(self):
        """
        Connect to the sidecar server
        """
        if self.connection:
            logging.warning("SyncClient already connected")
        async def coro():
            self.connection = await self.aclient
        self.runner.run(coro())

    def close(self):
        """
        Close the connection to the sidecar server
        """
        if not self.connection:
            logging.warning("SyncClient not connected")
        else:
            async def coro():
                await self.connection.close()
                self.connection = None
            self.runner.run(coro())
            self.runner.close()

    # of course we can't inherit from the async class as-is
    # so let's wrap the async methods
    def __getattr__(self, method):
        #print(f"SyncClient resolving method {method}")
        if method not in dir(SidecarConnection):
            raise AttributeError(f"no such method {method} in SidecarConnection")
        def wrapper(*args, **kwds):
            async def coro():
                return await getattr(self.connection, method)(*args, **kwds)
            return self.runner.run(coro())
        return wrapper

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()
