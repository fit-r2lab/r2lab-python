"""
The r2lab package
"""

from .version import version as __version__

from .utils import (
    r2lab_hostname,
    r2lab_reboot,
    r2lab_data,
    r2lab_parse_slice,
    find_local_embedded_script,
)

from .argparse_additions import (
    ListOfChoices,
    ListOfChoicesNullReset,
)

from .r2labmap import R2labMap, BokehR2labMap

# protect for install-time when dependencies are not yet installed
try:
    import socketIO_client
    from .sidecar import R2labSidecar
except ModuleNotFoundError:
    print("Warning: could not import module socketIO_client")
