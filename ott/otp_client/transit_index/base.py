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
        try:
            if always_cpy or name in src:
                def_val = getattr(self, name)
                val = src.get(name, def_val)
                setattr(self, name, val)
        except Exception as e:
            log.info(e)

def main():
    #import pdb; pdb.set_trace()
    argv = sys.argv
    if 'routes' in argv:
        from .routes import Routes
        o = Routes()
    else:
        o = Base()
    print(o.__dict__)


if __name__ == '__main__':
    main()
