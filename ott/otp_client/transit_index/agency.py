class Agency():

    @classmethod
    def from_gtfsdb_factory(cls, agency):
        """
        {
          'agency_id': u'TRIMET'
          'agency_name': u'TriMet'
          'agency_url': u'http://trimet.org/'
          'agency_fare_url': u'http://trimet.org/fares/',
          'agency_timezone': u'America/Los_Angeles',
          'agency_lang': u'en',
          'agency_email': u'customerservice@trimet.org'
        }
        """
        # import pdb; pdb.set_trace()
        a = Agency()
        a.id = agency.agency_id
        a.name = agency.agency_name
        a.url = agency.agency_url
        a.fareUrl = agency.agency_fare_url
        a.timezone = agency.agency_timezone
        a.lang = agency.agency_lang
        a.phone = agency.agency_phone
        return a
