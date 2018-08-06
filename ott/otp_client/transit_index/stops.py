from ott.utils import object_utils
from ott.utils import otp_utils

from .base import Base

import logging
log = logging.getLogger(__file__)


class Stops(Base):
    """
    Scrolling map / BBOX call to stops:

    https://<domain & port>/otp/routers/default/index/stops?
      minLat=45.50854243338104&maxLat=45.519789433696744&minLon=-122.6960849761963&maxLon=-122.65591621398927
    [
        {
            id: TriMet:4026
            code: 4026
            name: SE Morrison & 9th
            lat: 45.517303
            lon: -122.656536
            url: http://trimet.org/#tracker/stop/4026
        }
    ]

    Nearest stops call:

    https://<domain & port>/otp/routers/default/index/stops?
    radius=1000&lat=45.4926336&lon=-122.63915519999999
    [
      {
        "id": "TriMet:5516",
        "code": "5516",
        "name": "SE Steele & 30th",
        "lat": 45.484781,
        "lon": -122.635074,
        "url": "http://trimet.org/#tracker/stop/5516",
        "dist": 928
      }
    ]

    FYI, there's also a new OTP TI P&R service:
    https://trimet-otp.conveyal.com/otp/routers/default/park_and_ride

    ALSO STOP SCHEDULES:
    https://trimet-otp.conveyal.com/otp/routers/default/index/stops/TriMet:823/stoptimes?timeRange=14400

    """
    def __init__(self, args={}):
        super(Stops, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'code', args)
        object_utils.safe_set_from_dict(self, 'name', args)
        object_utils.safe_set_from_dict(self, 'lat', args)
        object_utils.safe_set_from_dict(self, 'lon', args)
        object_utils.safe_set_from_dict(self, 'url', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'mode', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'dist', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'routes', args, always_cpy=False) # todo

    @classmethod
    def bbox_stops(cls, session, bbox, limit=1000, agency_id=None):
        """
        :return a list of stops within the bbox
        """
        ret_val = []
        from ott.data.dao.stop_dao import StopListDao
        stops = StopListDao.stops_by_bbox(session, bbox.to_geojson(), limit, agency_id)
        ret_val = cls._stop_list_from_gtfsdb_list(stops, agency_id)
        return ret_val

    @classmethod
    def nearest_stops(cls, session, point, limit=10, agency_id=None):
        """
        query nearest stops based on walk graph
        :params db session, POINT(x,y), limit=10:
        TODO: otp nearest is TDB functionality ... so just call gtfsdb for now
        :return a list of nearest stops
        """
        #import pdb; pdb.set_trace()
        from ott.data.dao.stop_dao import StopListDao
        stops = StopListDao.query_nearest_stops(session, geojson_point, radius, limit, is_active)
        ret_val = cls._stop_list_from_gtfsdb_list(stops, agency_id)
        return ret_val

    @classmethod
    def _stop_list_from_gtfsdb_list(cls, gtfsdb_stop_list, agency_id=None):
        """ input gtfsdb list, output Route obj list """
        ret_val = []
        for s in gtfsdb_stop_list:
            stop = cls._stop_from_gtfsdb(s, agency_id)
            ret_val.append(stop.__dict__)
        return ret_val

    @classmethod
    def _stop_from_gtfsdb(cls, s, agency_id=None, detailed=False):
        """
        factory to genereate a Stop obj from a queried gtfsdb stop
        TODO: thinking we should have a current (and maybe future) stop table in gtfsdb, where
              agency, routes, tiny names, etc... are pre-calculated
              and stops are updated weekly (daily) in this current schema
        """
        mode = None
        agency_name = agency_id
        route_short_names = None

        # step 1: get mode and agency id (if needed)
        if s.routes and len(s.routes) > 0:
            for r in s.routes:
                # step 1a: get agency and mode vars
                if agency_id is None:
                    agency_id = r.agency_id
                agency_name = r.agency.agency_name
                mode = r.type.otp_type

                # step 1b: stopping condition
                if mode and agency_id:
                    break

        # step 2: build out stop info if we want detailed info
        if detailed:
            from ott.data.dao.stop_dao import StopDao
            route_short_names = StopDao.make_short_names(s) # note: this will probably be very expensive

        # step 3: build the stop
        otp_stop_id = otp_utils.make_otp_id(s.stop_id, agency_id)
        cfg = {
            'agencyName': agency_name, 'id': otp_stop_id,
            'name': s.stop_name, 'code': s.stop_code,
            'lat': float(s.stop_lat), 'lon': float(s.stop_lon),
            'url': getattr(s, 'stop_url', None),
            'mode': mode,
            'dist': 111.111,  # todo: dist and also routes
            'routes': route_short_names
        }
        ret_val = Stops(cfg)
        return ret_val

    @classmethod
    def mock(cls, num_recs=5):
        """ mock a response """
        ret_val = []
        for i in range(num_recs):
            stop_id = i+1
            cfg = {'id': stop_id}
            distance = 2.2 + float(i)
            cfg['dist'] = distance
            s = Stops(cfg)
            ret_val.append(s.__dict__)
        return ret_val
