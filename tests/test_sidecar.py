# pylint: disable=missing-docstring

"""
uses a local server by default, run it with r2lab-sidecar --devel
these tests write in the sidecar, so tweak TEST_SERVER to use
the production server only if you really mean it

the attribute that we set on nodes is called TEST_FLAG; the sidecar has
no opinion on what attributes are, but one that is meaningful (like
cmc_on_off) would show up in the web interface
"""

from unittest import TestCase

import asyncio
# import websockets
# import json
# import logging

from r2lab import SidecarAsyncClient, SidecarSyncClient

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here

LOCAL_SERVER = "ws://localhost:10000/"
PROD_SERVER = "wss://r2lab-sidecar.inria.fr:443/"

TEST_SERVER = LOCAL_SERVER

TEST_FLAG = 'test_flag'

def not_status(ok_ko):
    return "".join(reversed(ok_ko))

def co_run(coro):
    with asyncio.Runner() as runner:
        return runner.run(coro)


    # return asyncio.get_event_loop().run_until_complete(coro)
    # if I do any of these 2 I transform 1 warning into 3 errors !
    # return asyncio.run(coro)

class Tests(TestCase):


    async def co_ping(self):

        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            nodes = await sidecar.nodes_status()
        self.assertIsInstance(nodes, dict)

    def test_async_ping(self):
        co_run(self.co_ping())


    DELAY = 0.3

    async def co_nodes(self):

        # one connection, one message
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, TEST_FLAG, 'ok')

        await asyncio.sleep(self.DELAY)
        # reopen the connexion
        # one connection, several messages
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, TEST_FLAG, 'ko')
            await asyncio.sleep(self.DELAY)
            await sidecar.set_node_attribute(1, TEST_FLAG, 'ok')
            await asyncio.sleep(self.DELAY)
            await sidecar.set_node_attribute(1, TEST_FLAG, 'ko')

        await asyncio.sleep(self.DELAY)
        # set attribute and check consistency
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, TEST_FLAG, 'ok')
            nodes = await sidecar.nodes_status()
#            print("First fetch (expect test_flag=ok) {}".format(nodes[1]))
            self.assertEqual(nodes[1][TEST_FLAG], 'ok')

        await asyncio.sleep(self.DELAY)
        # a little more complex
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_node_attribute('1', TEST_FLAG, 'ko')
            await sidecar.set_node_attribute('2', TEST_FLAG, 'ok')
            nodes = await sidecar.nodes_status()
#            print("Second fetch (expect test_flag=ko) {}".format(nodes[1]))
            self.assertEqual(nodes[1][TEST_FLAG], 'ko')
            self.assertEqual(nodes[2][TEST_FLAG], 'ok')

    def test_async_nodes(self):
        co_run(self.co_nodes())



    async def co_phones(self):
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_phone_attribute(1, 'airplane_mode', 'on')
            phones = await sidecar.phones_status()
            print(f"First fetch (expect airplane_mode=on) {phones[1]}")
            self.assertEqual(phones[1]['airplane_mode'], 'on')

        await asyncio.sleep(self.DELAY)
        # reopen the connexion
        # this is safer because otherwise we may get an older result
        async with SidecarAsyncClient(TEST_SERVER) as sidecar:
            await sidecar.set_phones_triples(
                ('1', 'airplane_mode', 'off'),
                ('2', 'airplane_mode', 'on')
            )
            phones = await sidecar.phones_status()
            print(
                f"Second fetch on phone 1 (expect airplane_mode=off) {phones[1]}")
            self.assertEqual(phones[1]['airplane_mode'], 'off')
            print(
                f"Second fetch on phone 2 (expect airplane_mode=on) {phones[2]}")
            self.assertEqual(phones[2]['airplane_mode'], 'on')

    def test_async_phones(self):
        co_run(self.co_phones())


    ### sync client - lighter tests as it relies on the async code

    def test_ping_iter(self):
        client = SidecarSyncClient(TEST_SERVER)
        client.connect()
        nodes = client.nodes_status()
        self.assertIsInstance(nodes, dict)
        client.close()


    def test_ping_with(self):
        with SidecarSyncClient(TEST_SERVER) as client:
            nodes = client.nodes_status()
        self.assertIsInstance(nodes, dict)


    def test_nodes(self):
        client = SidecarSyncClient(TEST_SERVER)
        client.connect()
        nodes = client.nodes_status()
        start = nodes.get(1, {}).get(TEST_FLAG, 'ok')
        not_start = not_status(start)
        # invert
        client.set_node_attribute(1, TEST_FLAG, not_start)
        nodes1 = client.nodes_status()
        self.assertEqual(nodes1[1][TEST_FLAG], not_start)
        # put back
        client.set_node_attribute(1, TEST_FLAG, not_start)
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
        self.assertIn(1, nodes)
    def prod_status(self):
        co_run(self.co_prod_status())
