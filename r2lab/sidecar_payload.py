# pylint: disable=c0111, w1203

"""
Sidecar protocol relies on a very simple payload
"""

import logging
import json


# the attributes of interest, and their possible values
# this for now is for information only
#
# the sidecar only keeps live data about the nodes
# what is static (SDR, photos, ...) comes from the inventory, and
# the availability from r2labapi (see rhubarbe available);
# both are reported by monitornodes, and are not meant to be set from here
SUPPORTED = {
    'nodes': {
        '__range__': range(1, 38),
        # live status
        'cmc_on_off': ("on", "off", "fail"),
        'usrp_on_off': ("on", "off"),
        'control_ping': ("on", "off"),
        # ssh answers, on any port (22, or 2222 on a docker host)
        'control_ssh': ("on", "off"),
        # only if monitornodes looks for it: the node runs the image
        # loader or saver
        'control_telnet': ("on", "off"),
        # where ssh answers, a list of ports: [22], [2222] or [22, 2222]
        'ssh_ports': "list",
        # one label computed from the above by monitornodes
        'state': ("off", "bios", "booting", "telnet", "docker-only",
                  "container", "regular", "zombie", "unknown"),
        # records, i.e. dicts, as sent by monitornodes
        # what runs on the bare machine: ssh_port, os_release, pretty_name,
        # image_radical, uname, gnuradio_release, docker_version, seen
        'metal': "dict",
        # None for a regular node; for a docker node: image, running,
        # started, os_release, pretty_name, seen
        'container': "dict or None",
        # free-form, from the inventory: usrp_type, usrp_duplexer,
        # usrp_logo, data_interface, images, images_wifi, images_usrp, ...
        'static': "dict",
        # status ('ok' or 'ko') and, if ko, reason and since
        'availability': "dict",
    },
    'phones': {
        '__range__': range(1, 2),
        'airplane_mode': ("on", "off"),
    },
    'leases': {},
}



class SidecarPayload:

    """
    A Payload instance models what goes in one websockets message
    It has 2 forms, either raw string, or a JSON-decoded dict (called umbrella),
    which is expected to have 3 keys: category, action and message
    """

    def __init__(self, *, umbrella=None, string=None):
        if umbrella is not None:
            self.umbrella = umbrella
        elif string is not None:
            self.string = string
        else:
            self._umbrella = {}


    @staticmethod
    def check_umbrella(umbrella):
        """
        Check payload once it's been json-unmarshalled
        """
        if ('action' not in umbrella or
                umbrella['action'] not in ('request', 'info')):
            logging.error(f"Ignoring misformed umbrella {umbrella}")
            return False
        if ('category' not in umbrella or
                umbrella['category'] not in SUPPORTED):
            logging.error(f"Ignoring unknown category in {umbrella}")
            return False
        if 'message' not in umbrella:
            logging.error(f"Ignoring payload without a 'message' {umbrella}")
            return False
        if 'action' == 'info':
            message = umbrella['message']
            if not isinstance(message, list):
                logging.error(f"Unexpected 'message'"
                              f" of type {type(message).__name__}"
                              f" - should be a list")
                return False
        return True


    # the umbrella property
    def _get_umbrella(self):
        return self._umbrella

    def _set_umbrella(self, umbrella):
        if self.check_umbrella(umbrella):
            self._umbrella = umbrella

    umbrella = property(
        _get_umbrella, _set_umbrella, None, doc=
        """
        This attribute allows to deal with the payload object through
        a 3-fold dict object that has the ``category``, ``action``
        and ``message`` keys.
        """)


    # the string property
    def _get_string(self):
        return json.dumps(self._umbrella)

    def _set_string(self, string):
        decoded = json.loads(string)
        if self.check_umbrella(decoded):
            self._umbrella = decoded

    string = property(_get_string, _set_string)


    # another common need is, you have the 'message' part
    # as a list of infos already
    # and want to send it in a 'category'
    # in this case the action is always 'info'
    def fill_from_infos(self, infos, category='nodes'):
        self.umbrella = dict(category=category,
                             action='info',
                             message=infos)
        return self


    # set several attributes in one message
    # a triple is an (id, attribute, value)
    def fill_from_triples(self, category, triples):
        """
        Fills payload object from category and triples,
        which must be a list of unpackable objects of the form
        id, attribute, value
        """
        info_by_id = {}
        for oid, attribute, value in triples:
            # accept strings
            oid = int(oid)
            if oid not in info_by_id:
                info_by_id[oid] = {'id': oid}
            info_by_id[oid][attribute] = value
        infos = list(info_by_id.values())
        return self.fill_from_infos(infos, category=category)
