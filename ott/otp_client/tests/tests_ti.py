import os
import unittest

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops
from ott.utils.geo.bbox import BBox
from ott.utils.geo.point import Point

from .base import *


class TiTest(unittest.TestCase):
    db = None
    DO_PG = False
    PG_URL = "postgresql://ott@localhost:5432/ott"
    PG_SCHEMA = "current_test"

    def setUp(self):
        # import pdb; pdb.set_trace()
        if TiTest.db is None:
            if self.DO_PG:
                self.db = load_pgsql(self.PG_URL, self.PG_SCHEMA)
            else:
                self.db = load_sqlite()

            TiTest.db = self.db

    def test_route(self):
        # test current routes
        route = Routes.route_factory(self.db.session, 'NEW')
        self.assertTrue(route.get('id') == 'DTA:NEW')

        route = Routes.route_factory(self.db.session, 'OLD')
        self.assertTrue(route.get('id') == 'DTA:OLD')

        route = Routes.route_factory(self.db.session, 'ALWAYS')
        self.assertTrue(route.get('id') == 'DTA:ALWAYS')

    def test_routes_list(self):
        # test current routes
        routes = Routes.route_list_factory(self.db.session)
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))

        # test query of routes via date (slower)
        routes = Routes.route_list_factory(self.db.session, date="9-15-2018")
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

    def test_stop_routes(self):
        # test current stop querying it's route list
        routes = Routes.stop_routes_factory(self.db.session, 'DADAN')
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))

        # test an old stop querying it's route list (assigned to DTA:OLD route)
        routes = Routes.stop_routes_factory(self.db.session, 'EMSI', date="9-15-2018")
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

        # test an old stop querying it's route list (assigned to DTA:ALWAYS route, but don't show due to OLD stop)
        routes = Routes.stop_routes_factory(self.db.session, 'OLD', date="9-15-2018")
        self.assertTrue(len(routes) == 1)
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

        # test querying old stop, but with current date ... so no results, since stop is not in CurrentStops
        routes = Routes.stop_routes_factory(self.db.session, 'OLD')
        self.assertTrue(len(routes) == 0)

    def test_stop_query(self):
        stop = Stops.stop(self.db.session, 'NEW')
        self.assertTrue(stop)
        self.assertTrue(stop.routes == '50')

        stop = Stops.stop(self.db.session, 'OLD', def_val=None)
        self.assertTrue(stop == None)

    def test_bbox_stops(self):
        if self.DO_PG:
            bbox = BBox(min_lat=36.0, max_lat=37.0, min_lon=-117.5, max_lon=-116.0)
            stops = Stops.bbox_stops(self.db.session, bbox)
            self.assertTrue(len(stops) > 5)

    def test_point_stops(self):
        if self.DO_PG:
            #import pdb; pdb.set_trace()
            point = Point(x=-117.15, y=36.43)
            stops = Stops.nearest_stops(self.db.session, point)
            self.assertTrue(len(stops) > 5)
            self.assertTrue(stops[0].get('dist') > 1000 and stops[0].get('dist') < 2000)
