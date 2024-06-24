import pandas as pd
import os
from dotenv import load_dotenv
import ssl

# idk why this makes it work in the regular python interpreter, but it does... epic
ssl._create_default_https_context = ssl._create_unverified_context

# load enviornment and instantiate query request / variables
load_dotenv()

key = os.getenv('WEATHER_KEY')

laps = pd.read_csv('/Users/bennett/PycharmProjects/CAPi/laps_data.csv')
ids = laps['activity.id'].to_dict()

base = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline'
params= f'?key={key}&contentType=csv&unitGroup=us&include=current'

df = pd.DataFrame()

# get live weather data per lap in each activity, add back some unique identifier data so we can join later.
for index, activity in laps.iterrows():
    query = f'{base}/{activity["start_lat"]},{activity["start_long"]}/{activity["start_date_local"].replace("Z", "")}' + params
    print(query)
    temp = pd.read_csv(query)
    temp['activity_id'] = activity['activity_id']
    temp['name'] = activity['name']
    df = pd.concat([df, temp])

df.to_csv('/Users/bennett/PycharmProjects/CAPi/weather_data.csv')