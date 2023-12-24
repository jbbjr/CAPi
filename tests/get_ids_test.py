import StravaAPI
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

client = StravaAPI.Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

ids = client.get_activity_ids()     # testing on personal strava account, should return around 400ish length dict of ids
print(ids)
print(f'number of activities {len(ids["id"])}')