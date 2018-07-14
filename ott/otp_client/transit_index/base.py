from ott.utils import json_utils
from ott.utils import object_utils

import sys
import logging
log = logging.getLogger(__file__)


class Base(object):

    def __init__(self, args={}):
        object_utils.safe_set_from_dict(self, 'id', args)
        object_utils.safe_set_from_dict(self, 'agencyName', args)


def main():
    #import pdb; pdb.set_trace()
    argv = sys.argv
    if 'routes' in argv:
        from .routes import Routes
        o = Routes()
    elif 'stops' in argv:
        from .stops import Stops
        o = Stops()
    else:
        o = Base()

    print(o.__dict__)


if __name__ == '__main__':
    main()
