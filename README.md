![image](https://raw.githubusercontent.com/jbblancojr/CAPi/main/images/cropped_version.png)
**Climate Adjusted Pace individualized (CAPi) is a predictive model trained on a users Strava data. It leverages optimal weather conditions from personal research to return a Climate Adjusted Pace (CAP) for an athlete. Similar to Gradient Adjusted Pace (GAP), this will help athletes train more efficiently in suboptimal weather conditions.**

## Purpose
I began my endurance running journey with the 2021 NYC Marathon and have gotten more involved in the sport and community since. Most of my training has traditionally been in intense heat and humidity, as I did undergrad in the mid-south at Rhodes College. So, as I begun to take things more seriously and look toward running a Boston Qualifying time (BQ), I became much more aware of tracking things like my heartrate, cadence, regular and gradient adjusted pace, etc. This led me to my personal research to discover: [How does weather impact runners?](https://github.com/jbblancojr/Marathon-Weather-Analysis-and-Performance-Prediction). After spending a majority of my senior year on this research, I knew I wanted to leverage Machine Learning and Data Science to derive some value from my findings. This is when I decided to build **CAPi**.

#### Summary
CAPi will first train on a users existing [Strava](https://www.strava.com) data, so that it can predict your moving time for a given lap in your Strava activity, given the current weather conditions. From there, CAPi will impute optimal weather conditions and repredict that lap, take the difference of its two predictions and subtract that margin from the real, providing an approximated CAP. 

#### Value
In a nutshell, **CAPi** is a tool for runners to help them train better in poor climate. The model provides a Climate Adjusted Pace (CAP) that you can utilize to better understand whether or not you over/under exherted on your run, or what your true time in a race could have been if the conditions weren't so harsh.

While this information is generally more beneficial to serious runners rather casual ones (esepcailly those familiar with heartrate zones and zone training), it will help democratize a generally understood concept in the advanced running community that your heartrate is effected by the climate, which will in turn effect your performance.


## Collecting Data & Building Client
## Model Selection & Results
## CAPi and CAPi Equation
## Use Case on Run
## Limitations and Next Steps
