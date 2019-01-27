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
    
    str_tomorrow = str(datetime.date.today()+ datetime.timedelta(days=1))
    #str_today = str(datetime.date.today())
    day1=[]
    numt=0
    time_30min=np.linspace(0,1410,48)
    rad_30min=[]
    for num in range(len(period_end)):
        if str_tomorrow in period_end[num]:
            rad_30min.append(rad[num])
            day1.append((time_30min[numt],rad[num]))
            numt+=1
    
    
    for num in range(len(period_end)):
        if str_tomorrow in period_end[num]:
            start_num= num 
            break
    
    #print(start_num)    
    rad_1h6d= rad[start_num::]
    #print(len(rad_1h6d))
       
    
    time_1h1d= np.linspace(0,1380,24)
    rad_1h1d= rad_30min[::2]
    
    time_1h6d= np.linspace(0,8580,24*6)
    rad_1h6d=rad_1h6d[:288:2]

    
    return (time_1h1d,rad_1h1d),(time_1h6d, rad_1h6d)


#loc= 'Munich'
#result1d, result6d= create_rad(loc)




#plt.plot(result6d[0]/60,result6d[1])
#plt.show()