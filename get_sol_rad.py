# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 17:41:37 2018

@author: Milos
"""

import requests
import numpy as np
import matplotlib.pyplot as plt

#resp = requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=14.42076&latitude=50.08804&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI')
#resp=requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=149.117&latitude=-35.277&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI&format=json')
from geopy.geocoders import Nominatim
geolocator = Nominatim(user_agent="specify_your_app_name_here")
location = geolocator.geocode("Munich")
#print(location.address)
#Flatiron Building, 175, 5th Avenue, Flatiron, New York, NYC, New York, ...
print((location.latitude, location.longitude))
lon= location.longitude
lat= location.latitude
date='2018-12-22'
#(40.7410861, -73.9896297241625)
#print(location.raw)



def solar_rad(lon, lat, date):

    data=dict(longitude= str(lon), latitude=str(lat), api_key= '0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI', format='json')
    resp=requests.get('https://api.solcast.com.au/radiation/forecasts', params=data)
    if resp.status_code != 200:
        # This means something went wrong.
        print(resp.status_code)
    json_resp=resp.json()
    period_end=[]
    rad= []
    for result in json_resp['forecasts']:
        rad.append(result['ghi'])
        period_end.append(result['period_end'])
    #print(period_end)
    
    # 1 Day
    
    
    substring = date
    day1=[]
    numt=0
    time=np.linspace(0,1410,48)
    rad1=[]
    for num in range(len(period_end)):
        if substring in period_end[num]:
            rad1.append(rad[num])
            day1.append((time[numt],rad[num]))
            numt+=1
    
    return time,rad1

time, rad= solar_rad(lon,lat,date)

    
plt.plot(time/60,rad)
plt.show()