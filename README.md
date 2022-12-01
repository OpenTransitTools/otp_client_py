otp_client_py
===============

Python client for OTP

Install and run example app:
  1. install python 3.x, along with zc.buildout and git
  2. git clone https://github.com/OpenTransitTools/otp_client_py.git
  3. cd otp_client_py
  4. buildout 
  5. buildout (workaround for issue during build) 
  6. bin/trip_planner "from=pdx&to=zoo" trimet p

This code has been tested to run TriMet's instance of OTP and SOLR geocoder.  To get another OTP instance and/or SOLR geocoder up and running, see opentripplanner.org (v *.10.x) and geocoder project.
