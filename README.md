# Uber Pickups in New York City
This file contains raw data on pickups from a non-Uber FHV company. The trip information varies by company, but can include day of trip, time of trip, pickup location, driver's for-hire license number, and vehicle's for-hire license number.

visit this link on Kaggle: https://www.kaggle.com/datasets/fivethirtyeight/uber-pickups-in-new-york-city?select=other-Federal_02216.csv

## Data Overview
* other-Federal_02216.csv: 276 records in total 
* Range of dates: 2014-06-30 to 2014-09-27

## File Structure
* pu-data/: contains the raw data
* pu-routes/: contains the processed route data
* log/: contains the log file
* EDA.ipynb: exploratory data analysis
* getRoutes.py: get routes from Google Maps API. 
Run `python getRoutes.py` to get the routes.
Change TODOs in the code for customizing the output.

## Setup
* .env: contains the environment variables, see example.env. Put your own API key in there.
* requirements.txt: contains the dependencies
Run `pip install -r requirements.txt` to install the dependencies
