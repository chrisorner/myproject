# -*- coding: utf-8 -*-
"""
Created on Thu Jan 17 06:26:26 2019
@author: chris
"""
import numpy as np
np.set_printoptions(threshold=np.nan)
import dash
import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import requests
# from geopy.geocoders import Nominatim
from get_local_rad import create_rad
from get_local_rad2 import create_rad_jrc
from read_house_hold_data3 import consumer_data
from calculations import Solar, Battery, Costs
import datetime

## same function also in calculations file. Global variables to be removed
#
# d_len = 10
# d_hours = np.arange(1, 25, 1)
# t_len = np.size(d_hours)
# t_ges = np.arange(1, t_len * d_len + 1, 1)

##Start of Web Application##
server = Flask(__name__)

## connect to SQL Database
# 1 is for localhost, 1 for deployed app

# SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
#    username="chrisorn",
#   password="Handball",
#    hostname="chrisorn.mysql.pythonanywhere-services.com",
#    databasename="chrisorn$test",
# )
SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="root",
    password="Handball",
    hostname="localhost",
    databasename="energyapp",
)

server.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
server.config["SQLALCHEMY_POOL_RECYCLE"] = 299
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(server)


class SolarCell(db.Model):
    __tablename__ = "Photovoltaik"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    efficiency = db.Column(db.Float)

    def __init__(self, id, name, efficiency):
        self.id = id
        self.name = name
        self.efficiency = efficiency


all_cells = SolarCell.query.all()


## End of SQL stuff        


### Start of the Application ####
app = dash.Dash(__name__, server=server)

app.title = 'Energy Systems Simulator'
app.css.append_css({'external_url': 'https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css'})

# Initialize  user consumption
df = pd.DataFrame({
    'Hour': [str(i) for i in range(1, 25)],
    'Energy Consumption [kWh]': [0.2, 0.2, 0.2, 0.2, 0.2, 1, 1.5, 1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.8, 1.5,
                                 1, 0.8, 0.8, 0.5, 0.2, 0.2]
}, columns=['Hour', 'Energy Consumption [kWh]'])

# load energy constumption data
dataset = pd.read_csv('household_power_consumption1.csv', header=0, infer_datetime_format=True, parse_dates=['datetime'],
                   index_col=['datetime'])
consumption = consumer_data(dataset)

## GUI is created here
app.layout = html.Div([

    html.H1('Solar Energy Calculator'),
    html.Div([
        html.Div([
            html.H5('Select Graph'),
            dcc.Dropdown(
                id='select_Graph',
                options=[
                    {'label': 'Radiation & Consumption', 'value': 'rad_graph'},
                    {'label': 'Energy Overview', 'value': 'power_graph'},
                    {'label': 'Costs', 'value': 'cost_graph'}
                ])
        ], className='col-3'),
        html.Div([
            html.H5('Select Calculation'),
            dcc.Dropdown(
                id='select_calc',
                options=[
                    {'label': 'Investment Analysis', 'value': 'invest'},
                    {'label': 'Forecast', 'value': 'forec'}
                ])
        ], className='col-3')
    ], className='row'),
    html.Div([
        html.Div([html.Button('Start Calculation', id='button_calc', className='btn btn-primary')], className='col-3')
    ], className='row my-2'),
    html.Div([
        html.Div([
            dcc.Graph(id='graph-with-slider', config={'displayModeBar': False})], className='col-6'),
        html.Div([
            html.Div([
                html.H4('Energy System', className='col-12'),
                html.Div([
                    html.Label('Solar Panels Area [m2]', id='A_cells_label'),
                    dcc.Input(id='A_cells', value='50', type='text', className='form-control')
                ], className='col-4 offset-md-1'),
                html.Div([
                    html.Label('Battery Capacity [kWh]', id='cap_label'),
                    dcc.Input(id='capacity', value='5', type='text', className='form-control')
                ], className='col-4 offset-md-1')
            ], className='row my-4'),
            html.Div([
                html.H4('Select Solar Panel', className='col-12'),
                html.Div([
                    dcc.Dropdown(
                        id='select_database',
                        options=[{'label': [cell.name+' ('+str(cell.efficiency)+'%)'], 'value': cell.name} for cell in all_cells
                                 ], value='LG')
                ], className='col-4 offset-md-1'),
                html.Div([

                ], className='col-4 offset-md-1')
            ], className='row my-4'),
            html.Div([
                html.H4('Cost Data', className='col-12'),
                html.Div([
                    html.Label('Battery [EUR/kWh]', id='cost_label'),
                    dcc.Input(id='cost_bat', value='1500', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Grid supply [EUR/kWh]', id='cost_label2'),
                    dcc.Input(id='cost_kwh', value='0.3', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Solar Panels [EUR/kWp]', id='cost_label3'),
                    dcc.Input(id='cost_wp', value='1923', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Number of Years', id='years_label'),
                    dcc.Input(id='years', value='20', type='number', className='form-control')
                ], className='col-3')
            ], className='row my-4 align-items-end')
        ], className='col-6')
    ], className='row'),

    html.Div([
        html.Div([
            html.H4('Energy Consumption Over Day'),
            dt.DataTable(
                columns=[{"name": i, "id": i} for i in df.columns],
                data=df.to_dict("records"),
                n_fixed_rows=1,
                style_table={'maxHeight': '300', 'overflowY': 'scroll'},
                # optional - sets the order of columns
                # columns=sorted(DF_SIMPLE.columns),
                editable=True,
                id='editable-table')
        ], className='col-4'),
        html.Div([
            html.H4('Get Solar Radiation', className='col-12'),
            html.Div([
                html.Div([html.Label('Location', id='location_label'),
                          dcc.Input(id='location', type='text', className='form-control', value='Berlin')
                          ], className='col-7'),
                html.Div([html.Button('Submit', id='button_loc', className='btn btn-primary')]),
                dcc.Input(id='output-provider2', type='hidden')
            ], className='row mt-4 ml-3 align-items-end'),
        ], className='col-4 offset-md-2')
    ], className='row'),

    html.Div([
        html.H4('Database', className='col-12'),
        html.Div([
            html.Label('Type of Solar Panel', id='typeSP_label'),
            dcc.Input(id='typeSP', type='text', className='form-control'),
        ], className='col-3'),
        html.Div([
            html.Label('Efficiency', id='efficiencySP_label'),
            dcc.Input(id='efficiency', type='text', className='form-control')
        ], className='col-3'),
        html.Div([
            dcc.ConfirmDialogProvider(children=html.Button('Submit', id='button',
                                                           className='btn btn-primary'), id='confirm',
                                      message='Solar cell was added to database')
        ]),
        html.P(id='placeholder'),
        html.Div(id='output-provider')
    ], className='row my-4 align-items-end'),

], className='mx-3')


@app.callback(
    dash.dependencies.Output('output-provider2', 'value'),
    [dash.dependencies.Input('button_loc', 'n_clicks')],
    [dash.dependencies.State('location', 'value')])
def get_loc_rad(n_clicks, loc):
    # get the radiation for location
    rad_data1d, rad_data7d = create_rad(loc)
    rad_data_hist = create_rad_jrc(loc)
    return (rad_data_hist, rad_data7d[1])


@app.callback(
    dash.dependencies.Output('placeholder', 'children'),
    [dash.dependencies.Input('button', 'n_clicks')],
    [dash.dependencies.State('typeSP', 'value'),
     dash.dependencies.State('efficiency', 'value')])
# Add new solar cell to database
def update_db(n_clicks, typeSP, effic):
    if n_clicks is not None:
        new_entry = SolarCell(None, typeSP, effic)
        db.session.add(new_entry)
        db.session.commit()


@app.callback(dash.dependencies.Output('output-provider', 'children'),
              [dash.dependencies.Input('confirm', 'submit_n_clicks')])
def display_confirm(submit_n_clicks):
    return ''


@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('select_Graph', 'value'),
     dash.dependencies.Input('select_calc', 'value'),
     dash.dependencies.Input('select_database', 'value'),
     dash.dependencies.Input('button_calc', 'n_clicks'),
     dash.dependencies.Input('output-provider2', 'value')],
    [dash.dependencies.State('cost_bat', 'value'),
     dash.dependencies.State('capacity', 'value'),
     dash.dependencies.State('years', 'value'),
     dash.dependencies.State('cost_kwh', 'value'),
     dash.dependencies.State('cost_wp', 'value'),
     dash.dependencies.State('A_cells', 'value'),
     dash.dependencies.State('editable-table', 'data')],
)
def update_cost(sel_graph, sel_calc, sel_cell, n_clicks, loc_rad, cost_bat, cap_bat, years_input, cost_kwh, cost_wp,
                area_cells, rows):
    ##Update everything with input data
    Temp = 298  # Ambient Temperature
    years_input = int(years_input)

    # Find today's date and end date in 5 days
    time_vec6d= np.linspace(0,8580,24*6)
    today = datetime.datetime.today().strftime('2007-%m-%dT00:00')
    time_end = datetime.date.today() + datetime.timedelta(days=5)
    end_time = time_end.strftime('2007-%m-%dT23:00')

    # 1 year consumption
    dff = consumption
    # consumption for short term forecast
    dff2 = dff.loc[today:end_time]

    if sel_calc == 'forec':
        rad_val = loc_rad[1]
        rad_time = [x / 60 for x in time_vec6d]

        dff = dff2
    else:
        #df = pd.read_csv('hist_irrad.csv')
        #last_year = '2018'
        #rad_val = []

        #for num in range(len(df['PeriodEnd'])):
        #    if last_year in df['PeriodEnd'].iloc[num]:
        #        rad_val.append(df['Ghi'].iloc[num])

        rad_val=loc_rad[0][:8760]
        rad_time = np.linspace(1, 8760*years_input, 8760*years_input)
        # rad_time = rad_time[0:2000]
        # rad_val = rad_val[0:2000]

    t_len = len(rad_val)
    d_len = int(t_len / 24)

    # if days_input > 5 and sel_graph=='power_graph':
    #    days_input = 5

    # dff_conc=pd.concat([dff]*d_ges)
    df_num = pd.to_numeric(dff['Global_active_power'])
    df_num = df_num.as_matrix()

    for cell in all_cells:
        if cell.name == sel_cell:
            cell_obj = cell

    grid_costs = []
    solar_costs = []
    e_batt = []
    p_sol = []
    e_grid = []
    p_cons = []

    if n_clicks:

        sol = Solar(rad_val)
        area_cells = float(area_cells)
        # Sol.calc_Pmpp(Ncells,Temp,rad_ampl,rad_width,Isc,Uoc)
        p_sol = sol.calc_power(rad_val, area_cells, cell_obj)
        p_peak = area_cells*cell_obj.efficiency/100*1000
        cost = Costs(rad_val, years_input, cost_kwh, p_peak)

        cost.calc_costs(rad_val, years_input, cap_bat, cost_bat, p_peak, cost_wp, df_num, area_cells, cell_obj)
        grid_costs = cost.total_costs
        solar_costs = cost.total_costs_sol

        bat = Battery(rad_val)
        bat.calc_soc(rad_val, cap_bat, df_num, area_cells, cell_obj)
        e_batt = bat.get_stored_energy()
        e_grid = bat.get_from_grid()
        e_sell = bat.get_w_unused()

        p_cons = df_num

    # Create Graphs
    trace1 = (go.Scatter(
        x=np.arange(0, d_len*years_input + 1, 1),
        y=grid_costs,
        name='Without Solar Panels',
    ))

    trace2 = (go.Scatter(
        x=np.arange(0, d_len*years_input + 1, 1),
        y=solar_costs,
        name='With Solar Panels',
    ))

    trace3 = (go.Scatter(
        x=rad_time[0:119],
        y=e_batt[0:119],
        name='W_stored',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'white'}
        },
    ))
    trace4 = (go.Scatter(
        x=rad_time[0:119],
        y=p_sol[0:119],
        name='W_solar',
        yaxis='y2',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'blue'}
        },
    ))
    trace5 = (go.Scatter(
        x=rad_time[0:119],
        y=e_grid[0:119],
        name='W_grid',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'green'}
        },
    ))
    trace6 = (go.Scatter(
        x=rad_time[0:8760],
        y=rad_val[0:8760],
        name='Radiation',
        yaxis='y1',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'white'}
        },
    ))
    trace7 = (go.Scatter(
        x=rad_time,
        y=p_cons,
        name='Consumption',
        yaxis='y2',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'blue'}
        },
    ))

    traces = [trace1, trace2, trace3, trace4, trace5, trace6, trace7]

    if sel_graph == 'cost_graph':
        return {
            'data': traces[0:2],
            'layout': go.Layout(
                title='Cost Estimation',
                xaxis={'title': 'Days/Years'},
                yaxis={'title': 'Costs [Eur]'},
                legend=dict(x=-.1, y=1.2)
            )
        }

    elif sel_graph == 'power_graph':
        return {
            'data': traces[2:5],
            'layout': go.Layout(
                title='Energy Overview',
                xaxis={'title': 'Time'},
                yaxis1={'title': 'Energy [kWh]', 'rangemode': 'tozero'},
                yaxis2={'title': 'Solar Power [W]', 'rangemode': 'tozero', 'overlaying': 'y', 'side': 'right'},
                legend=dict(x=-.1, y=1.1, orientation='h')
            )
        }
    else:
        return {
            'data': traces[5:7],
            'layout': go.Layout(
                title='Daily Radiation and Consumption',
                xaxis={'title': 'Time'},
                yaxis1={'title': 'Radiation [W/m2]', 'range': [0, 1000]},
                yaxis2={'title': 'Consumption [kW]', 'overlaying': 'y', 'side': 'right', 'range': [0, 10]},
                legend=dict(x=-.1, y=1.2)
            )
        }


app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server()
