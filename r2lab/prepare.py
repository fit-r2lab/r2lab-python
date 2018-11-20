"""
This module contains a utility for preparing the testbed.

The logic is that you write a scheduler that implements your
pure experimental logic.

You can then pass this scheduler to ``r2lab_prepare_scheduler()``,
that returns a scheduler where your original one is embedded.

This overall scheduler will prepend instructions for preparing the testbed,
in terms of loading images on nodes, turning off unused nodes, and similar.
"""

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, RunScript

from .utils import PHONES, r2lab_id, find_local_embedded_script

INCLUDES = [find_local_embedded_script(x)
            for x in ("faraday.sh", "r2labutils.sh")]

# how to run something on all nodes but a specified list
# be flexible on how to specify that list
# e.g _rhubarbe_command('off', ['fit1', 'fit02', 5, '10', b'12'])
# => "rhubarbe off --all ~1 ~2 ~5 ~10 ~12"
def _rhubarbe_command(verb, left_alone):
    result = "rhubarbe {} --all".format(verb)
    for node in left_alone:
        result += " ~{}".format(node)
    return result


def prepare_testbed_scheduler(                   # pylint: disable=r0913, r0914
        gateway: SshNode,
        load_flag: bool,
        experiment_scheduler: Scheduler,
        images_mapping,
        nodes_left_alone=None,
        sdrs_left_alone=None,
        phones_left_alone=None,
        verbose_jobs=False):
    """

    This function is designed as a standard way for experiments to warm up.
    Experimenters only need to write a scheduler that defines the behaviour
    of their core experiment, this function will add additional steps that
    take care of a) checking for a valid lease, b) load images on nodes, and
    c) turn off unused devices.

    It is generally desirable to write an experiment script that has a
    `--load/-l` boolean flag; typically, one would use the ``--load`` flag the
    first time that an experiment is launched during a given timeslot, while
    subsequent calls won't. That is the purpose of the ``load_flag`` below;
    when set to False, only step a) is performed, otherwise the resulting
    scheduler will go for the full monty.

    Parameters:
      gateway_sshnode: the ssh handle to the gateway
      load_flag(bool): if not set, only the lease is checked
      experiment_scheduler: core scheduler for the experiment
      images_mapping: a dictionary that specifies images to be loaded on nodes;
        see examples below
      nodes_left_alone: a list of node numbers that should be left intact,
        neither loaded nor turned off;
      phones_left_alone: a list of node numbers that should be left intact,
        i.e. not switched to airplane mode.

    Return :
      The overall scheduler where the input ``experiment_scheduler`` is embedded.

    Examples:
      Specify a mapping like the following::

          images_mapping = { "ubuntu" : [1, 4, 5], "gnuradio": [16]}

      Note that the format for ``images_mapping``, is flexible;
      if only one node is to be loaded, the iterable level is optional;
      also each node can be specified as an ``int``, a ``bytes``, a ``str``,
      in which case non numeric characters are ignored. So this is a legitimate
      requirement as well::

        images_mapping = { 'openair-cn': 12 + 4,
                           'openair-enodeb': ('fit32',),
                           'ubuntu': {12, 'reboot1', '004',
                                      'you-get-the-picture-34'}
        }
    """

    # handle default mutable args
    nodes_left_alone = set(nodes_left_alone) if nodes_left_alone else set()
    sdrs_left_alone = set(sdrs_left_alone) if sdrs_left_alone else set()
    phones_left_alone = set(phones_left_alone) if phones_left_alone else set()

    scheduler = Scheduler(label="Preparation")

    check_lease = SshJob(
        scheduler=scheduler,
        node=gateway,
        verbose=verbose_jobs,
        label="Check lease {}".format(gateway.username),
        command=Run("rhubarbe leases --check", label="rlease"),
    )

    # if no image loading is requested, we're done here
    if not load_flag:
        scheduler.add(experiment_scheduler)
        experiment_scheduler.requires(check_lease)
        return scheduler

    # otherwise, we want to do in parallel
    # (*) as many image-loading jobs as we have entries in images_mapping
    # (*) one job to turn off phones, nodes and usrps
    #     as parallelizing brings no speed up at all

    # todo ideally we could also probe the testbed to figure out which nodes
    # are currently unavailable, and let them alone as well; but well.

    # the jobs that we need to wait for before going on with the real stuff
    octopus = []

    loaded_nodes = set()

    for image, nodes in images_mapping.items():
        # let's be as flexible as possible
        # (1) empty node list should be fine
        if not nodes:
            continue
        # (2) atomic types should be allowed
        if isinstance(nodes, (int, str, bytes)):
            nodes = [nodes]
        # (3) accept all forms of inputs
        nodes = {r2lab_id(node) for node in nodes}
        duplicates = loaded_nodes & nodes
        if duplicates:
            print("WARNING - nodes in {} have been assigned several images"
                  .format(duplicates))
        loaded_nodes.update(nodes)
        # for there on we need strings
        node_args = " ".join(str(node) for node in nodes)
        octopus.append(
            SshJob(
                gateway,
                scheduler=scheduler,
                required=check_lease,
                label=("loading {} on {}"
                       .format(image, node_args)),
                commands=[
                    Run("rhubarbe load -i {} {}"
                        .format(image, node_args)),
                    Run("rhubarbe wait {}" .format(node_args)),
                ],
                verbose=verbose_jobs,
                ))

    ### turn off stuff
    # nodes
    dont_off_nodes = nodes_left_alone | loaded_nodes
    # do turn off usrp device even on loaded nodes
    dont_off_sdrs = sdrs_left_alone
    # phones - there's no equivalent of --all ~ notation with phones
    off_phones = set(range(1, PHONES+1)) \
                 - {r2lab_id(ph) for ph in phones_left_alone}

    if off_phones:
        octopus.append(
            SshJob(
                gateway,
                scheduler=scheduler,
                required=check_lease,
                critical=False,
                commands=[
                    RunScript(
                        find_local_embedded_script("faraday.sh"),
                        "macphone{}".format(phone),
                        "r2lab-embedded/shell/macphone.sh", "phone-off",
                        label="turn off phone {}".format(phone),
                        includes=INCLUDES)
                    for phone in off_phones],
                verbose=verbose_jobs)
            )


    octopus.append(
        SshJob(gateway,
               scheduler=scheduler,
               required=check_lease,
               label="Turn off unused devices",
               commands=[
                   Run(_rhubarbe_command(verb="off", left_alone=dont_off_nodes)),
                   Run(_rhubarbe_command(verb="usrpoff", left_alone=dont_off_sdrs)),
               ],
               verbose=verbose_jobs,
               ))

    # embed experiment scheduler
    experiment_scheduler.requires(octopus)
    scheduler.add(experiment_scheduler)

    return scheduler
