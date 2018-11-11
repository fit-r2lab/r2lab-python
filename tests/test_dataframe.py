# pylint: disable=c0111, r0201
from unittest import TestCase

from r2lab import R2labMap, MapDataFrame

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here


class Tests(TestCase):

    def test_build(self):

        r2labmap = R2labMap()
        r2df = MapDataFrame(r2labmap,
                            columns={'foo': 1, 'bar': 'bardef'})
        print(r2df)
