# pylint: disable=w1203

from unittest import TestCase

import asyncio
import websockets
import json
import logging

from r2lab import SidecarClient

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here

LOCAL_SERVER = "ws://localhost:10000/"

class Tests(TestCase):

    async def co_local_nodes(self):

        # one connection, one message
        async with SidecarClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ok')
        await sidecar.wait_closed()

        # reopen the connexion
        # one connection, several messages
        async with SidecarClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ko')
            await asyncio.sleep(0.2)
            await sidecar.set_node_attribute(1, 'available', 'ok')
            await asyncio.sleep(0.2)
            await sidecar.set_node_attribute(1, 'available', 'ko')
        await sidecar.wait_closed()

        async with SidecarClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute(1, 'available', 'ok')
            nodes = await sidecar.nodes_status()
            print("First fetch (expect available=ok) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ok')
        await sidecar.wait_closed()

        async with SidecarClient(LOCAL_SERVER) as sidecar:
            await sidecar.set_node_attribute('1', 'available', 'ko')
            await sidecar.set_node_attribute('2', 'available', 'ok')
            nodes = await sidecar.nodes_status()
            print("Second fetch (expect available=ko) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ko')
            self.assertEqual(nodes[2]['available'], 'ok')
        await sidecar.wait_closed()

    def local_nodes(self):
        return (asyncio.get_event_loop()
                .run_until_complete(self.co_local_nodes()))




    # not async'ed yet
    def test_prod(self):

        with SidecarClient(debug=True) as sidecar:
            nodes = sidecar.nodes_status()
        self.assertEqual(nodes[1]['available'], 'ok')

    def local_simplest(self):

        with SidecarClient(LOCAL_SERVER, debug=True) as sidecar:
            nodes = sidecar.nodes_status()
        self.assertEqual(nodes[1]['available'], 'ok')

    # requirements to run this part:
    # a running local sidecar server (sidecar.js -l)
    def local(self):
        self.local_nodes()
        self.local_phones()

    def local_phones(self):
        with SidecarClient(LOCAL_SERVER) as sidecar:
            sidecar.set_phone_attribute(1, 'airplane_mode', 'on')
            phones = sidecar.phones_status()
            print("First fetch (expect airplane_mode=on) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'on')
        # reopen the connexion
        # this is safer because otherwise we may get an older result
        with SidecarClient(LOCAL_SERVER) as sidecar:
            sidecar.set_phones_triples(
                ('1', 'airplane_mode', 'off'),
                ('2', 'airplane_mode', 'on')
            )
            phones = sidecar.phones_status()
            print(
                "Second fetch on phone 1 (expect airplane_mode=off) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'off')
            print(
                "Second fetch on phone 2 (expect airplane_mode=on) {}".format(phones[2]))
            self.assertEqual(phones[2]['airplane_mode'], 'on')
