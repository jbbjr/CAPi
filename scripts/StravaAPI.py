import requests
import pandas as pd
import urllib3
import ssl

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Client:
    def __init__(self, client_id, client_secret, refresh_token, weather_key):
        self.base_url = 'https://www.strava.com/api/v3/'
        self.auth_url = 'https://www.strava.com/oauth/token'
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.weather_key = weather_key
        self.access_token = self.get_access_token()

    def get_access_token(self):
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': "refresh_token",
            'scope': 'activity:read_all',
            'f': 'json'
        }

        print("Requesting Token...\n")
        res = requests.post(self.auth_url, data=payload, verify=False)
        access_token = res.json()['access_token']
        print(res.json())

        print("Access Token = {}\n".format(access_token))
        return access_token

    # collects activity ids from summary activity objects
    # returns a dict of ids back
    def get_activity_ids(self):
        ids = {'id': []}

        url = f'{self.base_url}athlete/activities'
        header = {'Authorization': 'Bearer ' + self.access_token}

        page = 1

        while True:
            param = {'per_page': 200, 'page': page}
            results = requests.get(url, headers=header, params=param).json()

            # completion case (no activities left)
            if len(results) == 0:
                break

            # get the ids within results and append to the dict
            for i in range(0, len(results)):
                ids['id'].append(results[i]['id'])

            page += 1

        return ids

    # returns the most recent activity
    # returns the id of it to process it in get detailed activity
    def get_recent_activity(self):
        url = f'{self.base_url}athlete/activities'
        header = {'Authorization': 'Bearer ' + self.access_token}

        param = {'per_page': 1, 'page': 1}
        result = requests.get(url, headers=header, params=param).json()
        return result[0]['id']

    # edits the current description to include the CAPi predictions
    def update_description(self, activity_id=int, desc=str, pace=str):
        url = f'{self.base_url}/activities/{activity_id}'
        header = {'Authorization': 'Bearer ' + self.access_token}
        param = {'id': activity_id, '<Parameter Name>': 'description'}

        if desc:
            payload = {'description': f'Climate Adjusted Pace (CAPi): ~{pace} \n\n{desc}'}
        else:
            payload = {'description': f'Climate Adjusted Pace (CAPi): ~{pace}'}

        requests.put(url, headers=header, params=param, data=payload)


    # requests detailed activity information from the strava API
    # takes an activity_id (from a respective workout)
    def get_detailed_activity(self, activity_id=int):
        url = f'{self.base_url}activities/{activity_id}'
        header = {'Authorization': 'Bearer ' + self.access_token}
        param = {'id': activity_id, 'include_all_efforts': True}
        return requests.get(url, headers=header, params=param).json()

    # builds off of get_detailed_activity to get what we need in the appropriate format
    # takes a json get and turns it into a pandas df
    # returns the pandas df
    def build_activity_laps_df(self, activity_id=int):
        data = self.get_detailed_activity(activity_id=activity_id)

        if data['type'] != 'Run':
            return

        # make necessary pandas json manipulations to get data nice and tidy
        try:
            df = pd.json_normalize(data)
            relevant_data = pd.json_normalize(df['laps'].explode())
        except:
            print('no laps data')
            return

        # adding back relevant data that wasn't inside the lap element
        relevant_data['activity_id'] = data['id']
        relevant_data['type'] = data['type']
        relevant_data['sport_type'] = data['sport_type']
        relevant_data['timezone'] = data['timezone']

        # some activities might not have a location
        try:
            relevant_data['start_lat'] = data['start_latlng'][0]
            relevant_data['start_long'] = data['start_latlng'][1]
        except:
            relevant_data['start_lat'] = 'NaN'
            relevant_data['start_long'] = 'NaN'

        return relevant_data

    # Integrates the add_weather.py script into the class for a cleaner main
    def add_weather(self, activity_id=int):
        base = 'https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline'
        params = f'?key={self.weather_key}&contentType=csv&unitGroup=us&include=current'
        activity = self.build_activity_laps_df(activity_id)

        activity_weather = pd.DataFrame()
        # get live weather data per lap in each activity, add back some unique identifier data so we can join later.
        for index, lap in activity.iterrows():
            query = f'{base}/{lap["start_lat"]},{lap["start_long"]}/{lap["start_date_local"].replace("Z", "")}' + params
            # print(query)
            temp = pd.read_csv(query)
            temp['activity_id'] = lap['activity_id']
            temp['name'] = lap['name']
            activity_weather = pd.concat([activity_weather, temp])

        return activity_weather

    # For debugging purposes
    # Prints out the variables as you walk through the method
    def test_get_recent_activity(self):
        url = f'{self.base_url}athlete/activities'
        header = {'Authorization': 'Bearer ' + self.access_token}
        param = {'per_page': 1, 'page': 1}
        result = requests.get(url, headers=header, params=param).json()

        print(url)
        print(header)
        print(param)
        print(result)

    # For debugging purposes
    # Prints out the variables as you walk through the method
    def test_get_detailed_activity(self, activity_id=int):
        url = f'{self.base_url}activities/{activity_id}'
        print(f'url: {url}')

        # get access token within method so we can refresh if needed
        header = {'Authorization': 'Bearer ' + self.access_token}
        print(header)

        param = {'id': activity_id, 'include_all_efforts': True}
        print(param)

    # For debugging purposes
    # Prints out the properties of the Class Object
    def check_properties(self):
        print(self)  # should return the object in memory
        print(self.client_id)  # should return the client_id from .env
        print(self.client_secret)  # should return the client_secret from .env
        print(self.refresh_token)  # should return the refresh_token from .env
        print(self.base_url)  # should return "https://www.strava.com/api/v3/"
        print(self.auth_url)  # should return "https://www.strava.com/oauth/token
        print(self.access_token)  # should return an access_token based on the .env vars
