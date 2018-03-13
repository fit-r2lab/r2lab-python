from unittest import TestCase

import time

from r2lab import R2labSidecar

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here
def enable_debug():
    import logging, logging.config
    logging.config.fileConfig('r2lab/logging-debug.conf')
    logger = logging.getLogger('socketIO-client')


class Tests(TestCase):

    # enable_debug()

    def test_prod(self):

        with R2labSidecar() as sidecar:
            nodes = sidecar.nodes_status()
        self.assertEqual(nodes[1]['available'], 'ok')
            
            
    # requirements to run this part:
    # a running local sidecar server (sidecar.js -l)
    def local(self):
        self.local_nodes()
        self.local_phones()

    def local_nodes(self):
        with R2labSidecar("http://localhost:10000/") as sidecar:
            sidecar.set_node_attribute(1, 'available', 'ok')
            nodes = sidecar.nodes_status()
            print("First fetch (expect available=ok) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ok')
        # reopen the connexion
        # this is safer because otherwise we may get an older result
        with R2labSidecar("http://localhost:10000/") as sidecar:
            sidecar.set_node_attribute('1', 'available', 'ko')
            sidecar.set_node_attribute('2', 'available', 'ok')
            nodes = sidecar.nodes_status()
            print("Second fetch (expect available=ko) {}".format(nodes[1]))
            self.assertEqual(nodes[1]['available'], 'ko')
        # ditto
        with R2labSidecar("http://localhost:10000/") as sidecar:
            sidecar.set_nodes_triples(
                ('2', 'available', 'ko'),
                ('3', 'cmc_on_off', 'off'),
                ('2', 'cmc_on_off', 'on'),
                )
            nodes = sidecar.nodes_status()
            print("Third fetch on node 2 (expect available=ko) {}".format(nodes[2]))
            self.assertEqual(nodes[2]['available'], 'ko')
        
    def local_phones(self):
        with R2labSidecar("http://localhost:10000/") as sidecar:
            sidecar.set_phone_attribute(1, 'airplane_mode', 'on')
            phones = sidecar.phones_status()
            print("First fetch (expect airplane_mode=on) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'on')
        # reopen the connexion
        # this is safer because otherwise we may get an older result
        with R2labSidecar("http://localhost:10000/") as sidecar:
            sidecar.set_phones_triples(
                ('1', 'airplane_mode', 'off'),
                ('2', 'airplane_mode', 'on')
            )
            phones = sidecar.phones_status()
            print("Second fetch on phone 1 (expect airplane_mode=off) {}".format(phones[1]))
            self.assertEqual(phones[1]['airplane_mode'], 'off')
            print("Second fetch on phone 2 (expect airplane_mode=on) {}".format(phones[2]))
            self.assertEqual(phones[2]['airplane_mode'], 'on')
        
