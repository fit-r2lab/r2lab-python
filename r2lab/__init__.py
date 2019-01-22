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
    print("Warning: no module pandas - MapDataFrame not available")


try:
    from .sidecar import (
        SidecarAsyncClient, SidecarSyncClient, default_sidecar_url)
    from .sidecar_payload import SidecarPayload
except ModuleNotFoundError:
    print("Warning: no module websockets - sidecar clients not available")


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
