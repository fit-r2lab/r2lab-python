import re

from pathlib import Path

from asynciojobs import Scheduler
from apssh import SshNode, SshJob, Run, TimeColonFormatter

def _r2lab_name(x, prefix='fit'):
    if isinstance(x, bytes):
        x = x.decode(encoding='utf-8')
    if isinstance(x, str):
        # ignore all but digits
        x = re.sub(r'[^0-9]', '', x)
    x = int(x)
    return "{}{:02d}".format(prefix, x)


def r2lab_hostname(x):
    """
    Return a valid hostname like ``fit01`` from an input that can be
    either ``1`` (int), ``1`` (str), ``01`` (str) , ``fit1``, ``fit01`` or even ``reboot01``.

    Args:
       x(str): loosely typed input that reflects node number

    Examples:
       Simple use case::

           r2lab_hostname(1) == 'fit01'

       And::

           rl2ab_hostname('reboot1') == 'fit01'
    """
    return _r2lab_name(x, prefix='fit')

def r2lab_reboot(x):
    """
    Same as ``r2lab_hostname`` but returns a hostname of the form ``reboot01``.
    """
    return _r2lab_name(x, prefix='reboot')

def r2lab_data(x):
    """
    Same as ``r2lab_hostname`` but returns an interface name of the form ``data01``.
    """
    return _r2lab_name(x, prefix='data')


def r2lab_parse_slice(slice):
    """
    returns username and hostname from a slice.

    Args:
        slice(str): can be either ``username@hostname`` or just ``username``.
           In the latter case the hostname defaults to
           the R2lab gateway i.e. ``faraday.inria.fr``

    Returns:
        tuple: ``slice``, ``hostname``

    Example:
        Typical usage is::

            slice, hostname = r2lab_parse_slice("inria_r2lab.tutorial")

            slice, hostname = r2lab_parse_slice("inria_r2lab.tutorial@faraday.inria.fr")

    """
    if slice.find('@') > 0:
        user, host = slice.split('@')
        return user, host
    else:
        return slice, "faraday.inria.fr"


def find_local_embedded_script(script, extra_paths=None):
    """This helper is designed to find a script that typically comes with
    the ``r2lab-embedded`` repo, specifically in its ``shell``
    subdirectory.

    It knows of a few heuristics to locate your ``r2lab-embedded``
    repo, relative to your home and current directories. You can
    specify additional places to search for in ``extra_paths``

    Args:
        script(str): the simple name of a script to find
        extra_paths(List(str)): optional, a list of paths
           (can be ``Path`` instances too) where to search too

    Returns:
        str: a valid path in the local filesystem, or ``None``


    Example:
        Search for ``oai-enb.sh`` so as to run it remotely::

            local_script = find_local_embedded_script("oai-enb.sh")
            RunScript(localscript, ...)

    Note:

        Should this also look for some env. variable ?

    """
    heuritics = [
        # for people who have their git root in $HOME
        Path.home(),
        # for people who have their git root in ~/git
        Path.home() / "git",
        # when in r2lab-demos/one-demo
        Path("../../"),
        # when in r2lab-demos
        Path(".."),
    ]

    # convert extra paths into Paths
    if extra_paths is not None:
        heuritics += [Path(path) for path in extra_paths]

    # several chances each time
    relatives = ['r2lab-embedded/shell', 'shell', '.']

    for path in heuritics:
        for relative in relatives:
            candidate = path / relative / script
            if candidate.exists():
                return str(candidate)
    print("WARNING: could not find local embedded script {}".format(script))
    for path in heuritics:
        for relative in relatives:
            print("W: searched in {}".format(path / relative))

class r2labFalseStartError(Exception):
    """Personal exception that is raise if there is a problem when using
        "generate_experiment_header"
    """
    pass

def load_option(image="_default", timeout=300, bandwidth=500, curses=False,
                no_reset=True):
    """
    Wrapper to generate correct tupple use in the generate_experiment_header
    """
    image_load = ""
    if image != "_default":
        image_load = "-i "+image
    return image_load

def generate_experiment_header(slicename=None,
                               dic_node_image=None, list_sdr_on=None,
                               verbose_jobs=False, verbose_ssh=False,
                               formatter=TimeColonFormatter()):
    """ This helper is designed to populate a scheduler with element usefull
    at the start of an experiment. It allows the user to avoid the complicated
    synthax problem with rhubarbe on faraday.


    Argument :
    -slicename : Name of your slice on faraday (it is mandatory),
    -dic_node_image : A dictionary used to precise which node you want to turn
                      on.
                      It should be formated : {node_identifier : image_name}
                      -node_identifier is anything that cas identify a node,
                       like ''1''(int), ''1''(string), '01', 'fit1', etc...
                      -image_name is the name of the image you want to load
                       on this node. None and "" are the default image
    -list_sdr_on : List node_identifier attached to an sdr you want to turn
                    on
    -verbose_jobs : Enable/disable verbose mode on jobs.
    -verbose_ssh : Enable/disable verbose mode on ssh.
    -formatter : The colon formater you want to use on your node.

    Return :
     The scheduler containing the generated experiment header
     (checklease, on nodes, load images, sdr on)
    """
    scheduler = Scheduler(label="Experiment Header")
    if not slicename:
        raise r2labFalseStartError("No slice name given to check if you have"
                                     " a valid lease.")

    # Declaring nodes
    faraday = SshNode(hostname="faraday.inria.fr", username=slicename,
                      formatter=formatter, verbose=verbose_ssh)

    #Job to check lease
    check_lease = SshJob(
        scheduler=scheduler,
        node=faraday,
        verbose=verbose_jobs,
        label="Check lease {}".format(slicename),
        command=Run("rhubarbe leases --check", label="rlease"),
    )

    if dic_node_image:
        load_sched = Scheduler(required=check_lease,
                               scheduler=scheduler,
                               label="Load Scheduler")
        dic_load = {}
        negated_node_ids = []
        node_ids = []
        for id, image in dic_node_image.items():
            negated_node_ids.append("~{}".format(r2lab_hostname(id)))
            node_ids.append("{}".format(r2lab_hostname(id)))
            if image is None or image == "":
                image = "_default"

            try:
                dic_load[image].append(r2lab_hostname(id))
            except KeyError:
                dic_load[image] = [r2lab_hostname(id)]
        off_job = SshJob(
                         node=faraday,
                         scheduler=load_sched,
                         verbose=verbose_jobs,
                         label="rhubarbe off {}"
                         .format(negated_node_ids),
                         command=Run("rhubarbe-off -a ", *negated_node_ids,
                                     label="turn off every nodes except {}"
                                     .format(" ".join(node_ids))
                                     )
                        )
        load_jobs = [SshJob(
                            node=faraday,
                            verbose=verbose_jobs,
                            label="rhubarbe load {} image to {}"
                            .format(image, " ".join(ids)),
                            command=Run("rhubarbe-load {} {}"
                                        .format(load_option(image),
                                                " ".join(ids)),
                                        label="load {} on {}"
                                        .format(image, ", ".join(ids))
                                        )
                            )
                     for image, ids in dic_load.items()]
        load_job = Scheduler(
                                *load_jobs,
                                required=off_job,
                                scheduler=load_sched,
                                label="image loading"
                                )
        wait_job = SshJob(
                          node=faraday,
                          scheduler=load_sched,
                          required=load_job,
                          verbose=verbose_jobs,
                          label="rhubarbe wait {}".format(" ".join(node_ids)),
                          command=Run("rhubarbe-wait ", *node_ids,
                                      label="rwait")
                          )
    if list_sdr_on:

        sdr_sched = Scheduler(required=check_lease,
                               scheduler=scheduler,
                               label="Turn on sdr")
        negated_sdr = []
        sdrs = []
        for sdr in list_sdr_on:
            negated_sdr.append("~{}".format(r2lab_hostname(sdr)))
            sdrs.append("{}".format(r2lab_hostname(sdr)))
        sdroff_job = SshJob(
                             node=faraday,
                             scheduler=sdr_sched,
                             verbose=verbose_jobs,
                             label="rhubarbe-sdroff {}"
                             .format(negated_sdr),
                             command=Run("rhubarbe-usrpoff -a ", *negated_sdr,
                                         label="turn off every sdr except {}"
                                         .format(" ".join(sdrs))
                                         )
                             )
        sdron_job = SshJob(
                             node=faraday,
                             scheduler=sdr_sched,
                             required=sdroff_job,
                             verbose=verbose_jobs,
                             label="rhubarbe-sdron {}"
                             .format(sdrs),
                             command=Run("rhubarbe-usrpon", *sdrs,
                                         label="turn on sdr {}"
                                         .format(" ".join(sdrs))
                                         )
                             )
    return scheduler
