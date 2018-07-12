from ott.utils import object_utils

from .base import Base

import logging
log = logging.getLogger(__file__)


class Stops(Base):
    """
    https://<domain & port>/otp/routers/default/index/routes
    https://<domain & port>/otp/routers/default/index/stops?
      minLat=45.50854243338104&maxLat=45.519789433696744&minLon=-122.6960849761963&maxLon=-122.65591621398927
    [
        {
            id: TriMet:4026
            code: 4026
            name: SE Morrison & 9th
            lat: 45.517303
            lon: -122.656536
            url: http://trimet.org/#tracker/stop/4026
        }
    ]
    """
    code = "CODE (stop id)"
    name = "STOP NAME"
    lat = "STOP LAT"
    lon = "STOP LON"
    url = "STOP URL"

    mode = "RAIL"

    def __init__(self, args={}):
        super(Stops, self).__init__(args)
        object_utils.safe_set_from_dict(self, 'code', args)
        object_utils.safe_set_from_dict(self, 'name', args)
        object_utils.safe_set_from_dict(self, 'lat', args)
        object_utils.safe_set_from_dict(self, 'lon', args)
        object_utils.safe_set_from_dict(self, 'url', args)
        object_utils.safe_set_from_dict(self, 'mode', args, def_val="BUS")

    @classmethod
    def factory(cls):
        pass
