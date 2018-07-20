from pyramid.response import Response
from pyramid.view import view_config

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops

import logging
log = logging.getLogger(__file__)

cache_long=5555


def do_view_config(cfg):
    cfg.add_route('routes', '/routes')
    cfg.add_route('stops', '/stops')
    cfg.add_route('stop_routes', '/stops/{stop}/routes')


@view_config(route_name='routes', renderer='json', http_cache=cache_long)
def routes(request):
    r = Routes()
    ret_val = r.__dict__
    return ret_val


@view_config(route_name='stops', renderer='json', http_cache=cache_long)
def stops(request):
    s = Stops()
    ret_val = s.__dict__
    return ret_val


@view_config(route_name='stop_routes', renderer='json', http_cache=cache_long)
def stop_routes(request):
    ret_val = []
    try:
        stop = request.matchdict['stop']
        agency_id, stop_id = stop.split(':')
        ret_val = Routes.stop_routes(agency_id, stop_id)
    except Exception as e:
        log.warn(e)
    return ret_val
