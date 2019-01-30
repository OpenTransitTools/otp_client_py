import os
import unittest

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops


def get_db():
    from gtfsdb import api, util
    from ott.utils import file_utils
    dir = file_utils.get_module_dir(Routes)
    gtfs_file = os.path.join(dir, '..', 'tests', 'data', 'gtfs', 'multi-date-feed.zip')
    gtfs_file = gtfs_file.replace('c:\\', '/').replace('\\', '/')
    gtfs_file = "file://{0}".format(gtfs_file)
    gtfs_file = gtfs_file.replace('\\', '/')

    url = util.make_temp_sqlite_db_uri('curr')
    db = api.database_load(gtfs_file, url=url, current_tables=True)
    return db


class TiTest(unittest.TestCase):
    db = None

    def setUp(self):
        if TiTest.db is None:
            self.db = get_db()
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
        self.assertTrue(routes[0].get('id') == 'DTA:OLD')

        # test an old stop querying it's route list (assigned to DTA:ALWAYS route, but don't show due to OLD stop)
        routes = Routes.stop_routes_factory(self.db.session, 'OLD', date="9-15-2018")
        self.assertTrue(len(routes) == 1)
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

        # test querying old stop, but with current date ... so no results, since stop is not in CurrentStops
        routes = Routes.stop_routes_factory(self.db.session, 'OLD')
        self.assertTrue(len(routes) == 0)

    def test_bbox_stops(self):
        # TODO !!!
        pass
        # stops = Stops.stop()
        #import pdb; pdb.set_trace()
        #for r in routes: print(r)
