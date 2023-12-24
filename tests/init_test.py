import os
import StravaAPI
from dotenv import load_dotenv
import requests

load_dotenv()

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

client = StravaAPI.Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

client.check_properties()
