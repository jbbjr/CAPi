import pytest
import requests_mock
import os
from scripts.StravaAPI import Client
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# Create a fixture for the Client instance
@pytest.fixture
def client(requests_mock):
    token_url = 'https://www.strava.com/oauth/token'
    token_response = {
        'access_token': 'mock_access_token',
        'token_type': 'Bearer',
        'expires_at': 1568775134,
        'expires_in': 21600,
        'refresh_token': 'mock_refresh_token'
    }
    requests_mock.post(token_url, json=token_response)

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    refresh_token = os.getenv('REFRESH_TOKEN')
    weather_key = os.getenv('WEATHER_KEY')
    return Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, weather_key=weather_key)


# Test for get_access_token method
def test_get_access_token(client):
    access_token = client.get_access_token()
    assert access_token == 'mock_access_token'


# Test for get_detailed_activity method
def test_get_detailed_activity(requests_mock, client):
    activity_id = 9490587429
    detailed_activity_url = f'https://www.strava.com/api/v3/activities/{activity_id}'
    detailed_activity_response = {
        'id': activity_id,
        'name': 'Mock Activity',
        'distance': 1000.0,
        'moving_time': 300,
        'elapsed_time': 360,
        'total_elevation_gain': 50.0,
        'type': 'Run'
    }
    requests_mock.get(detailed_activity_url, json=detailed_activity_response)

    detailed_activity = client.get_detailed_activity(activity_id)
    assert detailed_activity['id'] == activity_id
    assert detailed_activity['name'] == 'Mock Activity'


# Test for get_recent_activity method
def test_get_recent_activity(requests_mock, client):
    recent_activity_url = f'https://www.strava.com/api/v3/athlete/activities'
    recent_activity_response = [
        {
            'id': 9490587429,
            'name': 'Mock Activity',
            'distance': 1000.0,
            'moving_time': 300,
            'elapsed_time': 360,
            'total_elevation_gain': 50.0,
            'type': 'Run'
        }
    ]
    requests_mock.get(recent_activity_url, json=recent_activity_response)

    recent_activity_id = client.get_recent_activity()
    assert recent_activity_id == 9490587429

# Test for update_description method
def test_update_description(requests_mock, client):
    activity_id = 9490587429
    update_url = f'https://www.strava.com/api/v3/activities/{activity_id}'
    update_response = {
        'id': activity_id,
        'description': 'Climate Adjusted Pace (CAPi): ~5:00 \n\nUpdated description'
    }
    requests_mock.put(update_url, json=update_response)

    client.update_description(activity_id, 'Updated description', '5:00')

    detailed_activity_url = f'https://www.strava.com/api/v3/activities/{activity_id}'
    requests_mock.get(detailed_activity_url, json=update_response)  # Mock the get request for updated description

    updated_activity = client.get_detailed_activity(activity_id)
    assert 'Climate Adjusted Pace (CAPi): ~5:00' in updated_activity['description']
    assert 'Updated description' in updated_activity['description']


# Test for check_properties method
def test_check_properties(client):
    assert client.client_id == os.getenv('CLIENT_ID')
    assert client.client_secret == os.getenv('CLIENT_SECRET')
    assert client.refresh_token == os.getenv('REFRESH_TOKEN')
    assert client.base_url == 'https://www.strava.com/api/v3/'
    assert client.auth_url == 'https://www.strava.com/oauth/token'
    assert client.access_token is not None