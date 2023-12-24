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
url as https://www.strava.com/api/v3/activities/ACTIVITY_ID
headers as {'Authorization': 'Bearer ACCESS TOKEN from constructor' }
params as {'id': ACTIVITY ID from arguments, 'include_all_efforts': True}
"""
client.test_get_detailed_activity(activity_id=9490587429)

# Should return a detailed activity JSON of the respective activity_id
activity = client.get_detailed_activity(activity_id=9490587429)
print(activity)

