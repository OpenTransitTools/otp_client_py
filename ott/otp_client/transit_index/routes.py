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
    def stop_routes_factory(cls, agency_id, stop_id):
        """
        :return a list of all route(s) serving a given stop
        """
        ret_val = []

        for i in range(5):
            agency_name = agency_id
            route_id = i
            short_name = i if i > 2 else None
            long_name = agency_id + str(i)
            color = stop_id
            mode = "TRAM"

            otp_route_id = "{}:{}".format(agency_id, route_id)
            cfg = {'agencyName': agency_name, 'id': otp_route_id,
                   'shortName': short_name, 'longName': long_name,
                   'mode': mode, 'color': color}
            r = Routes(cfg)
            ret_val.append(r.__dict__)

        return ret_val


    @classmethod
    def routes_factory(cls, agency_id=None):
        """
        :return a list of all route(s) for a given agency
        """
        ret_val = []

        for i in range(50):
            agency_name = agency_id
            route_id = i
            short_name = i if i > 2 else None
            long_name = i
            color = i
            mode = "TRAM"

            otp_route_id = "{}:{}".format(agency_id, route_id)
            cfg = {'agencyName': agency_name, 'id': otp_route_id,
                   'shortName': short_name, 'longName': long_name,
                   'mode': mode, 'color': color}
            r = Routes(cfg)
            ret_val.append(r.__dict__)

        return ret_val
