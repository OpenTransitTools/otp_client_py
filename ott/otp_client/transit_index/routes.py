from ott.utils import object_utils

from .base import Base

import logging
log = logging.getLogger(__file__)


class Routes(Base):
    """
    ROUTE LIST:
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

    STOP's ROUTES:
    https://<domain & port>/otp/routers/default/index/stops/TriMet:5516/routes
    [
      {
        "id": "TriMet:10",
        "shortName": "10",
        "longName": "Harold St",
        "mode": "BUS",
        "agencyName": "TriMet"
      }
    ]
    """

    def __init__(self, args={}):
        super(Routes, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'mode', args)
        object_utils.safe_set_from_dict(self, 'longName', args)
        object_utils.safe_set_from_dict(self, 'shortName', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'color', args, always_cpy=False)


    @classmethod
    def stop_routes(cls, agency_id, stop_id):
        ret_val = []

        for i in range(5):
            agency_name = agency_id
            route_id = i
            color = stop_id
            otp_route_id = "{}:{}".format(agency_id, route_id)
            r = Routes({'agencyName': agency_name, 'id': otp_route_id, 'shortName': route_id, 'color': color})
            ret_val.append(r.__dict__)

        return ret_val
