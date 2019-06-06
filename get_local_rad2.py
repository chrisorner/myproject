# -*- coding: utf-8 -*-
"""
Created on Fri Nov  9 17:41:37 2018

@author: Chris
"""

import requests
import numpy as np
import matplotlib.pyplot as plt
import datetime
import pandas as pd
#import matplotlib.pyplot as plt

#resp = requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=14.42076&latitude=50.08804&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI')
#resp=requests.get('https://api.solcast.com.au/radiation/forecasts?longitude=149.117&latitude=-35.277&api_key=0ePhpu3zEA9qdcre7P7e38G2JiQ4wMTI&format=json')
from geopy.geocoders import Nominatim

#(40.7410861, -73.9896297241625)
#print(location.raw)

def create_rad_jrc(location):

    
    geolocator = Nominatim(user_agent="Enefso")
    location = geolocator.geocode(location)
    #print(location.address)
    #Flatiron Building, 175, 5th Avenue, Flatiron, New York, NYC, New York, ...
    #print((location.latitude, location.longitude))
    long= location.longitude
    lati= location.latitude
    
    
    data=dict(lon= str(long), lat=str(lati), startyear=2016, endyear=2016)
    resp=requests.get('http://re.jrc.ec.europa.eu/pvgis5/seriescalc.php', params=data)
    if resp.status_code != 200:
        # This means something went wrong.
        print(resp.status_code)
    idx_start= resp.text.index('201')

    content1= resp.text[idx_start:]
    idx_end = content1.index('G_i')
    content2= content1[0:idx_end]
    data= content2.replace('\r\n', ',')
    data2= data[:-2].split(',')


    df = pd.DataFrame(np.array(data2).reshape(8784, 6), columns=['date', 'g_i', 'As', 'Tamb', 'W10', 'int'])
    df['date'] = pd.to_datetime(df['date'], format='%Y%m%d:%H%M')
    df['g_i'] = df['g_i'].astype('float')
    df['As'] = df['As'].astype('float')
    df['W10'] = df['W10'].astype('float')
    df['int'] = df['int'].astype('float')

    rad= df['g_i'].values.tolist()


    
    return rad


#create_rad('Paris')
#loc= 'Munich'
#result1d, result6d= create_rad(loc)




#plt.plot(result6d[0]/60,result6d[1])
#plt.show()