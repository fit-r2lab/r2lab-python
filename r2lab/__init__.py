"""
The r2lab package

Same order as API.rst
"""

from .version import __version__

# use try/expect to protect for install-time
# when dependencies are not yet installed

from .prepare import prepare_testbed_scheduler

from .r2labmap import R2labMap, R2labMapGeneric

try:
    from .mapdataframe import MapDataFrame
except ModuleNotFoundError:
    print("Warning: could not import module pandas")

try:
    import socketIO_client
    from .sidecar import R2labSidecar
except ModuleNotFoundError:
    print("Warning: could not import module socketIO_client")

from .argparse_additions import (
    ListOfChoices,
    ListOfChoicesNullReset,
)

from .utils import (
    PHONES,
    r2lab_id,
    r2lab_hostname,
    r2lab_reboot,
    r2lab_data,
    r2lab_parse_slice,
    find_local_embedded_script,
)
