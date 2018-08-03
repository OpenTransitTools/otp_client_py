from ott.utils import object_utils
from ott.utils import otp_utils

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
        object_utils.safe_set_from_dict(self, 'sortOrder', args)
        object_utils.safe_set_from_dict(self, 'shortName', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'color', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'textColor', args, always_cpy=False)

    @classmethod
    def stop_routes_factory(cls, session, stop_id, date=None, agency_id=None):
        """
        :return a list of all route(s) serving a given stop
        """
        from ott.data.dao.stop_dao import StopDao
        from ott.data.dao.route_dao import RouteListDao
        s = StopDao.query_orm_for_stop(session, stop_id, detailed=False) # detailed here will bring amenities
        routes = RouteListDao.filter_active_routes(s.routes, date=date)
        ret_val = cls._route_list_from_gtfsdb_list(routes, agency_id)
        return ret_val

    @classmethod
    def routes_factory(cls, session, date=None, agency_id=None):
        """
        :return a list of all route(s) for a given agency
        """
        from ott.data.dao.route_dao import RouteListDao
        routes = RouteListDao.active_routes(session, date=date)
        ret_val = cls._route_list_from_gtfsdb_list(routes, agency_id)
        return ret_val

    @classmethod
    def _route_list_from_gtfsdb_list(cls, route_list, agency_id=None):
        """ input gtfsdb list, output Route obj list """
        ret_val = []
        for r in route_list:
            route = cls._route_from_gtfsdb(r, agency_id)
            ret_val.append(route.__dict__)
        return ret_val

    @classmethod
    def _route_from_gtfsdb(cls, r, agency_id=None):
        """ factory to genereate a Route obj from a queried gtfsdb route """
        agency = agency_id if agency_id else r.agency_id
        otp_route_id = otp_utils.make_otp_route_id(r.route_id, agency)
        cfg = {
            'agencyName': r.agency.agency_name, 'id': otp_route_id,
            'longName': r.route_long_name, 'shortName': r.route_short_name,
            'mode': r.type.otp_type, 'sortOrder': r.route_sort_order,
            'color': r.route_color, 'textColor': r.route_text_color
        }
        ret_val = Routes(cfg)
        return ret_val

    @classmethod
    def mock(cls):
        """
        """
        ret_val = []

        for i in range(50):
            agency_name = agency_id
            route_id = i
            short_name = i if i > 2 else None
            long_name = i
            color = i
            mode = "TRAM"

            otp_route_id = cls.otp_route_id(route_id, agency_id)
            cfg = {'agencyName': agency_name, 'id': otp_route_id,
                   'shortName': short_name, 'longName': long_name,
                   'mode': mode, 'color': color}
            r = Routes(cfg)
            ret_val.append(r.__dict__)

        return ret_val
