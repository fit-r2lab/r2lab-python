import re

from pathlib import Path

PHONES = 2

def r2lab_id(anything):
    """
    Returns an integer from an input that can be either ``1`` (int),
    ``1`` (str), b``1``(bytes), ``01`` (str) ,
    ``fit1``, ``fit01`` or even ``reboot01``.
    """
    if isinstance(anything, bytes):
        anything = anything.decode(encoding='utf-8')
    if isinstance(anything, str):
        # ignore all but digits
        anything = re.sub(r'[^0-9]', '', anything)
    return int(anything)


def _r2lab_name(anything, prefix='fit'):
    return "{}{:02d}".format(prefix, r2lab_id(anything))


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
    """
    This helper is designed to find a script that typically comes with
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

    Raises:
        ``FileNotFoundError(script)`` if script can't be found

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
        Path.home() / "fit-r2lab",
        # when in r2lab-demos/one-demo
        Path("../../"),
        # when in r2lab-demos
        Path(".."),
        Path("."),
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
    raise FileNotFoundError(script)
