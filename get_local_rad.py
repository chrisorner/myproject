# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 17:41:37 2018

@author: Chris
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import datetime
#import matplotlib.pyplot as plt

#resp = requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=14.42076&latitude=50.08804&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI')
#resp=requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=149.117&latitude=-35.277&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI&format=json')
from geopy.geocoders import Nominatim

#(40.7410861, -73.9896297241625)
#print(location.raw)

def create_rad(location):

    
    geolocator = Nominatim(user_agent="Enefso")
    location = geolocator.geocode(location)
    #print(location.address)
    #Flatiron Building, 175, 5th Avenue, Flatiron, New York, NYC, New York, ...
    #print((location.latitude, location.longitude))
    lon= location.longitude
    lat= location.latitude
    
    
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
    #print(rad)
    
    substring = str(datetime.date.today()+ datetime.timedelta(days=1))
    day1=[]
    numt=0
    time_30min=np.linspace(0,1410,48)
    rad_30min=[]
    for num in range(len(period_end)):
        if substring in period_end[num]:
            rad_30min.append(rad[num])
            day1.append((time_30min[numt],rad[num]))
            numt+=1
    
    time_1h= np.linspace(0,1380,24)
    rad_1h= rad_30min[::2]
    
    return time_1h,rad_1h


loc= 'Munich'
time, rad= create_rad(loc)
#print(rad)



#plt.plot(time/60,rad)
#plt.show()