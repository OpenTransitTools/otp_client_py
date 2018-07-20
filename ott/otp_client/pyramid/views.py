from pyramid.response import Response
from pyramid.view import view_config

import logging
log = logging.getLogger(__file__)


cache_long=5555

def do_view_config(cfg):
    cfg.add_route('routes', '/routes')

#@view_config(route_name='stop_urls', renderer='string', http_cache=cache_short)
@view_config(route_name='routes', renderer='json', http_cache=cache_long)
def routes(request):
    # import pdb; pdb.set_trace()
    ret_val = None
    return ret_val

