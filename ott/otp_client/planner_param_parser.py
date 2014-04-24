'''
'''
import re
import time
import datetime
import calendar
import logging
log = logging.getLogger(__file__)

from param_parser import ParamParser
from ott.controller.util import config
from ott.controller.util import object_utils

class PlannerParamParser(ParamParser):

    def __init__(self, params):
        super(PlannerParamParser, self).__init__(params)

        self.frm   = None
        self.to    = None
        self._parse_from()
        self._parse_to()

        self.date  = None
        self.time  = None
        self.day   = None
        self.month = None
        self.year  = None
        self.hour  = None
        self.min   = None
        self.am_pm = None
        self.max_hours = config.get_int('otp_max_hours', 6)
        self._parse_date()
        self._parse_time()

        self.arrive_depart_raw = None
        self.arrive_depart = None
        self.do_first    = False  # TODO ... Arrive / Depart / First Trip / Last Trip
        self.do_last     = False
        self.optimize    = None
        self.walk        = None
        self.walk_meters = 0.0
        self.mode        = None
        self._parse_arrive_depart()
        self._parse_optimize()
        self._parse_walk()
        self._parse_mode()
        self._parse_misc()


    def safe_format(self, fmt, def_val=''):
        ''' 
        '''
        ret_val = def_val
        try:
            ret_val = fmt.format(**self.__dict__)
        except UnicodeEncodeError, e:
            log.debug(e)
            log.debug('trying to fix the encoding with the frm & to coords')
            self.frm = object_utils.to_str(self.frm)
            self.to  = object_utils.to_str(self.to)
            try:
                ret_val = fmt.format(**self.__dict__)
            except:
                pass

        except Exception, e:
            log.debug(e)
        return ret_val

    def pretty_output(self):
        return self.param_exists('pretty') or self.param_exists('is_pretty')

    def ott_url_params(self, fmt="from={frm}&to={to}&Hour={hour}&Minute={min}&AmPm={am_pm}&maxHours={max_hours}&month={month}&day={day}&year={year}&Walk={walk}&Arr={arrive_depart_raw}&min={optimize}&mode={mode}"):
        ''' return a string with the parameter values formatted for the OTT webapps
        '''
        ret_val = self.safe_format(fmt)
        ret_val = object_utils.fix_url(ret_val)
        return ret_val

    def ott_url_params_return_trip(self, add_hours=1, add_mins=30, fmt="from={to}&to={frm}&month={month}&day={day}&year={year}&Walk={walk}&Arr={arrive_depart_raw}&min={optimize}&mode={mode}"):
        ''' return a string with the parameter values formatted for OTT with a return trip of hours+X and minutes+Y 
            (change am to pm if needed, etc...)
        '''
        fmt = "Hour={add_hour}&Minute={add_min}&AmPm={add_am_pm}&maxHours={max_hours}&" + fmt

        # handle the extra minutes for the reverse trip (increment hours if need be)
        self.add_min = self.to_int(self.min) + add_mins
        if self.add_min > 60:
            self.add_min = self.to_int(self.add_min % 60)
            add_hours += 1

        # handle the extra hours (change am / pm if we go past 12 hour mark)
        self.add_am_pm = self.am_pm
        self.add_hour = self.to_int(self.hour) + add_hours
        if self.add_hour > 12:
            self.add_hour = self.add_hour - 12
            if self.add_am_pm == 'pm':
                self.add_am_pm = 'am'
            else:
                self.add_am_pm = 'pm'

        ret_val = self.safe_format(fmt)
        ret_val = object_utils.fix_url(ret_val)
        return ret_val


    def otp_url_params(self, fmt="fromPlace={frm}&toPlace={to}&time={time}&maxHours={max_hours}&date={date}&mode={mode}&optimize={optimize}&maxWalkDistance={walk_meters}&arriveBy={arrive_depart}"):
        ''' return a string with the parameter values formatted for the OTP routing engine (opentripplanner-api-webapp)
        '''
        ret_val = self.safe_format(fmt)
        ret_val = ret_val.replace("False", "false").replace("True", "true")
        ret_val = object_utils.fix_url(ret_val)
        return ret_val

    def map_url_params(self, fmt="from={frm}&to={to}&time={time}&maxHours={max_hours}&date={month}/{day}/{year}&mode={mode}&optimize={optimize}&maxWalkDistance={walk_meters:.0f}&arriveBy={arrive_depart}"):
        ''' return a string with the parameter values formatted for the OTT webapps
            http://maps.trimet.org/prod?
                toPlace=ZOO%3A%3A45.509700%2C-122.716290
                fromPlace=PDX%3A%3A45.587647%2C-122.593173
                time=5%3A30%20pm
                date=2013-06-13
                mode=TRANSIT%2CWALK
                optimize=QUICK
                maxWalkDistance=420
                arriveBy=true
        '''
        ret_val = self.safe_format(fmt)
        ret_val = ret_val.replace("False", "false").replace("True", "true")
        ret_val = object_utils.fix_url(ret_val)
        return ret_val


    def get_itin_num(self, def_val="1"):
        ret_val = def_val
        if 'itin_num' in self.params:
            ret_val = self.params['itin_num']
        return ret_val

    def get_itin_num_as_int(self, def_val=1):
        ret_val = self.get_itin_num()
        try:
            ret_val = self.to_int(ret_val)
        except: 
            log.info("params['itin_num'] has a value of {0} (it's not parsing into an int)".format(ret_val))
            ret_val = def_val
        return ret_val 

    def get_from(self, def_val=None):
        ret_val = def_val
        if self.frm:
            ret_val = self.frm 
        return ret_val

    def get_to(self, def_val=None):
        ret_val = def_val
        if self.to:
            ret_val = self.to 
        return ret_val

    def _parse_from(self):
        ''' parse out the trip origin from get params ... the value could be a string, a coordinate or combo of the two
        '''
        name = self.get_first_val(['from', 'fromPlace', 'f'])
        if name:
            self.frm = object_utils.to_str(name)
            pos = name.find('::')
            if pos < 0 or pos - 2 >= len(name):
                coord = self.get_first_val(['fromCoord'])
                if coord:
                    self.frm = self.make_named_coord(name, coord)
                else:
                    lat = self.get_first_val(['fromLat', 'fLat'])
                    lon = self.get_first_val(['fromLon', 'fLon'])
                    if lat and lon:
                        coord = "{0},{1}".format(lat, lon)
                        self.frm = self.make_named_coord(name, coord)


    def _parse_to(self):
        ''' parse out the trip destination from get params ... the value could be a string,a coordinate or combo of the two
        '''
        name = self.get_first_val(['to', 'toPlace', 't'])
        if name:
            self.to = object_utils.to_str(name)
            pos = name.find('::')
            if pos < 0 or pos - 2 >= len(name):
                coord = self.get_first_val(['toCoord'])
                if coord:
                    self.to = self.make_named_coord(name, coord)
                else:
                    lat = self.get_first_val(['toLat', 'tLat'])
                    lon = self.get_first_val(['toLon', 'tLon'])
                    if lat and lon:
                        coord = "{0},{1}".format(lat, lon)
                        self.to = self.make_named_coord(name, coord)


    def _parse_walk(self):
        ''' parse out the max walk (bike) distance ... default to 3/4 mile (~1260 meters)
        '''
        self.walk = self.get_first_val(['walk', 'Walk'], "1260")

        try:
            dist = float(self.walk)
            self.walk_meters = dist

            # self.walk value of less than 11 implies this is a fraction of a mile
            # (note OTP values are in meters, thus 1609 = number of meters in a mile)
            if dist and dist <= 10.0:
                self.walk_meters = 1609 * dist
        except:
            pass

    def _parse_arrive_depart(self):
        ''' parse out the arrive / depart string
        '''
        self.arrive_depart = False
        val = self.get_first_val(['Arr', 'arr'])
        if val:
            self.arrive_depart_raw = val
            if val in ('A', 'Arr', 'Arrive', 'True', 'true'):
                self.arrive_depart = True
            if val in ('L', 'Late', 'Latest'):
                self.arrive_depart = True
                self.time = "1:30am"
            if val in ('E', 'Early', 'Earliest'):
                self.arrive_depart = False
                self.time = "4:00am"

    def _parse_misc(self):
        ''' parse everything else for a param'''
        mh = self.get_first_val_as_int(['maxHours'])
        if mh:
            self.max_hours = mh


    def _parse_mode(self):
        ''' parse out the mode string ... and default to TRANSIT,WALK
            convert mode string, if it's legacy, to OTP mode strings 
        '''
        self.mode = self.get_first_val(['mode', 'Mode'])

        # order is important....
        if self.mode is None:
            self.mode = 'TRANSIT,WALK'
        elif self.mode == 'WALK':
            self.mode = 'WALK'
        elif 'TRANS' in self.mode and 'BIC' in self.mode:
            self.mode = 'TRANSIT,BICYCLE'
        elif 'TRAIN' in self.mode and 'BIC' in self.mode:
            self.mode = 'TRAINISH,BICYCLE'
        elif self.mode == 'BIKE' or self.mode =='BICYCLE':
            self.mode = 'BICYCLE'
        elif self.mode in ('B', 'BUS', 'BUSISH', 'BUSISH,WALK'):
            self.mode = 'BUSISH,WALK'
        elif self.mode in ('T', 'TRAIN', 'TRAINISH', 'TRAINISH,WALK'):
            self.mode = 'TRAINISH,WALK'
        else:
            self.mode = 'TRANSIT,WALK'

    def _parse_optimize(self):
        ''' parse out the optimize flag
        '''
        #import pdb; pdb.set_trace()
        self.optimize = self.get_first_val(['optimize', 'opt', 'Opt', 'min', 'Min'])
        if self.optimize in ('F', 'X', 'TRANSFERS'):
            self.optimize = 'TRANSFERS'
        elif self.optimize in ('S', 'SAFE'):
            self.optimize = 'SAFE'
        else:
            self.optimize = 'QUICK'

