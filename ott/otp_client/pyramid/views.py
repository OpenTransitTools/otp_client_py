from pyramid.response import Response
from pyramid.view import view_config

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops
from ott.otp_client.trip_planner import TripPlanner

from ott.geocoder.geosolr import GeoSolr
from ott.utils.parse.url.param_parser import ParamParser
from ott.utils.parse.url.geo_param_parser import GeoParamParser

from ott.utils import otp_utils
from ott.utils import json_utils

from ott.utils.svr.pyramid import response_utils
from ott.utils.svr.pyramid import globals

import logging
log = logging.getLogger(__file__)


APP_CONFIG = None
def set_app_config(app_cfg):
    """
    called set the singleton AppConfig object
    :see ott.utils.svr.pyramid.app_config.AppConfig :
    """
    global APP_CONFIG
    APP_CONFIG = app_cfg


def do_view_config(cfg):
    cfg.add_route('plan_trip', '/plan_trip')

    cfg.add_route('ti_route_patterns', '/ti/routes/{route}/patterns')
    cfg.add_route('ti_route', '/ti/routes/{route}')
    cfg.add_route('ti_route_list', '/ti/routes')

    cfg.add_route('ti_stop', '/ti/stops/{stop}')
    cfg.add_route('ti_stop_routes', '/ti/stops/{stop}/routes')
    cfg.add_route('ti_nearest_stops', '/ti/stops')


@view_config(route_name='ti_nearest_stops', renderer='json', http_cache=globals.CACHE_LONG)
def nearest_stops(request):
    """
    Nearest Stops: stops?radius=1000&lat=45.4926&lon=-122.6391
    BBox Stops: stops?minLat=45.508542&maxLat=45.5197894&minLon=-122.696084&maxLon=-122.65594
    """
     # import pdb; pdb.set_trace()
    params = GeoParamParser(request)
    agency_id = APP_CONFIG.get_agency(params)
    if params.has_radius():
        limit = params.get_first_val_as_int('limit', 10)
        with APP_CONFIG.db.managed_session(timeout=10) as session:
            ret_val = Stops.nearest_stops(session, params.point, agency_id, limit)
    elif params.has_bbox():
        limit = params.get_first_val_as_int('limit', 1000)
        with APP_CONFIG.db.managed_session(timeout=10) as session:
            ret_val = Stops.bbox_stops(session, params.bbox, agency_id, limit)
    else:
        ret_val = []
    return ret_val


@view_config(route_name='ti_stop', renderer='json', http_cache=globals.CACHE_LONG)
def stop(request):
    """
    Stop Info: index/stops/TriMet:9354
    {
      "id":"TriMet:9311",
      "code":"9311",
      "lat":45.526817, "lon":-122.674106,
      "name":"NW Glisan & 3rd",
      "desc":"Westbound stop in Portland (Stop ID 9311)",
      "url":"http://trimet.org/#tracker/stop/9311",
      "zoneId":"B",
      "locationType":0, (always 0)
      "wheelchairBoarding":0,(always 0)
      "vehicleType":-999, (always -999)
      "vehicleTypeSet":false (always false)
    }
    """
    ret_val = {}
    stop = request.matchdict['stop']
    agency_id, stop_id = otp_utils.breakout_agency_id(stop)
    if agency_id is None:
        agency_id = APP_CONFIG.get_agency(request)
    with APP_CONFIG.db.managed_session(timeout=10) as session:
        s = Stops.stop(session, stop_id, agency_id)
        if s:
            ret_val = s.__dict__
    return ret_val


@view_config(route_name='ti_stop_routes', renderer='json', http_cache=globals.CACHE_LONG)
def stop_routes(request):
    """
    """
    ret_val = []
    params = ParamParser(request)
    stop = request.matchdict['stop']
    agency_id, stop_id = otp_utils.breakout_agency_id(stop)
    if agency_id is None:
        agency_id = APP_CONFIG.get_agency(params)
    with APP_CONFIG.db.managed_session(timeout=10) as session:
        ret_val = Routes.stop_routes_factory(session, stop_id, params.get_date(), agency_id)
    return ret_val


@view_config(route_name='ti_route_list', renderer='json', http_cache=globals.CACHE_LONG)
def route_list(request):
    """
    """
    ret_val = []
    params = ParamParser(request)
    with APP_CONFIG.db.managed_session(timeout=10) as session:
        ret_val = Routes.route_list_factory(session, params.get_date())
    return ret_val


@view_config(route_name='ti_route', renderer='json', http_cache=globals.CACHE_LONG)
def route(request):
    """
    https://trimet-otp.conveyal.com/otp/routers/default/index/routes/TriMet:18
    """
    route = request.matchdict['route']
    agency_id, route_id = otp_utils.breakout_agency_id(route) # todo rename
    if agency_id is None:
        params = ParamParser(request)
        agency_id = APP_CONFIG.get_agency(params)

    ret_val = []
    with APP_CONFIG.db.managed_session(timeout=10) as session:
        ret_val = Routes.route_factory(session, route_id, agency_id)

    return ret_val



@view_config(route_name='ti_route_patterns', renderer='json', http_cache=globals.CACHE_LONG)
def route_patterns(request):
    """
    Will proxy calls to OTP transit index

    https://trimet-otp.conveyal.com/otp/routers/default/index/routes/TriMet:18/patterns

    Here's the sequence of calls to OTP for this stuff:
    https://trimet-otp.conveyal.com/otp/routers/default/index/routes/TriMet:18
    https://trimet-otp.conveyal.com/otp/routers/default/index/routes/TriMet:18/patterns
    https://trimet-otp.conveyal.com/otp/routers/default/index/patterns/TriMet:18:0:02/geometry
    """
    route = request.matchdict['route']
    ti_url = "{}/index/routes/{}/patterns".format(get_otp_url(), route)
    ret_val = json_utils.proxy_json(ti_url)
    return ret_val


@view_config(route_name='plan_trip', renderer='json', http_cache=globals.CACHE_SHORT)
def plan_trip(request):
    ret_val = None
    try:
        trip = get_planner().plan_trip(request)
        ret_val = response_utils.json_response(trip)
    except Exception as e:
        log.warning(e)
        ret_val = response_utils.sys_error_response()
    finally:
        pass
    return ret_val


def get_otp_url():
    if getattr(APP_CONFIG, 'otp_url', None) is None:
        APP_CONFIG.otp_url = APP_CONFIG.ini_settings.get('otp_url')
    return APP_CONFIG.otp_url


def get_planner():
    """ cache's up TripPlanner object (stores it in our APP_CONFIG) """
    # import pdb; pdb.set_trace()
    if getattr(APP_CONFIG, 'trip_planner', None) is None:
        planner_url = get_otp_url() + '/plan' # todo ... url append method available?
        advert_url = APP_CONFIG.ini_settings.get('advert_url')
        fare_url = APP_CONFIG.ini_settings.get('fare_url')
        cancelled_url = APP_CONFIG.ini_settings.get('cancelled_routes_url')
        solr = GeoSolr(APP_CONFIG.ini_settings.get('solr_url'))
        APP_CONFIG.trip_planner = TripPlanner(otp_url=planner_url, solr=solr, adverts=advert_url, fares=fare_url, cancelled_routes=cancelled_url)
    return APP_CONFIG.trip_planner
