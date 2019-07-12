from ott.utils import object_utils
from ott.utils import otp_utils

from .base import Base

import logging
log = logging.getLogger(__file__)


class Patterns(Base):
    """
    OpenTripPlanner's (OTP's) Transit Index (TI) is a GET web service that will return route, stop and schedule data from
    the OTP graph. The problem is that the TI cannot deal with date-based GTFS data.  Further, I would (strongly) argue
    that the TI is way out of OTP's scope architecturally.

    This call provides the pattern query services from gtfsdb as an alternate to OTP.

    The Pattern class will deal with the following TI services:
      - ROUTE PATTENS  - https://<domain & port>/otp/routers/default/index/route/<route_id>/patterns
      - SINGLE PATTERN - https://<domain & port>/otp/routers/default/index/pattern/<ID>/geometry

    """
    def __init__(self, args={}):
        super(Pattern, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'mode', args)

    @classmethod
    def pattern_factory(cls, session, pattern_id, agency_id=None, encode=True):
        """
        will return the geometry of the specified pattern (via pattern_id aka shape_id)

        :param session:
        :param pattern_id - NOTE that pattern_id is also referred to as shape_id in GTFSDB:
        :param agency_id - optional ... else defaults to configured default agency:
        :param encode - use mapbox compressing of geometry into encoded/minified string :
        :return geometry object of some sort:
        """


    @classmethod
    def route_patterns_factory(cls, session, route_id, date=None, agency_id=None):
        """
        :return a list of all patterns serving a given route

        http://localhost:54445/ti/ XXXXXNNN

        [
          {
            "id": "TriMet:10",
          }
        ]
        """
        # import pdb; pdb.set_trace()
        if date:
            from gtfsdb import RoutePattern
        else:
            from gtfsdb import CurrentRoutePatter

        ret_val = cls._XXXXXXroute_list_from_gtfsdb_orm_list(routes, agency_id)
        return ret_val

    @classmethod
    def _route_from_gtfsdb_orm(cls, r, agency_id=None):
        """ factory to genereate a Route obj from a queried gtfsdb route """
        agency = agency_id if agency_id else r.agency_id
        otp_route_id = otp_utils.make_otp_id(r.route_id, agency)
        cfg = {
            'agencyName': r.agency.agency_name, 'id': otp_route_id,
            'longName': r.route_long_name, 'shortName': r.route_short_name,
            'mode': r.type.otp_type, 'type': r.type.route_type,
            'sortOrder': r.route_sort_order,
            'color': r.route_color, 'textColor': r.route_text_color
        }
        ret_val = Routes(cfg)
        return ret_val

    @classmethod
    def mock(cls, agency_id="MOCK"):
        """
        """
        ret_val = []
        for i in range(50):
            agency_name = agency_id
            route_id = str(i+1)
            short_name = str(route_id) if i % 2 else None
            long_name = "{}-{}".format(i+1, agency_id)
            color = "Ox{:02}{:02}{:02}".format(i+3, i*2, i+17)
            mode = "TRAM" if i % 3 else "BUS"

            otp_route_id = otp_utils.make_otp_id(route_id, agency_id)
            cfg = {'agencyName': agency_name, 'id': otp_route_id,
                   'shortName': short_name, 'longName': long_name,
                   'mode': mode, 'color': color, 'sortOrder': i+1}
            r = Routes(cfg)
            ret_val.append(r.__dict__)
        return ret_val
