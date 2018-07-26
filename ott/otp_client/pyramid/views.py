from pyramid.response import Response
from pyramid.view import view_config

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops
from ott.otp_client.trip_planner import TripPlanner

from ott.geocoder.geosolr import GeoSolr
from ott.utils.parse.url.geo_param_parser import GeoParamParser

from ott.utils import json_utils
from ott.utils import object_utils

from ott.utils.svr.pyramid import response_utils
from ott.utils.svr.pyramid.globals import *

import logging
log = logging.getLogger(__file__)


APP_CONFIG=None
def set_app_config(app_cfg):
    """
    called set the singleton AppConfig object
    :see ott.utils.svr.pyramid.app_config.AppConfig :
    """
    global APP_CONFIG
    APP_CONFIG = app_cfg


def do_view_config(cfg):
    cfg.add_route('plan_trip', '/plan_trip')
    cfg.add_route('ti_routes', '/ti/routes')
    cfg.add_route('ti_stops', '/ti/stops')
    cfg.add_route('ti_stop_routes', '/ti/stops/{stop}/routes')


@view_config(route_name='ti_stops', renderer='json', http_cache=CACHE_LONG)
def stops(request):
    """
    Nearest Stops: stops?radius=1000&lat=45.4926336&lon=-122.63915519999999
    BBox Stops: stops?minLat=45.508542&maxLat=45.5197894&minLon=-122.696084&maxLon=-122.65594
    """
    #import pdb; pdb.set_trace()
    params = GeoParamParser(request)
    if params.has_radius():
        ret_val = Stops.nearest_stops(2, 3, 5)
    elif params.has_bbox():
        ret_val = Stops.bbox_stops(1, 3, 5, 4)
    else:
        ret_val = []
    return ret_val


@view_config(route_name='ti_routes', renderer='json', http_cache=CACHE_LONG)
def routes(request):
    ret_val = Routes.routes_factory()
    return ret_val


@view_config(route_name='ti_stop_routes', renderer='json', http_cache=CACHE_LONG)
def stop_routes(request):
    ret_val = []
    try:
        stop = request.matchdict['stop']
        agency_id, stop_id = stop.split(':')
        ret_val = Routes.stop_routes_factory(agency_id, stop_id)
    except Exception as e:
        log.warn(e)
    return ret_val


@view_config(route_name='plan_trip', renderer='json', http_cache=CACHE_SHORT)
def plan_trip(request):
    ret_val = None
    try:
        trip = get_planner().plan_trip(request)
        ret_val = response_utils.json_response(trip)
    except Exception as e:
        log.warn(e)
        ret_val = response_utils.sys_error_response()
    finally:
        pass
    return ret_val


def get_planner():
    #import pdb; pdb.set_trace()
    if getattr(APP_CONFIG, 'trip_planner', None) is None:
        otp_url = APP_CONFIG.ini_settings.get('otp_url')
        advert_url = APP_CONFIG.ini_settings.get('advert_url')
        fare_url = APP_CONFIG.ini_settings.get('fare_url')
        cancelled_url = APP_CONFIG.ini_settings.get('cancelled_routes_url')
        solr = GeoSolr(APP_CONFIG.ini_settings.get('solr_url'))
        APP_CONFIG.trip_planner = TripPlanner(otp_url=otp_url, solr=solr, adverts=advert_url, fares=fare_url, cancelled_routes=cancelled_url)
    return APP_CONFIG.trip_planner
