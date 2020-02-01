import pandas as pd

E_cons= pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile.csv",names=['Total'])
E_cons['Electronics']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupElectronics.csv")
E_cons['Frdige']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupFridges.csv")
E_cons['Inductive']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupInductive.csv")
E_cons['Lighting']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupLighting.csv")
E_cons['Other']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupOther.csv")
E_cons['Standby']=pd.read_csv("C:/Users/chris/Desktop/myproject/Material/alpg-master/output/results/Electricity_Profile_GroupStandby.csv")
#E_cons.index = E_cons.index.map(str)
date_time= pd.date_range(start='2018-01-01', end='2018-12-31 23:59:00', freq= 'T')
E_cons['Time']= date_time
E_cons.set_index('Time', inplace=True)


start= pd.Timestamp('2018-08-01')
end= pd.Timestamp('2018-08-31 23:59:00')
end1= pd.Timestamp('2018-08-01 23:59:00')
select= (E_cons.index>= start) & (E_cons.index<=end1)

data_range= E_cons.loc[select]

#data_range.plot.line()
data_range['Lighting'].plot.line()

print(data_range.head())