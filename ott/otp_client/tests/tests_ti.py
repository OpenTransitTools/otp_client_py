import os
import unittest

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops


DB = None
def get_db():
    from gtfsdb import api
    from ott.utils import file_utils
    from gtfsdb import util
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
        global DB
        if DB is None:
            DB = get_db()
        self.db = DB

    def tearDown(self):
        pass

    def test_routes(self):
        # test current routes
        routes = Routes.route_list_factory(self.db.session)
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))

        # test query of routes via date (slower)
        #import pdb; pdb.set_trace()
        routes = Routes.route_list_factory(self.db.session, date="9-15-2018")
        # for r in routes: print(r)
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

    def test_stop_routes(self):
        routes = Routes.stop_routes_factory(self.db.session, 'DADAN')
        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))

        routes = Routes.stop_routes_factory(self.db.session, 'OLD', date="9-15-2018")
        self.assertTrue(len(routes) == 1)

        routes = Routes.stop_routes_factory(self.db.session, 'OLD')
        self.assertTrue(len(routes) == 0)

    def test_bbox_stops(self):
        pass
        # stops = Stops.stop()
        #import pdb; pdb.set_trace()
        #for r in routes: print(r)
