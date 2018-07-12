from ott.utils import json_utils
from ott.utils import object_utils

from .base import Base
import urllib
import logging
log = logging.getLogger(__file__)


class Routes(Base):
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
            "mode": "TRAM",
            "color": "84BD00",
            "agencyName": "Portland Streetcar"

        },
        {

            "id": "TriMet:190",
            "longName": "MAX Yellow Line",
            "mode": "TRAM",
            "color": "F8C213",
            "agencyName": "TriMet"

        },
        {

            "id": "TriMet:208",
            "longName": "Portland Aerial Tram",
            "mode": "GONDOLA",
            "color": "898E91",
            "agencyName": "Portland Aerial Tram"

        },
        {

            "id": "TriMet:203",
            "longName": "WES Commuter Rail",
            "mode": "RAIL",
            "color": "000000",
            "agencyName": "TriMet"

        }
    ]
    """
    longName = "LONG NAME"
    mode = "RAIL"

    def __init__(self, args={}):
        #import pdb; pdb.set_trace()
        super(Routes, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'longName', args)
        object_utils.safe_set_from_dict(self, 'mode', args)
        object_utils.safe_set_from_dict(self, 'color', args, always_cpy=False)

    @classmethod
    def factory(cls):
        pass


def main():
    routes = Routes.factory()
    print(routes)


if __name__ == '__main__':
    main()
