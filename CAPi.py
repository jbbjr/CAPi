import datetime

import numpy as np
import pandas as pd
from StravaAPI import Client
import pickle
from dotenv import load_dotenv
import os
from google.cloud import bigquery

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')
key = os.getenv('WEATHER_KEY')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'/Users/bennett/PycharmProjects/CAPi/gcp-key.json'


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


# overall pace
def overall_pace(df, col):
    # Conversion factors
    meters_to_miles = 0.000621371
    seconds_to_minutes = 1 / 60.0

    # Conversions
    distance_miles = df['distance'].sum() * meters_to_miles
    elapsed_time_minutes = df[col].sum() * seconds_to_minutes

    # minutes per mile
    pace_minutes_per_mile = elapsed_time_minutes / distance_miles

    # Format the result in M:SSmi
    pace_formatted = f"{int(pace_minutes_per_mile // 1):02}:{int((pace_minutes_per_mile % 1) * 60):02}mi"

    return pace_formatted


# load in general variables needed for script
client = Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, weather_key=key)
CAPi = load_model()

id = client.get_recent_activity()

activity = client.build_activity_laps_df(activity_id=id)
desc = client.get_detailed_activity(activity_id=id)['description']

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

# Feature Engineer
activity = activity.sort_values(by=['activity_id', 'name'])

activity['distance_covered_prior'] = activity.groupby('activity_id')['distance'].cumsum() - activity['distance']
activity['time_elapsed_prior'] = activity.groupby('activity_id')['moving_time'].cumsum() - activity['moving_time']

# set up predictions
y = activity[['moving_time']]
X = activity[['distance', 'average_speed', 'average_heartrate', 'average_cadence', 'max_speed', 'max_heartrate',
              'total_elevation_gain', 'pace_zone', 'temp', 'dew', 'humidity', 'windspeed', 'winddir',
              'sealevelpressure', 'cloudcover', 'distance_covered_prior', 'time_elapsed_prior', 'conditions']]

X_test = activity.drop(columns=['moving_time'])
predictions = CAPi.predict(X_test)

# Optimal conditions
X.loc[:, 'temp'] = 50
X_test = X
temp_predictions = CAPi.predict(X_test)

# Adding paces
activity['predictions'] = predictions
activity['optimal'] = temp_predictions
activity['CAPi_elapsed_time'] = activity['moving_time'] - (activity['predictions'] - activity['optimal'])

# Adding the columns
activity['pace_formatted'] = activity.apply(pace_conversion, col='moving_time', axis=1)
activity['predicted_pace_formatted'] = activity.apply(pace_conversion, col='predictions', axis=1)
activity['optimal_predicted_pace'] = activity.apply(pace_conversion, col='optimal', axis=1)
activity['CAPi'] = activity.apply(pace_conversion, col='CAPi_elapsed_time', axis=1)

# Update the activity with the overall adjusted pace on the users Strava
# client.update_description(activity_id=id, desc=desc, pace=overall_pace(activity, 'CAPi_elapsed_time'))

print('CAPi Laps')
print(activity['CAPi'])
print()
print('Normal Laps')
print(activity['pace_formatted'])

# Transformations for BQ
activity = activity.replace(np.NAN, None)
activity['athlete_id'] = activity['athlete.id']
new_data = activity.to_dict(orient='records')

# send results to bigquery database
bq_client = bigquery.Client(project='capi-410116')
ref = 'capi-410116.activities.activities-with-weather'

# established schema
schema = [
    bigquery.SchemaField('id', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('moving_time', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('start_date_local', 'TIMESTAMP', mode='NULLABLE'),
    bigquery.SchemaField('distance', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('average_speed', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('max_speed', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('lap_index', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('total_elevation_gain', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('average_cadence', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('average_watts', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('average_heartrate', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('max_heartrate', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('pace_zone', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('activity_id', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('athlete_id', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('type', 'STRING', mode='NULLABLE'),
    bigquery.SchemaField('start_lat', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('start_long', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('temp', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('dew', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('humidity', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('distance_covered_prior', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('winddir', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('conditions', 'STRING', mode='NULLABLE'),
    bigquery.SchemaField('windspeed', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('cloudcover', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('time_elapsed_prior', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('time_elapsed_prior', 'INTEGER', mode='NULLABLE'),
    bigquery.SchemaField('predictions', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('optimal', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('CAPi_elapsed_time', 'FLOAT', mode='NULLABLE'),
    bigquery.SchemaField('pace_formatted', 'STRING', mode='NULLABLE'),
    bigquery.SchemaField('predicted_pace_formatted', 'STRING', mode='NULLABLE'),
    bigquery.SchemaField('optimal_predicted_pace', 'STRING', mode='NULLABLE'),
    bigquery.SchemaField('CAPi', 'STRING', mode='NULLABLE'),
]

# copy the df for schema type mapping
activity_mapped = activity.copy()
activity_mapped = activity_mapped[['id', 'moving_time', 'start_date_local', 'distance', 'average_speed', 'max_speed', 'lap_index',
                             'total_elevation_gain', 'average_cadence', 'average_watts', 'average_heartrate', 'max_heartrate',
                             'pace_zone', 'activity_id', 'athlete_id', 'type', 'start_lat', 'start_long', 'temp', 'dew',
                             'humidity', 'precip', 'windspeed', 'winddir', 'sealevelpressure', 'cloudcover', 'conditions',
                             'distance_covered_prior', 'time_elapsed_prior', 'predictions', 'optimal', 'CAPi_elapsed_time',
                             'pace_formatted', 'predicted_pace_formatted', 'optimal_predicted_pace', 'CAPi']]


dtype_map = {'INTEGER': int, 'STRING': str, 'FLOAT': float, 'TIMESTAMP': 'datetime64[ns]'}

for field in schema:
    column_name = field.name
    data_type = dtype_map.get(field.field_type)

    # Handle nullable columns
    if field.mode == 'NULLABLE':
        activity_mapped[column_name] = activity_mapped[column_name].astype(data_type, errors='ignore')
    else:
        activity_mapped[column_name] = activity_mapped[column_name].astype(data_type)

# TIMESTAMP finicky sometimes
activity_mapped['start_date_local'] = pd.to_datetime(activity_mapped['start_date_local'], errors='coerce')
activity_mapped.info()

# Do the BQ stuff
job_config = bigquery.LoadJobConfig(autodetect=False, write_disposition='WRITE_APPEND', schema=schema)
job = bq_client.load_table_from_dataframe(activity_mapped, ref, job_config=job_config)
job.result()

if job.errors:
    print(f"Errors during batch insert: {job.errors}")
else:
    print("Batch insert successful")