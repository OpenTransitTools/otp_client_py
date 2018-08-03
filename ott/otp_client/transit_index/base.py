from ott.utils import json_utils
from ott.utils import object_utils

import sys
import logging
log = logging.getLogger(__file__)


class Base(object):

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
    else:
        list = Base.mock()

    for o in list:
        print(o)


if __name__ == '__main__':
    main()
