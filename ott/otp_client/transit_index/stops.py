from ott.utils import object_utils
from ott.utils import otp_utils
from ott.utils import geo_utils

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


    Stop call https://<domain & port>/otp/routers/default/index/stops/<agency>:<stop_id>
    {
        "id": "TriMet:9354",
        "code": "9354",
        "name": "W Burnside & SW Osage",
        "lat": 45.523777,
        "lon": -122.700989,
        "url": "http://trimet.org/#tracker/stop/9354",
        "desc": "Eastbound stop in Portland (Stop ID 9354)",
        "zoneId": "B",
        "locationType": 0,
        "wheelchairBoarding": 0,
        "vehicleType": -999,
        "vehicleTypeSet": false
    }


    FYI, there's also a new OTP TI P&R service:
    https://trimet-otp.conveyal.com/otp/routers/default/park_and_ride

    ALSO STOP SCHEDULES:
    https://trimet-otp.conveyal.com/otp/routers/default/index/stops/TriMet:823/stoptimes?timeRange=14400

    """
    def __init__(self, args={}):
        super(Stops, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'code', args)
        object_utils.safe_set_from_dict(self, 'name', args)
        object_utils.safe_set_from_dict(self, 'desc', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'lat', args)
        object_utils.safe_set_from_dict(self, 'lon', args)
        object_utils.safe_set_from_dict(self, 'url', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'dist', args, always_cpy=False)

        object_utils.safe_set_from_dict(self, 'zoneId', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'routes', args, always_cpy=False)  # todo
        object_utils.safe_set_from_dict(self, 'mode', args, always_cpy=False) # change to vehicleType??
        object_utils.safe_set_from_dict(self, 'locationType', args, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'vehicleType', args, def_val=-999, always_cpy=False)
        object_utils.safe_set_from_dict(self, 'vehicleTypeSet', args, def_val=False, always_cpy=False)

    @classmethod
    def bbox_stops(cls, session, bbox, limit=1000, agency_id=None):
        """
        :return a list of stops within the bbox
        """
        ret_val = []
        from ott.data.dao.stop_dao import StopListDao
        stops = StopListDao.query_bbox_stops(session, bbox.to_geojson(), limit, agency_id)
        ret_val = cls._stop_list_from_gtfsdb_list(stops, agency_id, limit)
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
        stops = StopListDao.query_nearest_stops(session, point.to_geojson(), point.radius, limit, is_active=True)
        ret_val = cls._stop_list_from_gtfsdb_list(stops, point, agency_id, limit)
        return ret_val

    @classmethod
    def stop(cls, session, stop_id, agency_id=None, def_val={}):
        """
        query stop from db via stop id and agency
        :return a stop record
        """
        #import pdb; pdb.set_trace()
        ret_val = def_val
        from ott.data.dao.stop_dao import StopDao
        stop = StopDao.query_orm_for_stop(session, stop_id)
        if stop:
            ret_val = cls._stop_from_gtfsdb(stop, agency_id=agency_id)
        return ret_val

    @classmethod
    def _stop_list_from_gtfsdb_list(cls, gtfsdb_stop_list, point=None, agency_id=None, limit=10):
        """ input gtfsdb list, output Route obj list """
        ret_val = []
        for i, s in enumerate(gtfsdb_stop_list):
            if i > limit: break
            stop = cls._stop_from_gtfsdb(s, point, agency_id)
            ret_val.append(stop.__dict__)
        return ret_val

    @classmethod
    def _stop_from_gtfsdb(cls, s, point=None, agency_id=None, detailed=False):
        """
        factory to genereate a Stop obj from a queried gtfsdb stop
        TODO: thinking we should have a current (and maybe future) stop table in gtfsdb, where
              agency, routes, tiny names, etc... are pre-calculated
              and stops are updated weekly (daily) in this current schema
        """
        mode = None
        location_type = s.location_type
        agency_name = agency_id
        route_short_names = None

        # step 1: get mode and agency id (if needed)
        if detailed and s.routes and len(s.routes) > 0:
            for r in s.routes:
                # step 1a: get agency and mode vars
                if agency_id is None:
                    agency_id = r.agency_id
                agency_name = r.agency.agency_name
                mode = r.type.otp_type
                location_type = r.type.route_type

                # step 1b: stopping condition
                if mode and agency_id:
                    break

        # step 2: build out stop info if we want detailed info
        if detailed:
            from ott.data.dao.stop_dao import StopDao
            route_short_names = StopDao.make_short_names(s)  # note: this will probably be very expensive

        # step 3: build the stop
        otp_stop_id = otp_utils.make_otp_id(s.stop_id, agency_id)
        cfg = {
            'agencyName': agency_name,
            'id': otp_stop_id, 'code': s.stop_code,
            'name': s.stop_name, 'desc': s.stop_desc,
            'lat': float(s.stop_lat), 'lon': float(s.stop_lon),
            'url': getattr(s, 'stop_url', None),
            'mode': mode,
            'locationType': location_type,
            'routes': route_short_names
        }
        if point:
            # todo ... have the dist come from PostGIS (Duh!)
            cfg['dist'] = geo_utils.distance(point.lat, point.lon, s.stop_lat, s.stop_lon)

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
