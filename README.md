otp_client_py
===============

Python client for OTP

Install and run example app:
  0. install python 2.7, along with zc.buildout and easy_install, git
  1. git clone https://github.com/OpenTransitTools/otp_client_py.git
  2. cd otp_client_py
  3. buildout
  4. bin/trip_planner "from=pdx&to=zoo" trimet p

This code has been tested to run TriMet's instance of OTP and SOLR geocoder.  To get another OTP instance and/or SOLR geocoder up and running, see opentripplanner.org (v *.10.x) and geocoder project.
