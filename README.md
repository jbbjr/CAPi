![image](https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/cropped_version.png)
**Climate Adjusted Pace individualized (CAPi) is a predictive model trained on a users Strava data. It leverages optimal weather conditions from personal research to return a Climate Adjusted Pace (CAP) for an athlete. Similar to Gradient Adjusted Pace (GAP), this will help athletes train more efficiently in suboptimal weather conditions.**

## Purpose

#### Background
I began my endurance running journey with the 2021 NYC Marathon and have gotten more involved in the sport and community since. Most of my training has traditionally been in intense heat and humidity, as I did undergrad in the mid-south at Rhodes College. So, as I begun to take things more seriously and look toward running a Boston Qualifying time (BQ), I became much more aware of tracking things like my heartrate, cadence, regular and gradient adjusted pace, etc. This led me to my personal research to discover: [How does weather impact runners?](https://github.com/jbblancojr/Marathon-Weather-Analysis-and-Performance-Prediction). After spending a majority of my senior year on this research, I knew I wanted to leverage Machine Learning and Data Science to derive some value from my findings. This is when I decided to build **CAPi**.

#### Value
In a nutshell, **CAPi** is a tool for runners to help them train better in poor climate. The model provides a Climate Adjusted Pace (CAP) that you can utilize to better understand whether or not you over/under exherted on your run, or what your true time in a race could have been if the conditions weren't so harsh.

While this information is generally more beneficial to serious runners rather casual ones (esepcailly those familiar with heartrate zones and zone training), it will help democratize a generally understood concept in the advanced running community that your heartrate is effected by the climate, which will in turn effect your performance.

#### Summary
CAPi will first train on a users existing [Strava](https://www.strava.com) data, so that it can predict your moving time for a given lap in your Strava activity, given the current weather conditions. From there, CAPi will impute optimal weather conditions and repredict that lap, take the difference of its two predictions and subtract that margin from the real, providing an approximated CAP. 

## Building a Client & Collecting Data
Gathering the necessary data to train the model is a little tedious. I'll go into more detail below, but here's the general process.

**Overiew**
- Get Strava API access
- Change API scope in Postman
- Collect a users (me) Strava data
- Collect relevant weather data 

### Setting up Strava API Access
Getting the right scope for the API is a little tricky. When you set up your [Strava API Application](https://www.strava.com/settings/api), the default scope is set to `activity:read`. In order to access important data such as pace zones and heartrate you'll need the scope `activity:read_all`, and to alter activities you'll need the scope `activity:write`. 

**To change your scope:**

You will need to gather your client id, client secret, and preferred scope, and finally paste this link into a browser. It will return a code=CODE portion. You just need to copy that code

`https://www.strava.com/oauth/authorize?client_id=your_client_id&redirect_uri=http://localhost&response_type=code&scope=activity:read_all,activity:write`

<p align="center">
  <img src="https://github.com/jbblancojr/CAPi/blob/main/images/scope.png" width="500" />
</p>

Next with the code you collected, you'll send a POST request with this link, which will return you a new set of client id, client secret, and refresh token.

`https://www.strava.com/oauth/token?client_id=your_client_id&client_secret=your_client_secret&code=your_code_from_previous_step&grant_type=authorization_code`

After this, just gather the variables and put them into your environment.

### Collecting the Data
When you post a run (or any other workout) to Strava, that is recorded as an activity. Each activity is given a unique `activity id` and is attatched to a unique `athlete id`. When working with the Strava API, you can request two types of the same activity: `SummaryActivity` and `DetailedActivity`. 

| <img src="https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/summarysmall.png" alt="Image 1" style="max-width: 100%;"> | <img src="https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/detailedsmall.png" alt="Image 2" style="max-width: 100%;"> |
| :---: | :---: |

Inside of the Detailed Activity object, there is a neat element called `Laps`. This contains more granular data for your run. Instead of getting overall distance or time, you can get it per lap by accessing that element. For this reason, we want to get a DetailedActivity for each of our recorded activities, so that we can train our data on samples of laps, which will result in higher accuracy and more data to train on. Furthermore, the aggregate stats for a workout might be skew

**Here's an example**  

This is one of my threshold workouts from the fall. You can see that even though the run is 8.5 miles, there are more than 8.5 laps. The darker bars represent my threshold sets (which were in minutes, not miles), and the tiny gaps in between are actually recoveries within sets. There's a large variance in paces too. This is why it's important to sample by lap.

![image](https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/laps_example.png)

There is a catch to collecting this data though. You can only access one DetailedAcitivity per API call by sending a GET for the corresponding activity id, where as you can collect multiple SummaryActivity objects in one call. This means that we need to first collect all the activity ids, and then request a DetailedActivity one by one, so we can access the Laps object for each of them. This is done inside of `compile_user_laps.py`, which takes care of transforming the data into a usable format and considering rate limiting.

Once the data is compiled, we use `add_weather.py` to get the necesarry weather data for each lap. What's really cool is that there is a start datetime for each lap, so the weather data can get super granular as well. Inside `add_weather.py` we factor that into a query request to the **VisualCrossing API** (I used this in my research, its super easy to work with, has good data, and I was already familiar with it). Once all that is complete we can move on to the EDA and modeling.

Another thing to mention is that both of these scripts rely on a lot of repetead tasks and API calls. For this reason I built a Client class to compensate.

### Building the Client
Since a few specfic requests need to be made pretty frequently, it makes the most sense to throw everything into a class. I set up `StravaAPI.py` to encapsulate those repeated tasks, which results in cleaner code for the EDA and main script. Tests for methods are located in the tests folder.

**The Client class can:**
- Automatically get access tokens (Strava's API requires you to use refresh token to generate new access tokens)
- Get all activity ids from a user (useful for requesting detailed activities)
- Get the most recent activity id (useful for main later)
- Update the description of an activity (also useful for main later)
- Get a detailed activity
- Build activity laps (transforms a lap object from a detailed activity into tabular form)
- Get weather for the activity data

## Model Selection & Results

### Predicting Moving Time
Before we can build CAPi, we need to train a model that can predict how long a lap is going to take given a specific set of features. From the lap and weather data we compiled and after data cleaning, we have about 4100 observations. `eda-and-model-selection.ipynb` goes into more detail on the specific steps. It also includes the preprocessing pipeline and model seleciton, tuning, and evaluation. 

### Dataset

<br/>

**Target Vector**
| Variable     | Description                              |
| ------------ | ---------------------------------------- |
| moving_time  | The lap's moving time, in seconds (int)  |

**Feature Matrix**
| Variable                | Description                                                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| distance                | The lap's distance, in meters (float                                                                                   |
| average_speed           | The lap's average speed (float)                                                                                        |
| average_heartrate       | The lap's average heartrate (float)                                                                                    |
| average_cadence         | The lap's average cadence (float)                                                                                      |
| max_speed               | The maximum speed of this lap, in meters per second (float)                                                            |
| max_heartrate           | The maximum heartrate of this lap (float)                                                                              |
| total_elevation_gain    | The elevation gain of this lap, in meters (float)                                                                      |
| pace_zone               | The athlete's pace zone during this lap (int)                                                                          |
| temp                    | Temperature at the location in Fahrenheit (float)                                                                      |
| dew                     | Dew point temperature (float)                                                                                          |
| humidity                | Relative humidity in % (float)                                                                                         |
| windspeed               | The sustained wind speed measured as the average windspeed that occurs during the preceding one to two minutes (float) |
| winddir                 | Direction from which the wind is blowing (float)                                                                       |
| sealevelpressure        | The atmospheric pressure at a location that removes reduction in pressure due to the altitude of the location (float)  |
| cloudcover              | How much of the sky is covered in cloud ranging from 0-100% (float)                                                    |
| distance_covered_prior  | The cumulative sum of distance covered prior to the current lap (float)                                                |
| time_elapsed_prior      | The cumulative sum of moving time elapsed prior to the current lap (float)                                             |
| conditions              | Textual representation of the weather conditions (string)                                                              |

<br/>

### Pipeline
```python
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer

nums = ['distance', 'average_speed', 'average_heartrate', 'average_cadence', 'max_speed', 
        'max_heartrate', 'total_elevation_gain', 'temp', 'dew', 'humidity', 'windspeed', 
        'winddir', 'sealevelpressure', 'cloudcover', 'distance_covered_prior', 'time_elapsed_prior']

cats =  ['pace_zone']
dummies = ['conditions']

num_pipe = Pipeline(steps=[
    ('impute', SimpleImputer(strategy='mean')),        # just for reproducibility purposes
    ('scale', StandardScaler())
])

# pace zone is actually ordinal with some sort of scale (we need to account for that)
cat_pipe = Pipeline(steps=[
    ('impute', SimpleImputer(strategy='most_frequent')),
    ('categorize', OrdinalEncoder()),
])

# we can't say much about how conditions are sequentially better than others in an ordinal sense.
dummy_pipe = Pipeline(steps=[
    ('impute', SimpleImputer(strategy='most_frequent')),       # just for reproducibility purposes
    ('categorize', OneHotEncoder(handle_unknown='ignore')),
])  
```
```python
from sklearn.compose import ColumnTransformer

preprocessing = ColumnTransformer(transformers=[
    ('numeric columns', num_pipe, nums),
    ('categorical columns', cat_pipe, cats),
    ('dummy columns', dummy_pipe, dummies)],
    remainder='passthrough'
)
```
```python
from xgboost import XGBRegressor
from sklearn.ensemble import RandomForestRegressor

rf_pipeline = Pipeline(steps=[
    ('preprocess', preprocessing),
    ('rf', RandomForestRegressor(random_state=42))
])

xgbr_pipeline = Pipeline(steps=[
    ('preprocess', preprocessing),
    ('xgboost', XGBRegressor(objective='reg:squarederror', alpha=1, random_state=42))
])
```

<br/>

### First Tune and Evaluations
For context, I tried about every single model in Scikit learn and found Random Forest and XGBoost to be the top two performance by quite a fair amount. For this reason, I'll only discussing the results from those two models. For the sake of compute I am using RandomizedSearch. Also, it actually seems to be performing pretty well. The metrics of interest are RMSE and MAPE. RMSE is really helpful because it will tell us how many seconds the model is off by on average. MAPE is nice as a double check, since its a percentage from the mean and not in units.

<br/>

After Running RandomizedSearch the first time, both the Random Forest and XGBoost models had almost a perfect $R^2$ of 99%. Given the limited size of the data, I was pretty certain this was just overfitting, but the results argue otherwise.

<br/>

**Random Forest Results:&nbsp;&nbsp; RMSE = 7.97&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MAPE = 5.6%**

**XGBoost Results:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RMSE = 3.86&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MAPE = 2.7%**

<br/>

Though these results were pretty good, I wanted to think of more ways I could reduce the error, since predictions need to be near perfect to derive any value (because temperature is only a small factor of what affects your run). 

### Re-evaluation with newly adjusted dataset
After I had exhausted different kinds of models and tried to tune different parameters, I needed to think of ways to reduce the error by manipulating the dataset. There had to be some noise I could eliminate. That's when I realized that often times a lap might be a recovery between sets. 

Recovery laps are a huge cause for noise in the dataset for a few reasons. A big one is that your heartrate will still be up from your speed set (so the model will get confused why there is a large increase in moving time but the heartrate is staying the same). The same thing is true for the pace zone and heartrate. Pace zone can compensate for the speed drop, but heartrate will be way higher than expected for that zone as well, further confusing the model.

Another way to limit noise is cutting off laps where time is extremely miniscule. Often times you don't run a perfect 6 miles for the day and it might end up being 6.01. That .01 actually is recorded as a lap and can cause noise in the dataset because the distance elapsed is a HUGE outlier (we'll see why this is a problem in the CAPi use case).

**Visual Representation**

You can see the recovery sets inbetween the darker bars. Those are what we want to remove for the reasons listed above. Furthermore, the narrow bar on the end is me running down the hill to my house because I overshot on distance just a tiny bit. It should get dropped too because of it's miniscule length / moving time. 

![outliers](https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/example%20of%20outliers.png)

Once I removed all instances the dataset was around 3200 observations, which is still plenty. Here are the new results.

<br/>

**Random Forest Results:&nbsp;&nbsp; RMSE = 4.48&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MAPE = 1.7%**

**XGBoost Results:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;RMSE = 2.64&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;MAPE = 1.0%**

<br/>

The hypothesis on the recovery and the spillover laps seems to hold true, as the error decreased by a reasonable amount. I did try to utilize Random Forest for feature seleciton, and the error didn't really change that much (slight increase). I felt that keeping the variables made the most sense because the compute is basically the same. I ended up going with the XGBoost and storing it in `CAPi.pkl` so that we can call on it for predictions in the app script.

## CAPi and CAPi Equation
## Use Case on Run
## Limitations and Next Steps
