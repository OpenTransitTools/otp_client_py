import os
import unittest

from ott.otp_client.transit_index.routes import Routes
from ott.otp_client.transit_index.stops import Stops
from ott.utils.geo.bbox import BBox
from ott.utils.geo.point import Point

from .base import *


class TiTestGeo(unittest.TestCase):
    """ test gtsdb trimet queries via geom junk"""
    db = None
    DO_PG = False

    def setUp(self):
        if TiTestGeo.db is None:
            from .tests_ti import TiTest
            if TiTest.DO_PG:
                self.DO_PG = True
                self.db = get_pg_db(TiTest.PG_URL, 'trimet')

    def test_bbox_stops(self):
        if self.DO_PG:
            bbox = BBox(min_lat=45.530, max_lat=45.535, min_lon=-122.665, max_lon=-122.667)
            stops = Stops.bbox_stops(self.db.session, bbox)
            self.assertTrue(len(stops) > 5)

    def test_point_stops(self):
        # import pdb; pdb.set_trace()
        if self.DO_PG:
            point = Point(x=-122.6664, y=45.53)
            stops = Stops.nearest_stops(self.db.session, point)
            self.assertTrue(len(stops) > 5)
