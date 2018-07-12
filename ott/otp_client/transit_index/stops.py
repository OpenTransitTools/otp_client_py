from ott.utils import object_utils

from .base import Base

import logging
log = logging.getLogger(__file__)


class Stops(Base):
    """
    https://<domain & port>/otp/routers/default/index/routes
    [
        {
            "id": "TriMet:54",
            "agencyName": "TriMet",
            "shortName": "54",
            "longName": "Beaverton-Hillsdale Hwy",
            "mode": "BUS"
        },
        {

            "id": "TriMet:193",
            "longName": "Portland Streetcar - NS Line",
            "mode": "TRAM" or "GONDOLA" or "RAIL" or ...
            "color": "84BD00",
            "agencyName": "Portland Streetcar"

        }
    ]
    """
    longName = "LONG NAME"
    mode = "RAIL"

    def __init__(self, args={}):
        super(Stops, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'longName', args)
        object_utils.safe_set_from_dict(self, 'mode', args)
        object_utils.safe_set_from_dict(self, 'color', args, always_cpy=False)

    @classmethod
    def factory(cls):
        pass
