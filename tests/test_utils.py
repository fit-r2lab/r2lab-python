import unittest

from pathlib import Path

from r2lab import (
    r2lab_hostname,
    r2lab_reboot,
    r2lab_data,
    r2lab_parse_slice,
    find_local_embedded_script,
)

class Tests(unittest.TestCase):

    def test_hostname(self):
        self.assertEqual(r2lab_hostname(1), 'fit01')
        self.assertEqual(r2lab_hostname('1'), 'fit01')
        self.assertEqual(r2lab_hostname('01'), 'fit01')
        self.assertEqual(r2lab_hostname('001'), 'fit01')
        self.assertEqual(r2lab_hostname('fit1'), 'fit01')
        self.assertEqual(r2lab_hostname('fit01'), 'fit01')
        self.assertEqual(r2lab_hostname('fit001'), 'fit01')
        self.assertEqual(r2lab_hostname(33), 'fit33')
        self.assertEqual(r2lab_hostname('33'), 'fit33')
        self.assertEqual(r2lab_hostname('033'), 'fit33')
        self.assertEqual(r2lab_hostname('0033'), 'fit33')
        self.assertEqual(r2lab_hostname('fit33'), 'fit33')
        self.assertEqual(r2lab_hostname('fit033'), 'fit33')
        self.assertEqual(r2lab_hostname('fit0033'), 'fit33')

        self.assertEqual(r2lab_hostname('reboot1'), 'fit01')

        self.assertEqual(r2lab_reboot('fit001'), 'reboot01')
        self.assertEqual(r2lab_reboot('reboot0000001'), 'reboot01')
        self.assertEqual(r2lab_reboot(1), 'reboot01')

        self.assertEqual(r2lab_data('fit001'), 'data01')
        self.assertEqual(r2lab_data('data0000001'), 'data01')
        self.assertEqual(r2lab_data(1), 'data01')


    def test_parse_slice(self):
        self.assertEqual(r2lab_parse_slice('inria_foo'),
                         ('inria_foo', 'faraday.inria.fr'))
        self.assertEqual(r2lab_parse_slice('inria_foo@faraday.inria.fr'),
                         ('inria_foo', 'faraday.inria.fr'))
        self.assertEqual(r2lab_parse_slice('inria_foo@etourdi.pl.sophia.inria.fr'),
                         ('inria_foo', 'etourdi.pl.sophia.inria.fr'))

    def test_find_local_embedded_script(self):
        self.assertEqual(
            find_local_embedded_script("oai-enb.sh"),
            str(Path.home() / 'git' / 'r2lab-embedded' / 'shell' / 'oai-enb.sh'))
        self.assertIsNone(
            find_local_embedded_script("inexistent"))



if __name__ == '__main__':
    unittest.main()
