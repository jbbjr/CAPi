import StravaAPI
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

client = StravaAPI.Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

# should return 5 laps (representing 5 miles ran in this specific workout)
print(client.build_activity_laps_df(activity_id=9490587429))

# might return error
print(client.build_activity_laps_df(activity_id=10402547018))

