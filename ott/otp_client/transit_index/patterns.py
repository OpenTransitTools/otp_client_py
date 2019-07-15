from ott.utils import object_utils
from ott.utils import otp_utils

from .base import Base

import gtfsdb

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
        ## TODO: Is this class needed?  Maybe for converting gtfsdb route patterns (list), but ???

    @classmethod
    def query_geometry_encoded(cls, app_config, pattern_id, agency_id=None):
        if agency_id is None:
            agency_id = app_config.get_agency()

        # with pattern id (i.e., shape id) and agency, query the encoded geometry from gtfsdb
        with app_config.db.managed_session(timeout=10) as session:
            ret_val = gtfsdb.Pattern.get_geometry_encoded(session, pattern_id, agency_id)
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
