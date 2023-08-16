# Import the dependencies.
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurements = Base.classes.measurement
Stations = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)


#################################################
# Flask Setup
#################################################

app = Flask(__name__)


#################################################
# Flask Routes
#################################################


# 0. Define a function to extract only the last 12 months of the data:
def year_before():

    # Create the session
    session = Session(engine)

    # Define the most recent date and use it to calculate the date from the previous year
    most_recent_date = session.query(Measurements.date).order_by(Measurements.date.desc()).first()
    last_year = (dt.datetime.strptime(most_recent_date[0],'%Y-%m-%d') - dt.timedelta(days=365)).strftime('%Y-%m-%d')

    # Close the session                   
    session.close()

    # Return the date
    return(last_year)


# 1. Start at the homepage and list all the available routes:
@app.route("/")
def welcome():
    """List all available api routes."""
    return(
        f"<b>Welcome to this challenge's homepage!</b><br/>"
        f"Available routes listed below:<br/>"
        f"Precipitation measurement over the last 12 months: /api/v1.0/precipitation<br/>"
        f"The following list contains all active stations and their numbers: /api/v1.0/stations<br/>"
        f"Temperature of the most active stations in the past 12 months: /api/v1.0/tobs<br/>"
        f"Enter a start date to retreive the minimum, maximum, and average temperatures after specified dates: /api/v1.0/<start><br/>"
        f"Enter both a start and end date to retreive the minimum, maximum and average temperatures between dates: /api/v1.0/<start>/<end>"
    )


# 2. Make a route that displays the precipitation measurements over the past 12 months in the data.
@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create the session
    session = Session(engine)

    # Query precipitation data from last 12 months from the most recent date in Measurement table
    prcp_data = session.query(Measurements.date, Measurements.prcp).\
        filter(Measurements.date >= year_before()).all()
    
    # Close the session                   
    session.close()

    # Create a dictionary from the row data and append to a list of prcp_list
    prcp_list = []
    for date, prcp in prcp_data:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["prcp"] = prcp
        prcp_list.append(prcp_dict)

    # Return a list of jsonified precipitation data for the previous 12 months 
    return jsonify(prcp_list)



# 3. Create a route that enlists all stations in the dataset:
@app.route("/api/v1.0/stations")
def stations():
    # Create the session
    session = Session(engine)

    all_stations = session.query(Stations.station, Stations.name).all()

    # Close the session                   
    session.close()

    #
    station_list = list(np.ravel(all_stations))

    # Return a list of jsonified list for all stations 
    return jsonify(station_list)


# 4. Create a route to retreive the temperature for the most active stations in the past 12 months:
@app.route("/api/v1.0/tobs")
def tobs():
    # Create the session
    session = Session(engine)

    # Get the date and temperature for station 'USC00519281' in the last year
    tobs_data = session.query(Measurements.date, Measurements.tobs).\
            filter(Measurements.date >= year_before()).\
            filter(Measurements.station == "USC00519281").\
            order_by(Measurements.date).all()
    
    # Turn the results into a dictionary
    tobs_dict = dict(tobs_data)

    # Return the dictionary as a json list
    return jsonify(tobs_dict)


# 5. Retrieve the min, max, and average temperatures for a start date and a 'in between dates.'
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def start_end_date(start, end=None):

    # See if there is an end date present, if not continue with the task:
    if end == None: 
        # Query from start date to most recent date:
        start_temp = session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.round(func.avg(Measurements.tobs), 2)).\
                            filter(Measurements.date >= start).all()
        # Convert list of tuples into normal list:
        start_list = list(np.ravel(start_temp))
        start_list2 = {"Temp min:": start_list[0],"Temp max:": start_list[1], "Temp avg:": start_list[2]}

        # Return the previous code into a jsonified version of a list:
        return jsonify(start_list2)
    else:
        # Query from start date to the end date:
        start_end_temp = session.query(func.min(Measurements.tobs), func.max(Measurements.tobs), func.round(func.avg(Measurements.tobs), 2)).\
                            filter(Measurements.date >= start).\
                            filter(Measurements.date <= end).all()
        # Convert list of tuples into normal list:
        start_end_list = list(np.ravel(start_end_temp))
        start_end_list2 = {"Temp min:": start_end_list[0],"Temp max:": start_end_list[1], "Temp avg:": start_end_list[2]}

        # Return the previous code into a jsonified version of a list:
        return jsonify(start_end_list)

    # Close the session                   
    session.close()


# 6. Define the main branch
if __name__ == '__main__':
    app.run(debug=True)
