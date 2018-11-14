# pylint: disable=c0111
from unittest import TestCase

from asynciojobs import Scheduler, PrintJob

from apssh import SshNode

from r2lab.prepare import prepare_testbed_scheduler

class Tests(TestCase):

    @staticmethod
    def dummy_exp():
        return Scheduler(PrintJob("Hello", "World", label="hello"),
                         label="scheduler"
                         )

    @staticmethod
    def dummy_node():
        return SshNode("faraday.inria.fr", username="slicename")

    def test_noload(self):

        overall = prepare_testbed_scheduler(
            gateway=self.dummy_node(),
            load_flag=False,
            experiment_scheduler=self.dummy_exp(),
            images_mapping={"ubuntu": 1})

        # xxx doing visual verifications for now
        overall.export_as_pngfile("tests/prepare_noload")

    def test_load(self):

        overall = prepare_testbed_scheduler(
            gateway=self.dummy_node(),
            load_flag=True,
            experiment_scheduler=self.dummy_exp(),
            images_mapping={"ubuntu": 1,
                            # this kind of dups dont matter
                            "fedora": (2, '02', b'003', 'fit004', 'r5'),
                            "gnuradio": 'fit25',
                            # this is a bigger deal
                            "duplicate": 3,
                            })

        # xxx doing visual verifications for now
        overall.export_as_pngfile("tests/prepare_load")
