# pylint: disable=w1203

# requirements to run this part:
# a running local sidecar server (sidecar.py)


from unittest import TestCase

import asyncio
import websockets
import json
import logging

from r2lab import SidecarAsyncClient, SidecarSyncClient

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here

LOCAL_SERVER = "ws://localhost:10000/"
PROD_SERVER = "wss://r2lab.inria.fr:999/"

def not_status(ok_ko):
    return "".join(reversed(ok_ko))

def co_run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)

class Tests(TestCase):


    async def co_ping(self):

        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            nodes = await sidecar.nodes_status()
        self.assertIn(nodes[1]['available'], {'ok', 'ko'})

    def test_async_ping(self):
        co_run(self.co_ping())


    DELAY = 0.3

    async def co_nodes(self):

        # one connection, one message
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ok')

        await asyncio.sleep(self.DELAY)
        # reopen the connexion
        # one connection, several messages
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ko')
            await asyncio.sleep(self.DELAY)
            await sidecar.set_node_attribute(1, 'available', 'ok')
            await asyncio.sleep(self.DELAY)
            await sidecar.set_node_attribute(1, 'available', 'ko')

        await asyncio.sleep(self.DELAY)
        # set attribute and check consistency
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ok')
            nodes = await sidecar.nodes_status()
#            print("First fetch (expect available=ok) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ok')

        await asyncio.sleep(self.DELAY)
        # a little more complex
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute('1', 'available', 'ko')
            await sidecar.set_node_attribute('2', 'available', 'ok')
            nodes = await sidecar.nodes_status()
#            print("Second fetch (expect available=ko) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ko')
            self.assertEqual(nodes[2]['available'], 'ok')

    def test_async_nodes(self):
        co_run(self.co_nodes())



    async def co_phones(self):
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_phone_attribute(1, 'airplane_mode', 'on')
            phones = await sidecar.phones_status()
            print("First fetch (expect airplane_mode=on) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'on')

        await asyncio.sleep(self.DELAY)
        # reopen the connexion
        # this is safer because otherwise we may get an older result
        async with SidecarAsyncClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_phones_triples(
                ('1', 'airplane_mode', 'off'),
                ('2', 'airplane_mode', 'on')
            )
            phones = await sidecar.phones_status()
            print(
                "Second fetch on phone 1 (expect airplane_mode=off) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'off')
            print(
                "Second fetch on phone 2 (expect airplane_mode=on) {}".format(phones[2]))
            self.assertEqual(phones[2]['airplane_mode'], 'on')

    def test_async_phones(self):
        co_run(self.co_phones())


    ### sync client - lighter tests as it relies on the async code

    def test_ping_iter(self):
        client = SidecarSyncClient(LOCAL_SERVER)
        client.connect()
        nodes = client.nodes_status()
        self.assertIn(nodes[1]['available'], {'ok', 'ko'})
        client.close()


    def test_ping_with(self):
        with SidecarSyncClient(LOCAL_SERVER) as client:
            nodes = client.nodes_status()
        self.assertIn(nodes[1]['available'], {'ok', 'ko'})


    def test_nodes(self):
        client = SidecarSyncClient(LOCAL_SERVER)
        client.connect()
        nodes = client.nodes_status()
        start = nodes[1]['available']
        not_start = not_status(start)
        # invert
        client.set_node_attribute(1, 'available', not_start)
        nodes1 = client.nodes_status()
        self.assertEqual(nodes1[1]['available'], not_start)
        # put back
        client.set_node_attribute(1, 'available', not_start)
        client.close()



    def sync(self):
        self.test_ping_iter()
        self.test_ping_with()
        self.test_nodes()

    ### SHOULD be automatic (start with test_)
    # once we have deployed on r2lab


    async def co_prod_status(self):
        async with SidecarAsyncClient(PROD_SERVER) as sidecar:
            nodes = sidecar.nodes_status()
        self.assertEqual(nodes[1]['available'], 'ok')
    def prod_status(self):
        co_run(self.co_prod_status())
