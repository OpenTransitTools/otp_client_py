from ott.utils import json_utils

import sys
import urllib
import logging
log = logging.getLogger(__file__)


class Base(object):
    id = "ID HERE"
    agencyName = "AGENCY ID HERE"

    def __init__(self, args={}):
        self.id = args.get('id', self.id)
        self.agencyName = args.get('agencyName', self.agencyName)

    def set(self, name, src={}, always_cpy=True):
        if always_cpy or src.get(name):
            self[name] = src.get(name, self[name])


def main():
    argv = sys.argv
    if 'route' in argv:
        from .routes import Routes
        o = Routes()
    else:
        o = Base()
    print(o.__dict__)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
