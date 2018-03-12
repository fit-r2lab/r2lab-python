from unittest import TestCase

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
            
            
    # cannot know in advance the result, as with animate it changes all the time
    # xxx would make sense to change something first
    def local_nodes(self):
        with R2labSidecar("http://localhost:10000/") as sidecar:
            nodes = sidecar.nodes_status()
        for id, node in nodes.items():
            print("local server: nodes[{}] = {}".format(id, node))
        
