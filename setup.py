import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'ott.utils',
    'ott.geocoder',
    'ott.data[postgresql]',

    'simplejson',
    'python-dateutil',

    'pyramid',
    'pyramid_tm',
    'pyramid_exclog',
    'waitress==2.1.1',

    'venusian==1.2.0',
    'protobuf<3.0' # 3.x requires 'six>=1.9' ... but some other lib wants six=1.4
]

extras_require = dict(
    dev=[],
)

setup(
    name='ott.otp_client',
    version='0.1.0',
    description='Open Transit Tools - OTT Database',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="Open Transit Tools",
    author_email="info@opentransittools.org",
    dependency_links=[
        'git+https://github.com/OpenTransitTools/utils.git#egg=ott.utils-0.1.0',
        'git+https://github.com/OpenTransitTools/data.git#egg=ott.data-0.1.0',
        'git+https://github.com/OpenTransitTools/geocoder.git#egg=ott.geocoder-0.1.0'
    ],
    license="Mozilla-derived (http://opentransittools.com)",
    url='http://opentransittools.com',
    keywords='ott, otp, gtfs, gtfsdb, data, database, services, transit',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    extras_require=extras_require,
    tests_require=requires,
    test_suite="ott.otp_client.tests",
    entry_points="""\
        [paste.app_factory]
        main = ott.otp_client.pyramid.app:main

        [console_scripts]
        parse_otp_json = ott.otp_client.otp_to_ott:main
        trip_planner = ott.otp_client.trip_planner:main
        ti = ott.otp_client.transit_index.base:main
    """,
)
