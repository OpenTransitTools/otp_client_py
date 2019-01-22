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

    def test_current_routes(self):
        routes = Routes.route_list_factory(self.db.session)
        #import pdb; pdb.set_trace()
        #for r in routes: print(r)

        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:NEW', 'DTA:ALWAYS'))

    def test_old_routes(self):
        routes = Routes.route_list_factory(self.db.session, date="9-15-2018")
        #import pdb; pdb.set_trace()
        #for r in routes: print(r)

        self.assertTrue(len(routes) == 2)
        self.assertTrue(routes[0].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))
        self.assertTrue(routes[1].get('id') in ('DTA:OLD', 'DTA:ALWAYS'))

    def test_bbox_stops(self):
        #stops = Stops.stop()
        #import pdb; pdb.set_trace()
        #for r in routes: print(r)

