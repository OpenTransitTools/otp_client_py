otp_client_py
===============

Python client for OTP

Install and run tests:
0) musts: Python 2.7, setup tools and buildout installed locally on your system
1) git clone projects utils and geocode projects (see http://opentransittools.com)
2) git clone otp_client_py
3) cd otp_client_py
4) buildout
5) bin/python ott/otp_client/trip_planner.py "from=pdx&to=zoo" trimet p 

This code has been tested to run TriMet's instance of OTP and SOLR geocoder.  To get another OTP instance and/or SOLR geocoder up and running, see opentripplanner.org (v *.10.x) and geocoder project.


