""" Convert an OpenTripPlanner json itinerary response into something that's more suitable for rendering via a webpage
"""
import re
import sys
import math
from decimal import *
import datetime
from datetime import timedelta
import simplejson as json

from ott.utils import object_utils
from ott.utils import date_utils
from ott.utils import json_utils

import logging
log = logging.getLogger(__file__)


def remove_agency_from_id(id):
    """ OTP 1.0 has TriMet:1 for trip and route ids
    """
    ret_val = id
    if id and ":" in id:
        v = id.split(":")
        if v and len(v) > 1 and len(v[1]) > 0:
            ret_val = v[1].strip()
    return ret_val


class Error(object):
    def __init__(self, jsn, params=None):
        self.id  = jsn['id']
        self.msg = jsn['msg']


class DateInfo(object):
    def __init__(self, jsn):
        # import pdb; pdb.set_trace()
        self.start_time_ms = jsn['startTime']
        self.end_time_ms = jsn['endTime']
        start = datetime.datetime.fromtimestamp(self.start_time_ms / 1000)
        end   = datetime.datetime.fromtimestamp(self.end_time_ms / 1000)

        self.start_date = "{}/{}/{}".format(start.month, start.day, start.year) # 2/29/2012
        self.end_date = "{}/{}/{}".format(end.month, end.day, end.year) # 2/29/2012

        self.start_time = start.strftime(" %I:%M%p").lower().replace(' 0','') # "3:40pm" -- note, keep pre-space
        self.end_time = end.strftime(" %I:%M%p").lower().replace(' 0','')    # "3:44pm" -- note, keep pre-space

        # service_date is important to link off to proper stop timetables
        # in OTP 1.0, we have: <serviceDate>20161123</serviceDate>
        # in older versions of OTP, there's no such date so set it to start_date
        if 'serviceDate' in jsn and len(jsn['serviceDate']) == 8:
            syear = jsn['serviceDate'][0:4]
            smonth = jsn['serviceDate'][4:6].lstrip('0')
            sday = jsn['serviceDate'][6:].lstrip('0')
            self.service_date = "{}/{}/{}".format(smonth, sday, syear) # 2/29/2012
        else:
            self.service_date = self.estimate_service_date(start)

        # OTP 1.0 has seconds not millisecs for duration
        durr = int(jsn['duration'])
        if durr < 60000:
            durr = durr * 1000
        self.duration_ms = durr
        self.duration = ms_to_minutes(self.duration_ms, is_pretty=True, show_hours=True)

        self.date = "%d/%d/%d" % (start.month, start.day, start.year) # 2/29/2012
        self.pretty_date = start.strftime("%A, %B %d, %Y").replace(' 0',' ')    # "Monday, March 4, 2013"

        self.day   = start.day
        self.month = start.month
        self.year  = start.year

    def estimate_service_date(self, start):
        """ in OTP 1.0, we are provided a service_date that's very important to linking to proper schedules, etc...
            but in prior versions, we are missing service_date, so this rountine is going to calculate service date
            this way:  if the hour is earier than 3am, then use 'yesterday' as the service date.  This is a hack that
            works for agencies like TriMet, which do not have Owl service.

            NOTE: there are often instances in parsing OTP 1.0 (non Legs) that also don't have a service_date attribute,
                  so this routine will also be called.  (Service date is mostly used for linking a transit leg
                  to a stop schedule, so...)
        """
        d = start
        if start.hour < 3:
            """ yesterday calculation for times less than 3am """
            d = start - timedelta(days=1)
        ret_val = "{}/{}/{}".format(d.month, d.day, d.year) # 2/29/2012
        return ret_val


class DateInfoExtended(DateInfo):
    """
    """
    def __init__(self, jsn):
        super(DateInfoExtended, self).__init__(jsn)
        self.extended = True

        # step 1: get data
        walk = get_element(jsn, 'walkTime', 0)
        tran = get_element(jsn, 'transitTime', 0)
        wait = get_element(jsn, 'waitingTime', 0)
        tot  = walk + tran + wait

        # step 2: trip length
        h,m = seconds_to_hours_minutes(tot)
        self.total_time_hours = h
        self.total_time_mins = m
        self.duration_min = int(round(tot / 60))

        # step 3: transit info
        h,m = seconds_to_hours_minutes(tran)
        self.transit_time_hours = h
        self.transit_time_mins = m
        self.start_transit = "TODO"
        self.end_transit = "TODO"

        # step 4: bike / walk length
        self.bike_time_hours = None
        self.bike_time_mins = None
        self.walk_time_hours = None
        self.walk_time_mins = None
        if 'mode' in jsn and jsn['mode'] == 'BICYCLE':
            h,m = seconds_to_hours_minutes(walk)
            self.bike_time_hours = h
            self.bike_time_mins = m
        else:
            h,m = seconds_to_hours_minutes(walk)
            self.walk_time_hours = h
            self.walk_time_mins = m

        # step 5: wait time
        h,m = seconds_to_hours_minutes(wait)
        self.wait_time_hours = h
        self.wait_time_mins = m

        # step 5: drive time...unused as of now...
        self.drive_time_hours = None
        self.drive_time_mins = None
        self.text = self.get_text()


    def get_text(self):
        """
        """
        ret_val = ''
        tot =  hour_min_string(self.total_time_hours, self.total_time_mins)
        walk = hour_min_string(self.walk_time_hours, self.walk_time_mins)
        bike = hour_min_string(self.bike_time_hours, self.bike_time_mins)
        wait = hour_min_string(self.wait_time_hours, self.wait_time_mins)
        return ret_val


class Elevation(object):
    def __init__(self, steps):
        self.points   = None
        self.points_array = None
        self.distance = None
        self.start_ft = None
        self.end_ft   = None
        self.high_ft  = None
        self.low_ft   = None
        self.rise_ft  = None
        self.fall_ft  = None
        self.grade    = None

        self.distance = self.make_distance(steps)
        self.points_array, self.points = self.make_points(steps)
        self.grade = self.find_max_grade(steps)
        self.set_marks()

    @classmethod
    def make_distance(cls, steps):
        """ loop through distance
        """
        ret_val = None
        try:
            dist = 0
            for s in steps:
                dist += s['distance']
            ret_val = dist
        except Exception as ex:
            log.warning(ex)
        return ret_val

    @classmethod
    def make_point_string(cls, points, max_len=50):
        """
        """
        points_array = points

        if len(points) > (max_len * 1.15):
            # reduce the point array down to something around the size of max_len (or smaller)
            points_array = []

            # slice the array up into chunks
            # @see http://stackoverflow.com/questions/1335392/iteration-over-list-slices (thank you Nadia)
            slice_size = int(round(len(points) / max_len))
            if slice_size == 1:
                slice_size = 2
            list_of_slices = zip(*(iter(points),) * slice_size)

            # average up the slices
            for s in list_of_slices:
                avg = sum(s) / len(s)
                points_array.append(avg)

        points_string = ','.join(["{0:.2f}".format(p) for p in points_array])
        return points_string

    @classmethod
    def make_points(cls, steps):
        """ parse leg for list of elevation points and distances
        """
        points_array  = None
        points_string = None
        try:
            points = [] 
            for s in steps:
                for e in s['elevation']: 
                    elev = e['second']
                    dist = e['first']
                    points.append(round(elev, 2))
            if len(points) > 0:
                points_array  = points
                points_string = cls.make_point_string(points)
        except Exception as e:
            log.warning(e)
        return points_array, points_string

    @classmethod
    def find_max_grade(cls, steps):
        """ parse leg for list of elevation points and distances
        """
        r = {'up': 0, 'down': 0, 'ue': 0, 'ud': 0, 'de': 0, 'dd': 0}
        ret_val = r
        try:
            for s in steps:
                first = True
                going_up = False
                for e in s['elevation']: 
                    dist = e['first']
                    elev = e['second']

                    if first:
                        first = False
                        r['ue'] = elev
                        r['ud'] = dist
                        r['de'] = elev
                        r['dd'] = dist
                    else:
                        # going up
                        if elev > r['lue']:
                            # set up vals
                            r['lue'] = elev
                            r['lud'] = dist

                            # set down vals
                            going_up = True
                        elif elev < r['lue']:
                            last_elev = elev
        except Exception as e:
            log.warning(e)

        return ret_val

    def set_marks(self):
        """ finds start / end / high / low
        """
        try:
            start = self.points_array[0]
            end   = self.points_array[len(self.points_array) - 1]
            high  = self.points_array[0]
            low   = self.points_array[0]
            rise  = 0.0
            fall  = 0.0
            slope = 0.0

            # find high, low and rise, fall points
            last = self.points_array[0]
            for p in self.points_array:
                if p > high:
                    high = p
                if p < low:
                    low = p
                if p > last:
                    rise += (p - last)
                if p < last:
                    fall += (p - last)
                last = p

            # end results as strings with 2 decimal places
            self.start_ft = "{0:.1f}".format(start)
            self.end_ft   = "{0:.1f}".format(end)
            self.high_ft  = "{0:.1f}".format(high)
            self.low_ft   = "{0:.1f}".format(low)

            # find how much of a rise and fall in feet there are from the avg height
            self.rise_ft = "{0:.1f}".format(rise)
            self.fall_ft = "{0:.1f}".format(fall)
        except Exception as e:
            log.warning(e)


class Place(object):
    def __init__(self, jsn, name=None):
        """ """
        self.name = jsn['name']
        self.lat  = jsn['lat']
        self.lon  = jsn['lon']
        self.stop = Stop.factory(jsn, self.name)
        self.map_img = self.make_img_url(lon=self.lon, lat=self.lat, icon=self.endpoint_icon(name))

    def endpoint_icon(self, name):
        """ """
        ret_val = ''
        if name:
            x='/extraparams/format_options=layout:{0}'
            if name in ['to', 'end', 'last']:
                ret_val = x.format('end')
            elif name in ['from', 'start', 'begin']:
                ret_val = x.format('start')

        return ret_val

    def make_img_url(self, url="//maps.trimet.org/eapi/ws/V1/mapimage/format/png/width/300/height/288/zoom/8/coord/%(lon)s,%(lat)s%(icon)s", **kwargs):
        return url % kwargs

    def append_url_params(self, route=None, month=None, day=None):
        if self.stop:
            self.stop.append_params_schedule_url(route, month, day)
            self.stop.append_params_info_url(month, day)

    @classmethod
    def factory(cls, jsn, obj=None, name=None):
        """ will create a Place object from json (jsn) data, 
            optionally assign the resultant object to some other object, as this alleviates the awkward 
            construct of 'from' that uses a python keyword, (e.g.,  self.__dict__['from'] = Place(j['from'])
        """
        p = Place(jsn, name)
        if obj and name:
            obj.__dict__[name] = p
        return p


class Alert(object):
    def __init__(self, jsn, route_id=None):
        self.type = 'ROUTE'
        self.route_id = route_id

        text = url = start_date = None
        try:
            """ OTP 0.10.x format
                "alerts":[
                {
                    "alertDescriptionText":{
                      "translations":{"":"The westbound stop on NE Dekum at M L King is closed for construction.  Use stop at 6th."},
                      "someTranslation":"The westbound stop on NE Dekum at M L King is closed for construction.  Use stop at 6th."},
                    "alertUrl":{
                          "translations":{"":"http://trimet.org/alerts/"},
                          "someTranslation":"http://trimet.org/alerts/"},
                    },
                    "effectiveStartDate":1473674400000
                }]
            """
            text = jsn['alertDescriptionText']['someTranslation']
            url = jsn['alertUrl']['someTranslation']
            start_date = jsn['effectiveStartDate']
        except:
            try:
                """ OTP 1.0 format
                   "alerts":[
                     {
                         "alertDescriptionText":"The westbound stop on NE Dekum at M L King is closed for construction.  Use stop at 6th.",
                         "effectiveStartDate":1473674400000,
                         "alertUrl":"http://trimet.org/alerts/"
                     }
                   ]
                """
                text = jsn['alertDescriptionText']
                url = jsn['alertUrl']
                start_date = jsn['effectiveStartDate']
            except:
                log.warn("couldn't parse alerts")

        self.text = text
        self.url = url

        # make sure we have a valid start date datetime
        try:
            dt = datetime.datetime.fromtimestamp(start_date / 1000)
            self.start_date = start_date
        except Exception as e:
            # import pdb; pdb.set_trace()
            dt = datetime.datetime.now()
            self.start_date = (dt - datetime.datetime(1970, 1, 1)).total_seconds()

        self.start_date_pretty = dt.strftime("%B %d").replace(' 0',' ')  # "Monday, March 4, 2013"
        self.start_time_pretty = dt.strftime(" %I:%M %p").replace(' 0',' ').lower().strip()  # "1:22 pm"
        self.long_term = True if datetime.datetime.today() - dt > timedelta(days=35) else False
        self.future = True if dt > datetime.datetime.today() else False

        # TODO: trimet hack (eliminate me)
        if "trimet.org" in self.url:
            self.url = "http://trimet.org/#alerts/"
            if self.route_id:
                self.url = "{0}{1}".format(self.url, self.route_id)

    @classmethod
    def factory(cls, jsn, route_id=None, def_val=None):
        """ returns either def_val (when no alerts in the jsn input), or a list of [Alert]s
        """
        ret_val = def_val
        if jsn and len(jsn) > 0:
            ret_val = []
            for a in jsn:
                alert = Alert(a, route_id)
                ret_val.append(alert)

        return ret_val


class Fare(object):
    """ 
    """
    def __init__(self, jsn, fares):
        self.adult = self.get_fare(jsn, '$2.50')
        if fares:
            self.adult_day = fares.query("adult_day", "$5.00")
            self.honored = fares.query("honored", "$1.25")
            self.honored_day = fares.query("honored_day", "$2.50")
            self.youth = fares.query("youth", "$1.25")
            self.youth_day = fares.query("youth_day", "$2.50")
            self.tram = fares.query("tram", "$4.70")
            self.notes = fares.query("notes")

    def get_fare(self, jsn, def_val):
        """  TODO -- need to figure out exceptions and populate self.note 
                  1) TRAM (GONDOLA) fare
                  2) $5.00 one-way fare, when the trip lasts longer than the transfer window
        """
        ret_val = def_val
        try:
            c = int(jsn['fare']['fare']['regular']['cents']) * 0.01
            s = jsn['fare']['fare']['regular']['currency']['symbol']
            ret_val = "%s%.2f" % (s, c)
        except Exception as e:
            pass
        return ret_val

    def update_fare_info(self,  def_val):
        """ read (periodically) a config file containing all fares an agency might present
        """
        ret_val = def_val
        try:
            if datetime.now() - self.last_update > timedelta(minutes = self.avert_timeout):
                log.warning("updating the advert content")
                self.last_update = datetime.now()
        except Exception as e:
            log.warning("ERROR updating the advert content {0}".format(e))

        return ret_val


class Stop(object):
    """
    """
    def __init__(self, jsn, name=None):
        # OLD OTP: "stop": {"agencyId":"TriMet", "name":"SW Arthur & 1st", "id":"143","info":"stop.html?stop_id=143", "schedule":"stop_schedule.html?stop_id=143"},
        # NEW OTP: "from": { "name":"SE 13th & Lambert","stopId":"TriMet:6693","stopCode":"6693","lon":-122.652906,"lat":45.468484,"arrival":1478551773000,"departure":1478551774000,"zoneId":"B","stopIndex":11,"stopSequence":12,"vertexType":"TRANSIT"}
        self.name     = name
        self.agency   = None
        self.id       = None
        self.get_id_and_agency(jsn)
        self.info     = self.make_info_url(id=self.id)
        self.schedule = self.make_schedule_url(id=self.id)

    def get_id_and_agency(self, jsn):
        try:
            # *.10.x format -- "stopId":{"agencyId":"TRIMET","id":"10579"}
            self.id = jsn['id']
            self.agency = jsn['agencyId']
        except Exception as e:
            # 1.0.x format -- "stopId":"TriMet:10579",
            try:
                s = jsn.split(':')
                self.id = s[1].strip()
                self.agency = s[0].strip()
            except Exception as e:
                log.warn("couldn't parse AGENCY nor ID from stop")

    def make_info_url(self, url="stop.html?stop_id=%(id)s", **kwargs):
        return url % kwargs

    def make_schedule_url(self, url="stop_schedule.html?stop_id=%(id)s", **kwargs):
        return url % kwargs

    def append_params_schedule_url(self, route, month, day):
        if self.schedule:
            if route:
                self.schedule += "&route={0}".format(route)
            if month and day:
                self.schedule += "&month={0}&day={1}".format(month, day)

    def append_params_info_url(self, month, day):
        if self.info:
            if month and day:
                self.info += "&month={0}&day={1}".format(month, day)

    @classmethod
    def factory(cls, jsn, name=None):
        ret_val = None
        stop_jsn = get_element(jsn, 'stopId')
        if stop_jsn:
            s = Stop(stop_jsn, name)
            ret_val = s
        return ret_val


class Route(object):
    def __init__(self, jsn):
        # TODO IMPORTANT
        # TODO We should probably use ott.data's DAO objects here ... very confusing to have multiple routes
        # TODO I know I wanted otp_to_ott.py to be standalone, but maybe that's a bad idea in terms of maintenance
        # TODO IMPORTANT

        # TODO this code is part of view.AgencyTemplate ... use a version of util.AgencyTemplate in the FUTURE
        self.route_id_cleanup = '\D.*'

        self.agency_id = jsn['agencyId']
        self.agency_name = get_element(jsn, 'agencyName')
        self.id = remove_agency_from_id(jsn['routeId'])
        self.name = self.make_name(jsn)
        self.headsign = get_element(jsn, 'headsign')
        self.trip = remove_agency_from_id(get_element(jsn, 'tripId'))
        url = self.url = get_element(jsn, 'url')
        if url is None:
            url = self.url = get_element(jsn, 'agencyUrl')
        self.url = url
        self.schedulemap_url = url

        # http://www.c-tran.com/routes/2route/map.html
        # http://trimet.org/schedules/r008.htm
        if self.agency_id.lower() == 'trimet':
            self.url = self.make_route_url("http://trimet.org/schedules/r{0}.htm")
            self.schedulemap_url = self.make_route_url("http://trimet.org/images/schedulemaps/{0}.gif")
        elif self.agency_id.lower() == 'psc':
            self.url = self.make_route_url("http://www.portlandstreetcar.org/node/3")
            self.schedulemap_url = self.make_route_url("http://www.portlandstreetcar.org/node/4")
        elif self.agency_id.lower() == 'c-tran':
            self.url = "http://c-tran.com/routes/{0}route/index.html".format(self.id)
            self.schedulemap_url = "http://c-tran.com/images/routes/{0}map.png".format(self.id)

    # TODO this code is part of view.AgencyTemplate ... use a version of util.AgencyTemplate in the FUTURE
    def clean_route_id(self, route_id):
        """ cleans the route_id parameter.  needed because TriMet started using id.future type route ids for route name changes
        """
        ret_val = route_id
        if self.route_id_cleanup:
            ret_val = re.sub(self.route_id_cleanup, '', route_id)
        return ret_val

    """ TODO: move to a single class that allows any agency to override & customize """
    def make_route_url(self, template):
        """ remove trailing x on route id, fill out the id with 3 zeros, pump that id thru the url template
        """
        id = self.clean_route_id(self.id)
        id = id.zfill(3)
        id = template.format(id)
        return id

    def make_name(self, jsn, name_sep='-', def_val=''):
        """ create a route name based on the returned json and the long & short names
            NOTE: we also handle a special case for interline legs
        """
        ret_val = def_val

        # step 1: interline name will use jsn['route'] in certain circumstances
        # NOTE:   we get some funky things with interline in the recent OTP code, where the record is the previous route
        #         not the new interline route.  So we'll build a name like MAX Yellow Line from the
        #         crap data we have fix this (temporarily)
        ln = get_element(jsn, 'routeLongName')
        if Leg.is_interline(jsn) and 'route' in jsn and len(jsn['route']) > 0 and not (jsn['route'] in ln or ln in jsn['route']):
            ret_val = jsn['route']
        else:
            # step 2: build up a route name using the short and long name(s) of the route

            # step 2a: grab short to go along with long name captured above
            sn = get_element(jsn, 'routeShortName')

            # step 2b: short name, ala '33' in 33-McLoughlin or '' for MAX Orange Line
            if sn and len(sn) > 0:
                if len(ret_val) > 0 and name_sep:
                    ret_val = ret_val + name_sep
                ret_val = ret_val + sn

            # step 2c: long name name, ala 'McLoughlin' in 33-McLoughlin, 'MAX Orange Line'
            if ln and len(ln) > 0:
                if len(ret_val) > 0 and name_sep:
                    ret_val = ret_val + name_sep
                ret_val = ret_val + ln
        return ret_val


class Step(object):
    def __init__(self, jsn):
        self.name = jsn['streetName']
        self.lat  = jsn['lat']
        self.lon  = jsn['lon']
        self.distance_meters = jsn['distance']
        self.distance_feet = m_to_ft(jsn['distance'])
        self.distance = pretty_distance(self.distance_feet)
        self.compass_direction = self.get_direction(get_element(jsn, 'absoluteDirection'))
        self.relative_direction = self.get_direction(get_element(jsn, 'relativeDirection'))

    @classmethod
    def get_direction(cls, dir):
        """ TODO localize me 
        """
        ret_val = dir
        try:
            ret_val = {
                'LEFT': dir.lower(),
                'RIGHT': dir.lower(),
                'HARD_LEFT': dir.lower().replace('_', ' '),
                'HARD_RIGHT': dir.lower().replace('_', ' '),
                'CONTINUE': dir.lower(),

                'NORTH': dir.lower(),
                'SOUTH': dir.lower(),
                'EAST': dir.lower(),
                'WEST': dir.lower(),
                'NORTHEAST': dir.lower(),
                'NORTHWEST': dir.lower(),
                'SOUTHEAST': dir.lower(),
                'SOUTHWEST': dir.lower(),
            }[dir]
        except Exception as e:
            pass

        return ret_val

    @classmethod
    def get_relative_direction(cls, dir):
        """ """
        ret_val = dir
        return ret_val


class Leg(object):
    """
    """
    def __init__(self, jsn):
        self.mode = jsn['mode']

        fm = Place.factory(jsn['from'], self, 'from')
        to = Place.factory(jsn['to'],   self, 'to')

        self.steps = self.get_steps(jsn)
        self.elevation = None
        if self.steps and 'steps' in jsn:
            self.elevation = Elevation(jsn['steps'])

        self.date_info = DateInfo(jsn)
        self.compass_direction = self.get_compass_direction()
        self.distance_meters = jsn['distance']
        self.distance_feet = m_to_ft(jsn['distance'])
        self.distance = pretty_distance(self.distance_feet)

        # transit related attributes
        self.route = None
        self.alerts = None
        self.transfer = None
        self.interline = None

        # mode specific config
        route_id = None
        if self.is_transit_mode():
            self.route = Route(jsn)
            route_id = self.route.id
            if 'alerts' in jsn:
                self.alerts = Alert.factory(jsn['alerts'], route_id=self.route.id)
            self.interline = self.is_interline(jsn)

        svc_date = date_utils.parse_month_day_year_string(self.date_info.service_date)
        fm.append_url_params(route_id, month=svc_date['month'], day=svc_date['day'])
        to.append_url_params(route_id, month=svc_date['month'], day=svc_date['day'])

    @classmethod
    def is_interline(cls, jsn):
        ret_val = False
        if 'interlineWithPreviousLeg' in jsn:
            ret_val = jsn['interlineWithPreviousLeg']
        return ret_val

    def is_transit_mode(self):
        return self.mode in ['BUS', 'TRAM', 'RAIL', 'TRAIN', 'SUBWAY', 'CABLECAR', 'GONDOLA', 'FUNICULAR', 'FERRY']

    def is_sea_mode(self):
        return self.mode in ['FERRY']

    def is_air_mode(self):
        return self.mode in ['GONDOLA']

    def is_non_transit_mode(self):
        return self.mode in ['BIKE', 'BICYCLE', 'WALK', 'CAR', 'AUTO']

    def get_steps(self, jsn):
        ret_val = None
        if 'steps' in jsn and jsn['steps'] and len(jsn['steps']) > 0:
            ret_val = []
            for s in jsn['steps']:
                step = Step(s)
                ret_val.append(step)

        return ret_val

    def get_compass_direction(self):
        ret_val = None
        if self.steps and len(self.steps) > 0:
            v = self.steps[0].compass_direction
            if v:
                ret_val = v

        return ret_val


class Itinerary(object):
    """
    """
    def __init__(self, jsn, itin_num, url, fares):
        self.dominant_mode = None
        self.selected = False
        self.has_alerts = False
        self.alerts = []
        self.url = url
        self.itin_num = itin_num
        self.transfers = jsn['transfers']
        self.fare = Fare(jsn, fares)
        self.date_info = DateInfoExtended(jsn)
        self.legs = self.parse_legs(jsn['legs'])

    def set_dominant_mode(self, leg):
        """ dominant transit leg -- rail > bus
        """
        if object_utils.has_content(self.dominant_mode) is False:
            self.dominant_mode = object_utils.safe_str(leg.mode).lower()

        if leg.is_transit_mode() and not leg.is_sea_mode():
            if self.dominant_mode != 'rail' and leg.mode == 'BUS':
                self.dominant_mode = 'bus'
            else:
                self.dominant_mode = 'rail'

    def parse_legs(self, legs):
        """
        """
        ret_val = []

        # step 1: build the legs
        for l in legs:
            leg = Leg(l)
            ret_val.append(leg)

        # step 2: find transfer legs e.g., this pattern TRANSIT LEG, WALK/BIKE LEG, TRANSIT LEG
        num_legs = len(ret_val) 
        for i, leg in enumerate(ret_val):
            self.set_dominant_mode(leg)
            if leg.is_transit_mode() and i+2 < num_legs: 
                if ret_val[i+2].is_transit_mode() and ret_val[i+1].is_non_transit_mode():
                    self.transfer = True

        # step 3: find 'unique' alerts and build an alerts object for the itinerary
        alerts_hash = {}
        for leg in ret_val:
            if leg.alerts:
                self.has_alerts = True
                try:
                    for a in leg.alerts:
                        alerts_hash[a.text] = a
                except Exception as e:
                    pass

        self.alerts = []
        for v in alerts_hash.values():
            self.alerts.append(v)

        return ret_val


class Plan(object):
    """ top level class of the ott 'plan' object tree

        contains these elements:
          self.from, self.to, self.params, self.arrive_by, self.optimize (plus other helpers 
    """
    def __init__(self, jsn, params=None, fares=None, path="planner.html?itin_num={0}"):
        """ creates a self.from and self.to element in the Plan object """
        Place.factory(jsn['from'], self, 'from')
        Place.factory(jsn['to'],   self, 'to')
        self.itineraries = self.parse_itineraries(jsn['itineraries'], path, params, fares)
        self.set_plan_params(params)

    def parse_itineraries(self, itineraries, path, params, fares):
        """  TODO explain me...
        """
        ret_val = []
        for i, jsn in enumerate(itineraries):
            itin_num = i+1
            url_params = None
            if params: 
                url_params = params.ott_url_params()
            url = self.make_itin_url(path, url_params, itin_num)
            itin = Itinerary(jsn, itin_num, url, fares)
            ret_val.append(itin)

        # set the selected 
        selected = self.get_selected_itinerary(params, len(ret_val))
        if selected >= 0 and selected < len(ret_val):
            ret_val[selected].selected = True

        return ret_val

    def make_itin_url(self, path, query_string, itin_num):
        """
        """
        ret_val = None
        try:
            ret_val = path.format(itin_num)
            if query_string:
                ret_val = "{0}&{1}".format(ret_val, query_string)
        except Exception as e:
            log.warn("make_itin_url exception")

        return ret_val

    def get_selected_itinerary(self, params, max=3):
        """ return list position (index starts at zero) of the 'selected' itinerary
            @see ParamParser
        """
        ret_val = 0
        if params:
            ret_val = params.get_itin_num_as_int()
            ret_val -= 1  # decrement value because we need an array index, eg: itin #1 == itin[0]

        # final check to make sure we don't over-index the list of itineraries
        if ret_val < 0 or ret_val >= max:
            ret_val = 0

        return ret_val

    def pretty_mode(self, mode):
        """ TOD0 TODO TODO localize
        """
        ret_val = 'Transit'
        if 'BICYCLE' in mode and ('TRANSIT' in mode or ('RAIL' in mode and 'BUS' in mode)):
            ret_val = 'Bike to Transit'
        elif 'BICYCLE' in mode and 'RAIL' in mode:
            ret_val = 'Bike to Rail'
        elif 'BICYCLE' in mode and 'BUS' in mode:
            ret_val = 'Bike to Bus'
        elif 'TRANSIT' in mode:
            ret_val = 'Transit'
        elif 'BUS' in mode:
            ret_val = 'Bus'
        elif 'RAIL' in mode:
            ret_val = 'Rail'
        elif 'BICYCLE' in mode:
            ret_val = 'Bike'
        elif 'WALK' in mode:
            ret_val = 'Walk'
        return ret_val

    def dominant_transit_mode(self, i=0):
        """ TODO ... make better...parse itin affect adverts (at least) """
        ret_val = 'rail'
        if len(self.itineraries) < i:
            i = len(self.itineraries) - 1
        if i >= 0 and self.itineraries:
            ret_val = self.itineraries[i].dominant_mode

        return ret_val

    def set_plan_params(self, params):
        """ passed in by a separate routine, rather than parsed from returned itinerary
        """
        if params:
            self.params  = {
                "is_arrive_by" : params.arrive_depart,
                "optimize"     : params.optimize,
                "map_planner"  : params.map_url_params(),
                "edit_trip"    : params.ott_url_params(),
                "return_trip"  : params.ott_url_params_return_trip(),
                "modes"        : self.pretty_mode(params.mode),
                "walk"         : pretty_distance_meters(params.walk_meters)
            }
        else:
            self.params = {}
        self.max_walk = "1.4"


"""
UTILITY METHODS
"""
def get_element(jsn, name, def_val=None):
    """
    """
    ret_val = def_val
    try:
        v = jsn[name]
        if type(def_val) == int:
            ret_val = int(v)
        else:
            ret_val = v
    except Exception as e:
        log.debug(name + " not an int value in jsn")
    return ret_val


def ms_to_minutes(ms, is_pretty=False, show_hours=False):
    ret_val = ms / 1000 / 60

    # pretty '3 hours & 1 minute' string
    if is_pretty:
        h_str = ''
        m_str = ''

        # calculate hours string
        m = ret_val
        if show_hours and m > 60:
            h = int(math.floor(m / 60))
            m = int(m % 60)
            if h > 0:
                hrs =  'hour' if h == 1 else 'hours'
                h_str = '%d %s' % (h, hrs)
                if m > 0:
                    h_str = h_str + ' ' + '&' + ' '

        # calculate minutes string
        if m > 0:
            mins = 'minute' if m == 1 else 'minutes'
            m_str = '%d %s' % (m, mins)

        ret_val = '%s%s' % (h_str, m_str) 

    return ret_val


def hour_min_string(h, m, fmt='{0} {1}', sp=', '):
    ret_val = None
    if h and h > 0:
        hr = 'hours' if h > 1 else 'hour'
        ret_val = "{0} {1}".format(h, hr)
    if m:
        min = 'minutes' if m > 1 else 'minute'
        pre = '' if ret_val is None else ret_val + sp 
        ret_val = "{0}{1} {2}".format(pre, m, min)
    return ret_val


def seconds_to_hours_minutes(secs, def_val=None, min_secs=60):
    """
    """
    min = def_val
    hour = def_val
    if secs > min_secs:
        m = math.floor(secs / 60)
        min = m % 60
        if m >= 60:
            m = m - min
            hour = int(math.floor(m / 60))
    return hour,min


def m_to_ft(m):
    ret_val = float(m) * 3.28
    return ret_val


def distance_dict(distance, measure):
    return {'distance':distance, 'measure':measure}


def pretty_distance(feet):
    """ TODO localize
    """
    ret_val = ''

    if feet <= 1.0:
        ret_val = distance_dict(1, 'foot')
    elif feet < 1000:
        ret_val = distance_dict(int(feet), 'feet')
    elif feet < 1500:
        ret_val = distance_dict('1/4', 'mile')
    elif feet < 2200:
        ret_val = distance_dict('1/3', 'mile')
    elif feet < 3100:
        ret_val = distance_dict('1/2', 'mile')
    elif feet < 4800:
        ret_val = distance_dict('3/4', 'mile')
    elif feet < 5400:
        ret_val = distance_dict('1', 'mile')
    else:
        ret_val = distance_dict(round(feet / 5280, 1), 'miles')
    return ret_val


def pretty_distance_meters(m):
    """
    """
    ret_val = m
    try:
        d = pretty_distance(float(m) * 3.28)
        ret_val = "{distance} {measure}".format(**d)
    except Exception as e:
        log.warn("pretty distance meters")
    return ret_val


def main():
    argv = sys.argv

    if argv and len(argv) > 1 and ('new' in argv or 'n' in argv):
        file = 'new/pdx2ohsu.json'
    elif argv and len(argv) > 1 and not ('pretty' in argv or 'p' in argv):
        file = argv[1]
    else:
        file = 'old/pdx2ohsu.json'

    try:
        f = open(file)
    except Exception as e:
        path = "{0}/{1}".format('ott/otp_client/tests', file)
        f = open(path)

    j = json.load(f)
    p = Plan(j['plan'])
    pretty = False
    if argv:
        pretty = 'pretty' in argv or 'p' in argv
    y = json_utils.json_repr(p, pretty)
    print y


if __name__ == '__main__':
    main()
