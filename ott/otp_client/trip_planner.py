import sys
import simplejson as json
import urllib
import contextlib
import logging
import exceptions
log = logging.getLogger(__file__)

from ott.utils import json_utils
from ott.utils import object_utils
from ott.utils import html_utils

from ott.otp_client  import otp_to_ott
from ott.utils.parse import TripParamParser

from ott.geocoder.geosolr import GeoSolr


class TripPlanner(object):
    def __init__(self, otp_url="http://localhost/prod", adverts=None, fares=None, solr='http://localhost/solr'):
        self.otp_url = otp_url

        self.geo = solr
        if isinstance(solr, str):
            self.geo = GeoSolr(solr)

        self.adverts = adverts
        self.fares = fares

        # optionally create Adverts and Fares objects
        # note: requires change to this buildout to include the ott.data project
        try:
            from ott.data.content import Adverts
            from ott.data.content import Fares

            if isinstance(adverts, str):
                self.adverts = Adverts(adverts)

            if isinstance(fares, str):
                self.fares = Fares(fares)
        except Exception, e:
            log.warn(e)

    def plan_trip(self, request=None, pretty=False):
        """ "powell%20blvd::45.49063653,-122.4822897"  "45.433507,-122.559709"
        """

        # step 1: parse params
        param = TripParamParser(request)

        # step 2: handle any geocoding needing to be done -- note, changes param object implicitly in the call
        #import pdb; pdb.set_trace()
        msg = self.geocode(param)
        if msg:
            # TODO -- trip error or plan?
            pass

        # step 3: call the trip planner...
        url = "{0}?{1}".format(self.otp_url, param.otp_url_params())
        f = self.call_otp(url)
        j=json.loads(f)
        #print json.dumps(j, sort_keys=True, indent=4);

        # step 4: process any planner errors
        if j is None:
            pass
            # TODO -- trip error or plan?

        # step 5: parse the OTP trip plan into OTT format
        ret_val = {}
        try:
            plan = otp_to_ott.Plan(jsn=j['plan'], params=param, fares=self.fares)
            ret_val['plan'] = plan

            if self.adverts:
                m = plan.dominant_transit_mode()
                l = html_utils.get_lang(request)
                ret_val['adverts'] = self.adverts.query(m, l)
        except:
            try:
                ret_val['error'] = otp_to_ott.Error(j['error'], param)
            except:
                pass

        ret_val = json_utils.json_repr(ret_val, pretty or param.pretty_output())
        return ret_val

    @classmethod
    def call_otp(cls, url):
        ret_val = None
        try:
            log.info(url)
            with contextlib.closing(urllib.urlopen(url)) as f:
                ret_val = f.read()
        except Exception as e:
            log.warn(e)
        return ret_val

    def geocode(self, param):
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
            f = self.geo.geostr(f)
            param.frm = f

        # step 3: get your destination
        t = param.get_to()
        if not param.has_valid_coord(t):
            # step 3b: geocode the destination if you don't have a valid ::LatLon
            t = param.strip_coord(t)
            t = self.geo.geostr(t)
            param.to = t

        return ret_val


def main(argv):
    #import pdb; pdb.set_trace()
    pretty = 'pretty' in argv or 'p' in argv
    trimet = 'trimet' in argv or 'tm' in argv
    tp = None
    if trimet:
        tp = TripPlanner(otp_url="http://maps.trimet.org/prod", solr='http://maps.trimet.org/solr')
    else:
        tp = TripPlanner()

    plan = tp.plan_trip(argv[1], pretty)
    print plan

if __name__ == '__main__':
    main(sys.argv)
