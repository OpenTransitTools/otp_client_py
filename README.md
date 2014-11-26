otp_client_py
===============

Python client for OTP

Install and run example app:
  0. install python 2.7, along with zc.buildout and easy_install, git
  1. git clone https://github.com/OpenTransitTools/otp_client_py.git
  2. git clone projects https://github.com/OpenTransitTools/utils.git and https://github.com/OpenTransitTools/geocode.git (see http://opentransittools.com)
  3. cd otp_client_py
  4. buildout
  5. bin/python ott/otp_client/trip_planner.py "from=pdx&to=zoo" trimet p 

This code has been tested to run TriMet's instance of OTP and SOLR geocoder.  To get another OTP instance and/or SOLR geocoder up and running, see opentripplanner.org (v *.10.x) and geocoder project.
