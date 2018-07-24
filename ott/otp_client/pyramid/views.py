from pyramid.response import Response
from pyramid.view import view_config

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops

from ott.utils.parse.url.geo_param_parser import GeoParamParser

import logging
log = logging.getLogger(__file__)

cache_long=5555


def do_view_config(cfg):
    cfg.add_route('ti_stops', '/ti/stops')
    cfg.add_route('ti_stop_routes', '/ti/stops/{stop}/routes')
    cfg.add_route('ti_routes', '/ti/routes')


@view_config(route_name='ti_stops', renderer='json', http_cache=cache_long)
def stops(request):
    """
    Nearest Stops: stops?radius=1000&lat=45.4926336&lon=-122.63915519999999
    BBox Stops: stops?minLat=45.508542&maxLat=45.5197894&minLon=-122.696084&maxLon=-122.65594
    """
    # import pdb; pdb.set_trace()
    params = GeoParamParser(request)
    # if request contains 'radius' and lat and lon:
    ret_val = Stops.nearest_stops(2, 3, 5)
    # elif request contains ....
    ret_val = Stops.bbox_stops(1, 3, 5, 4)
    return ret_val


@view_config(route_name='ti_routes', renderer='json', http_cache=cache_long)
def routes(request):
    ret_val = Routes.routes_factory()
    return ret_val


@view_config(route_name='ti_stop_routes', renderer='json', http_cache=cache_long)
def stop_routes(request):
    ret_val = []
    try:
        stop = request.matchdict['stop']
        agency_id, stop_id = stop.split(':')
        ret_val = Routes.stop_routes_factory(agency_id, stop_id)
    except Exception as e:
        log.warn(e)
    return ret_val
