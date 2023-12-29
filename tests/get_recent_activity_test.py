import StravaAPI
from dotenv import load_dotenv
import os

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

client = StravaAPI.Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

"""
should return:
url as https://www.strava.com/api/v3/athlete/activities
headers as {'Authorization': 'Bearer ACCESS TOKEN from constructor' }
params as {'per_page': 1, 'page': 1}
result containing info of most recent activity, 
which at the time of the test is a null location treadmill run from 12-27-23
"""
client.test_get_recent_activity()

recent = client.get_recent_activity()     # testing on personal strava account, should return id of most recent activity
print(recent)
