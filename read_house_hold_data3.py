# yearly line plots
from pandas import read_csv
#from matplotlib import pyplot


def consumer_data(data):

    # get all observations for the year
    result = data[str(2007)]
    result_sel = result['Global_active_power']
    result_sel.index.name = 'datetime'
    # print(result08.size)
    #result08_resample = result08.resample('H').mean()
    # power_tot08 = result08.sum()/60
    result_sel.fillna(0, inplace=True)
    return result


# dataset = read_csv('household_power_consumption.csv', header=0, infer_datetime_format=True, parse_dates=['datetime'],
#                    index_col=['datetime'])

# df = consumer_data(dataset)


# plot the active power for the year
# pyplot.figure()
# pyplot.plot(result08['2008-01'])
# pyplot.plot(result08_resample['2008-01'])
# pyplot.show()
