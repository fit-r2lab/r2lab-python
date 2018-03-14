from pathlib import Path


def r2lab_hostname(x, prefix='fit', incoming='fit'):
    """
    Return a valid hostname like ``fit01`` from an input that can be
    either ``1`` (int), ``1`` (str), ``01`` (str) , ``fit1`` or ``fit01``

    Args:
       x(str): loosely typed input that reflects node number
       prefix(str): if set, it is used instead of ``fit`` for building the output name
       incoming(str): if set, it is used instead of ``fit`` for filtering the incoming name.

    Examples:
       Simple use case::

           r2lab_hostname(1) == 'fit01'

       And::

           rl2ab_hostname('reboot1', incoming='reboot') == 'fit01'
    """
    return "{}{:02d}".format(prefix, int(str(x).replace(incoming, '')))


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
