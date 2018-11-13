# pylint: disable=c0111

from unittest import TestCase

from r2lab.r2labmap import R2labMapGeneric, R2labMap

# this is for debug/devel, at the very least
# it needs the logging config file mentioned here


class Tests(TestCase):

    @staticmethod
    def _build_and_show(r2labmap, message):
        print(10 * '-', message)
        for index, (node, (gridx, gridy)) \
                in enumerate(r2labmap.iterate_nodes()):
            print(f"{node:02d} -> {gridx:02d} x {gridy:02d} | ", end="")
            if index % 5 == 4:
                print()
        print()
        for (gridx, gridy) in r2labmap.iterate_holes():
            print(f"H -> {gridx} x {gridy} | ", end="")
        print()

    def test_raw(self):
        themap = R2labMapGeneric()
        self._build_and_show(themap, "raw map")
        self.assertEqual(themap.position(1), (0, 0))
        self.assertEqual(themap.position(11), (2, 0))
        self.assertEqual(themap.position(37), (8, 4))
        self.assertEqual(themap.node(8, 4), 37)

    def test_usual(self):
        themap = R2labMap()
        self._build_and_show(themap, "standard map")
        self.assertEqual(themap.position(1), (1, 5))
        self.assertEqual(themap.position(11), (3, 5))
        self.assertEqual(themap.position(37), (9, 1))
