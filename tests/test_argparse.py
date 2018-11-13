import unittest

import argparse

from r2lab import ListOfChoices, ListOfChoicesNullReset


class Tests(unittest.TestCase):

    def test1(self):
        """
        ListOfChoices micro-test for antennas-like
        """
        def p():
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument("-a", "--antenna-mask", default=['1', '1'],
                                choices=['1', '3', '7', '11'],
                                dest='antennas',
                                action=ListOfChoices,
                                help="specify antenna mask for each node")
            return parser

        # with no argument, use sys.argv, which in our case is
        # the call to nosetest
        #self.assertListEqual(p().parse_args().antennas, ['1', '1'])
        self.assertListEqual(p().parse_args([]).antennas, ['1', '1'])
        self.assertListEqual(p().parse_args(['-a', '1']).antennas, ['1'])
        self.assertListEqual(p().parse_args(
            ['-a', '1', '-a', '3']).antennas, ['1', '3'])
        self.assertListEqual(p().parse_args(
            ['-a', '1', '-a', '3', '-a', '11']).antennas, ['1', '3', '11'])

    def test2(self):
        """
        ListOfChoices micro-test for phones-like
        """
        def p():
            parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
            parser.add_argument("-p", "--phones", default=[1],
                                choices=(1, 2, 3, 0),
                                type=int,
                                action=ListOfChoicesNullReset,
                                help="specify phones")
            return parser

        # ditto
        #self.assertEqual(p().parse_args().phones, [1])
        self.assertListEqual(p().parse_args([]).phones, [1])
        self.assertListEqual(p().parse_args(['-p', '1']).phones, [1])
        self.assertListEqual(p().parse_args(['-p', '1', '-p', '2']).phones, [1, 2])
        self.assertListEqual(p().parse_args(
            ['-p', '1', '-p', '3', '-p', '2']).phones, [1, 3, 2])
        self.assertListEqual(p().parse_args(['-p', '0']).phones, [])


if __name__ == '__main__':
    unittest.main()
