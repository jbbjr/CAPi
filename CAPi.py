from StravaAPI import Client
import pandas as pd
import pickle
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')
key = os.getenv('WEATHER_KEY')


def load_model():
    with open('CAPi.pkl', 'rb') as file:
        return pickle.load(file)


# Used chatGPT for this. I didn't want to have to think about this that long
def pace_conversion(row, col):
    # Conversion factors
    meters_to_miles = 0.000621371
    seconds_to_minutes = 1 / 60.0

    # Conversions
    distance_miles = row['distance'] * meters_to_miles
    elapsed_time_minutes = row[col] * seconds_to_minutes

    # minutes per mile
    pace_minutes_per_mile = elapsed_time_minutes / distance_miles

    # Format the result in M:SSmi
    pace_formatted = f"{int(pace_minutes_per_mile // 1):02}:{int((pace_minutes_per_mile % 1) * 60):02}mi"

    return pace_formatted


client = Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, weather_key=key)
CAPi = load_model()

id = client.get_recent_activity()

activity = client.build_activity_laps_df(activity_id=id)

# edge case for if the activity is not outside or is not a run
for index, row in activity.iterrows():
    if row['start_lat'] == 'NaN':
        print('Activity was not recorded outside or has insufficient location data. exitting CAPi')
        exit()
    elif row['type'] != 'Run':
        print('Activity is not a run. exitting CAPi')
        exit()

# make weather request and merge with activity
weather = client.add_weather(activity_id=id)
activity = activity.merge(weather, how='left', on=['name', 'activity_id']).drop_duplicates()
print(activity)

# set up predictions
y = activity[['moving_time']]
X = activity[['distance', 'average_speed', 'average_heartrate', 'average_cadence', 'max_speed', 'max_heartrate',
              'total_elevation_gain', 'pace_zone', 'temp', 'dew', 'humidity', 'windspeed', 'winddir',
              'sealevelpressure', 'cloudcover', 'distance_covered_prior', 'time_elapsed_prior', 'conditions']]

X_test = activity.drop(columns=['moving_time'])
predictions = CAPi.predict(X_test)

# Optimal conditions
X['temp'] = 50
X_test = activity.drop(columns=['moving_time'])
temp_predictions = CAPi.predict(X_test)

# Adding paces
activity['predictions'] = predictions
activity['optimal'] = temp_predictions
activity['CAPi_moving_time'] = activity['moving_time'] - (activity['predictions'] - activity['optimal'])

# Adding the columns
activity['predicted_pace_formatted'] = activity.apply(pace_conversion, col='predictions', axis=1)
activity['optimal_predicted_pace'] = activity.apply(pace_conversion, col='optimal', axis=1)
activity['CAPi'] = activity.apply(pace_conversion, col='CAPi_moving_time', axis=1)

print('CAPi Laps')
print(activity['CAPi'])
