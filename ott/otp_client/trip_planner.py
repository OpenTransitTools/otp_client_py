"""
"""
import sys
import simplejson as json
import urllib
import logging
log = logging.getLogger(__file__)

from ott.controller.util import json_utils
from ott.controller.util import object_utils
from ott.controller.util import html_utils
from ott.controller.util import config

from ott.otp_client import otp_to_ott
from ott.utils.parser.trip_param_parser import TripParamParser

from ott.controller.services.geocoder.geosolr import GeoSolr
geo = GeoSolr(config.get('solr'))

def call_otp(url):
    ret_val = None
    try:
        log.info(url)
        f = urllib.urlopen(url)
        ret_val = f.read()
    except Exception as e:
        log.warn(e)
    return ret_val

def geocode(param):
    ''' TODO ... rethink this whole thing 
        1) should geocoding be in param_parser
        2) we're going to need other parsers ... like for stops, etc... (where we only need to geocode 1 param, etc...)
        3) ....
    '''
    ret_val = None

    # step 2: get your origin
    f = param.get_from()
    if not param.has_valid_coord(f):
        # step 2b: geocode the origin if you don't have a valid ::LatLon
        f = param.strip_coord(f)
        f = geo.geostr(f)
        param.frm = f

    # step 3: get your destination
    t = param.get_to()
    if not param.has_valid_coord(t):
        # step 3b: geocode the destination if you don't have a valid ::LatLon
        t = param.strip_coord(t)
        t = geo.geostr(t)
        param.to = t

    return ret_val

#import pdb; pdb.set_trace()

def plan_trip(request=None, pretty=False, adverts=False):
    """ "powell%20blvd::45.49063653,-122.4822897"  "45.433507,-122.559709"
    """

    # step 1: parse params
    param = PlannerParamParser(request)

    # step 2: parse params -- note, changes param object implicitly in the call
    msg = geocode(param)
    if msg:
        # TODO -- trip error or plan?
        pass

    # step 3: call the trip planner...
    url = "{0}?{1}".format(config.get('otp'), param.otp_url_params())
    f = call_otp(url) 
    j=json.loads(f)
    #print json.dumps(j, sort_keys=True, indent=4);

    # step 4: process any planner errors
    if j is None:
        pass
        # TODO -- trip error or plan?

    # step 5: parse the OTP trip plan into OTT format
    ret_val = {}
    try:
        plan = otp_to_ott.Plan(j['plan'], param)
        ret_val['plan'] = plan

        if adverts:
            m = plan.dominant_transit_mode()
            l = html_utils.get_lang(request)
            ret_val['adverts'] = adverts.query(m, l)

    except:
        try:
            ret_val['error'] = otp_to_ott.Error(j['error'], param)
        except:
            pass

    ret_val = json_utils.json_repr(ret_val, pretty or param.pretty_output())

    return ret_val

def main(argv):
    pretty = 'pretty' in argv or 'p' in argv
    plan = plan_trip(argv, pretty)
    print plan

if __name__ == '__main__':
    main(sys.argv)
