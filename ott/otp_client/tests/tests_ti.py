import os
import unittest

from ott.otp_client.transit_index.routes import Routes


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

    def test_all_routes(self):
        # import pdb; pdb.set_trace()
        # import pdb; pdb.set_trace()
        dao = Routes.route_list_factory(self.db.session)
        for r in dao.routes:
            print(r)

        self.assertTrue(len(dao.routes) == 2)
        self.assertTrue(dao.routes[0].route_id in ('NEW', 'ALWAYS'))
        self.assertTrue(dao.routes[1].route_id in ('NEW', 'ALWAYS'))

    def test_bbox_stops(self):
        pass
