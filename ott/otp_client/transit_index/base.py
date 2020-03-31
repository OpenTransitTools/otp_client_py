from ott.utils import object_utils

import sys
import logging
log = logging.getLogger(__file__)


class Base(object):
    """
    Base class for OpenTripPlanner (OTP) Transit Index (TI) web services

    Park & Rides:
        https://<domain & port>/otp/routers/default/park_and_ride

    Routes and Routes serving a stop:
        https://<domain & port>/otp/routers/default/index/routes
        https://<domain & port>/otp/routers/default/index/stops/TriMet:5516/routes

    Stops:
        https://<domain & port>/otp/routers/default/index/stops?
          minLat=45.50854243338104&maxLat=45.519789433696744&minLon=-122.6960849761963&maxLon=-122.65591621398927

        https://<domain & port>/otp/routers/default/index/stops?
          radius=1000&lat=45.4926336&lon=-122.63915519999999

    Stop Schedules:
        https://<domain & port>/otp/routers/default/index/stops/TriMet:823/stoptimes?timeRange=14400
    """
    def __init__(self, args={}):
        object_utils.safe_set_from_dict(self, 'id', args)
        object_utils.safe_set_from_dict(self, 'agencyName', args)

    @classmethod
    def mock(cls):
        return []


def main():
    # import pdb; pdb.set_trace()
    argv = sys.argv
    if 'routes' in argv:
        from .routes import Routes
        list = Routes.mock()
    elif 'stops' in argv:
        from .stops import Stops
        list = Stops.mock()
    elif 'pat' in argv:
        from .patterns import Patterns
        list = Patterns.mock()
    else:
        list = Base.mock()

    print("HI")
    for o in list:
        print(o)
    print("BYE")


if __name__ == '__main__':
    main()
