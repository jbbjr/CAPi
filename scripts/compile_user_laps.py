from scripts.StravaAPI import Client
import os
from dotenv import load_dotenv
import pandas as pd
import time

load_dotenv()

# instantiate environment variables
client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
refresh_token = os.getenv('REFRESH_TOKEN')

# setup the client
client = Client(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token)

# get our activity ids
ids = client.get_activity_ids()
print('ids collected')

# Strava API rate limits
CALLS_PER_15_MIN = 200 - 1  # account for get (ids)
CALLS_PER_DAY = 2000
SECONDS_PER_15_MIN = 15 * 60

# Initialize variables
remaining_calls_15min = CALLS_PER_15_MIN
remaining_calls_day = CALLS_PER_DAY
start_time = time.time()

# Instantiate the dataframe
df = pd.DataFrame()
print('Variables instantiated')

# Check our current progress, or instantiate it
try:
    with open('last_processed.txt', 'r') as file:
        last_processed = int(file.read())
        print(f'According to last_processed, {last_processed} is where we left off... Starting there')
except FileNotFoundError:
    print('Creating last_processed file starting at 0')
    last_processed = 0

print('Begin data collection')

# Loop through other activities
for activity_index, activity in enumerate(ids['id'][last_processed:], start=last_processed):

    # Check rate limits
    current_time = time.time()
    elapsed_time = current_time - start_time

    # construct the df for concat to work on the first run through
    if len(df) == 0:
        print(f'activity: {activity}')
        base = client.build_activity_laps_df(activity_id=activity)
        df = pd.DataFrame(base, columns=base.columns)

    # Only 200 calls per 15 minutes, wait in here if needed
    if elapsed_time < SECONDS_PER_15_MIN and remaining_calls_15min <= 0:
        print('15 minute rate limit met. Wait here')
        time.sleep(SECONDS_PER_15_MIN - elapsed_time)
        start_time = time.time()
        remaining_calls_15min = CALLS_PER_15_MIN

    # Daily limit is met
    if remaining_calls_day <= 0:
        print(f'Daily limit was met at {activity_index}')
        print(f'Saving position to last_processed.txt')
        with open('last_processed.txt', 'w') as file:
            file.write(str(activity_index))
        break

    # Make the API call
    print(f'activity: {activity}')
    temp = client.build_activity_laps_df(activity_id=activity)

    # Update remaining calls and time
    remaining_calls_15min -= 1
    remaining_calls_day -= 1

    # Concatenate dataframes
    df = pd.concat([df, temp])

# Save the final dataframe to CSV
df.to_csv('/Users/bennett/PycharmProjects/CAPi/laps_data.csv')
