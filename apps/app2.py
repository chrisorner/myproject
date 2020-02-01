import numpy as np
import json
np.set_printoptions(threshold=np.nan)
import dash
import dash_table as dt
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.graph_objs as go
import pandas as pd
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# import requests
# from geopy.geocoders import Nominatim
from get_local_rad import create_rad
from get_local_rad2 import create_rad_jrc
from read_house_hold_data3 import consumer_data
from calculations import Solar2, Battery, Costs
from read_alpg_data import alpg_read_data
import datetime
import pvlib
from pvlib import pvsystem

import matplotlib.pyplot as plt

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
SQLALCHEMY_DATABASE_URI = "mysql://{username}:{password}@{hostname}/{databasename}".format(
    username="root",
    password="Handball",
    hostname="localhost",
    databasename="energyapp",
)

server.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
server.config["SQLALCHEMY_POOL_RECYCLE"] = 299
server.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(server)


class BatteryDB(db.Model):
    __tablename__ = "Photovoltaik"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    capacity = db.Column(db.Float)
    cost = db.Column(db.Float)

    def __init__(self, name, capacity, bat_cost):
#        self.id = id
        self.name = name
        self.capacity = capacity
        self.cost = bat_cost

db.create_all()
all_batteries = BatteryDB.query.all()

## End of SQL stuff


### Start of the Application ####
app = dash.Dash(__name__, server=server)

app.title = 'Energy Systems Simulator'
external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css']
#    , 'https://codepen.io/chriddyp/pen/brPBPO.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)


# Initialize  user consumption
df = pd.DataFrame({
    'Hour': [str(i) for i in range(1, 25)],
    'Energy Consumption [kWh]': [0.2, 0.2, 0.2, 0.2, 0.2, 1, 1.5, 1, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.8, 1.5,
                                 1, 0.8, 0.8, 0.5, 0.2, 0.2]
}, columns=['Hour', 'Energy Consumption [kWh]'])

# load energy constumption data
dataset = pd.read_csv('household_power_consumption1.csv', header=0, infer_datetime_format=True,
                      parse_dates=['datetime'],
                      index_col=['datetime'])
consumption = consumer_data(dataset)
all_modules = pvsystem.retrieve_sam(name='SandiaMod')
module_names = list(all_modules.columns)

alpg_data = alpg_read_data()

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
                ], value= 'rad_graph')
        ], className='col-3'),

    ], className='row'),
    html.Div([
        html.Div([html.Button('Start Calculation', id='button_calc', className='btn btn-primary')], className='col-3')
    ], className='row my-2'),
    html.Div([
        html.Div([
            dcc.Tabs(id="tabs-graph", value='tab-cost', children=[
            dcc.Tab(label='Costs', value='tab-cost', children=[
                html.Div([
                    dcc.Graph(id='graph-with-slider', config={'displayModeBar': False})
                    ])]),
            dcc.Tab(label='Consumption', value='tab-cons', children=[
                html.Div([
                    dcc.Graph(id='cons_graph', config={'displayModeBar': False})
            ]),
                html.Div([
                    dcc.Checklist(id= 'checkbox_cons_data',
                        options=[
                            {'label': ' Total Energy', 'value': 'Total'},
                            {'label': ' Electronics', 'value': 'Electronics'},
                            {'label': ' Fridge', 'value': 'Fridge'},
                            {'label': ' Inductive', 'value': 'Inductive'},
                            {'label': ' Lighting', 'value': 'Lighting'},
                            {'label': ' Other', 'value': 'Other'},
                            {'label': ' Standby', 'value': 'Standby'}
                        ],
                        value=['Total'],
                    )
                ], className= 'col-2'),
                html.Div([
                dcc.Dropdown(
                    id='season',
                    options=[
                            {'label': 'Spring', 'value': 'spring'},
                            {'label': 'Summer', 'value': 'summer'},
                            {'label': 'Autumn', 'value': 'autumn'},
                            {'label': 'Winter', 'value': 'winter'}
                             ], value='summer')
                ], className= 'col-4')
            ]),
            dcc.Tab(label='Solar Power', value='tab-power', children=[
                html.Div([
                    dcc.Graph(id='graph_solpower', config={'displayModeBar': False})
                ]),

            ])
            ]),

        ], className='col-6'),
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
                html.Label('Select Battery from Database'),
                daq.BooleanSwitch(
                  id='checkbox_battery',
                  on=True
                )
            ], className='row my-4'),
            html.Div([
                html.Div([
                    html.Label('Batteries'),
                    dcc.Dropdown(
                        id='battery_database',
                        options=[{'label': bat.name , 'value': bat.name} for
                                 bat in all_batteries
                                 ], value= 'Tesla')
 #                       options= [
 #                           {'label': 'Tesla', 'value': 'Tesla'},
 #                           {'label': 'LG', 'value': 'LG'}
 #                       ], value='Tesla'),
                ], className='col-4'),
                html.Div([
                    html.Label('Solar Panels'),
                    dcc.Dropdown(
                        id='sandia_database',
                        options=[{'label': module, 'value': module} for module in all_modules],
                        value='Canadian_Solar_CS5P_220M___2009_'),
                ], className='col-4')
            ],className='row my-4'),
            html.Div([
                html.Div([
                    html.Label('Panel Tilt [Deg]', id='tilt'),
                    dcc.Input(id='panel_tilt', value='30', type='number', className='form-control')
                ],className='col-3'),
                html.Div([
                    html.Label('Panel Orientation [Deg]', id='orient'),
                    dcc.Input(id='panel_orient', value='180', type='number', className='form-control')
                ],className='col-3'),

            ], className='row my-4 align-items-end'),
            html.Div([
                html.H4('Cost Data', className='col-12'),
                html.Div([
                    html.Label('Battery [EUR/kWh]', id='cost_label'),
                    dcc.Input(id='cost_bat', value='1500', type='text', className='form-control')
                ], className='col-2'),
                html.Div([
                    html.Label('Grid supply [EUR/kWh]', id='cost_label2'),
                    dcc.Input(id='cost_kwh', value='0.3', type='text', className='form-control')
                ], className='col-2'),
                html.Div([
                    html.Label('Solar Panels [EUR/kWp]', id='cost_label3'),
                    dcc.Input(id='cost_wp', value='1923', type='text', className='form-control')
                ], className='col-2'),
                html.Div([
                    html.Label('Number of Years', id='years_label'),
                    dcc.Input(id='years', value='20', type='number', className='form-control')
                ], className='col-2'),
                html.Div([
                    html.Label('Increase of Energy Cost', id='inc_cost_label'),
                    dcc.Input(id='inc_cost_ener', value='0.01', type='text', className='form-control')
                ], className='col-2'),
                html.Div([
                    html.Label('Inflation', id='inflation_label'),
                    dcc.Input(id='inflation', value='0.02', type='text', className='form-control')
                ], className='col-2'),
            ], className='row my-4 align-items-end'),
            html.Div([
                html.H4('Energy System', className='col-12'),
                html.Div([
                    html.Label('Location', id='location_label'),
                    dcc.Input(id='location', type='text', className='form-control', value='Berlin')
                ], className='col-4 offset-md-1'),
                html.Div([
                    html.Div([html.Button('Submit', id='button_loc', className='btn btn-primary')])
                ], className='col-4 offset-md-1')
            ], className='row my-4'),
        ], className='col-6')
    ], className='row'),

    html.Div([
       # html.Div([
       #     html.H4('Energy Consumption Over Day'),
       #     dt.DataTable(
       #         columns=[{"name": i, "id": i} for i in df.columns],
       #         data=df.to_dict("records"),
       #         n_fixed_rows=1,
       #         style_table={'maxHeight': '300', 'overflowY': 'scroll'},
                # optional - sets the order of columns
                # columns=sorted(DF_SIMPLE.columns),
       #         editable=True,
       #         id='editable-table')
        #], className='col-4'),

    ], className='row'),

    html.Div([
        html.H4('Database', className='col-12'),
        html.Div([
            html.Label('Battery Name', id='typeCap_label'),
            dcc.Input(id='type_bat', type='text', className='form-control'),
        ], className='col-2'),
        html.Div([
            html.Label('Battery Capacity', id='efficiencySP_label'),
            dcc.Input(id='inp_capacity', type='text', className='form-control')
        ], className='col-2'),
        html.Div([
            html.Label('Battery Cost'),
            dcc.Input(id='inp_bat_cost', type='text', className='form-control')
        ], className='col-2'),
        html.Div([
            dcc.ConfirmDialogProvider(children=html.Button('Submit', id='button',
                                                           className='btn btn-primary'), id='confirm',
                                      message='Solar cell was added to database')
        ]),
        html.Div([
            dcc.ConfirmDialogProvider(children=html.Button('Clear DB', id='delte_button',
                                                           className='btn btn-primary'), id='confirm_delete',
                                      message='Database has been cleared')
        ]),


        html.P(id='placeholder_database_entry', style={'display': 'none'}),
        html.Div(id= 'placeholder_delete_db',style={'display': 'none'}),
        html.Div(id='placeholder_confirm', style={'display': 'none'}),
        html.Div(id='store_p_sol', style={'display': 'none'}),
        html.Div(id='store_p_cons', style={'display': 'none'}),
        html.Div(id='store_rad', style={'display': 'none'}),
        html.Div(id='store_e_batt', style={'display': 'none'}),
        html.Div(id='store_e_grid', style={'display': 'none'}),
        html.Div(id='store_e_sell', style={'display': 'none'}),
        html.Div(id='store_grid_costs', style={'display': 'none'}),
        html.Div(id='store_solar_costs', style={'display': 'none'}),
        html.Div(id='store_location', style={'display': 'none'})
    ], className='row my-4 align-items-end'),



], className='mx-3')



@app.callback(
    dash.dependencies.Output('placeholder_database_entry', 'children'),
    [dash.dependencies.Input('confirm', 'submit_n_clicks')],
    [dash.dependencies.State('type_bat', 'value'),
     dash.dependencies.State('inp_capacity', 'value'),
     dash.dependencies.State('inp_bat_cost', 'value')]
)
# Add new solar cell to database
def update_db(submit_n_clicks, type_bat, cap, bat_cost):
    if submit_n_clicks is not None:
        with server.app_context():
            new_entry = BatteryDB(type_bat, cap, bat_cost)
            db.session.add(new_entry)
            db.session.commit()

@app.callback(
    dash.dependencies.Output('placeholder_delete_db', 'children'),
    [dash.dependencies.Input('confirm_delete', 'submit_n_clicks')]
)
# Delete Database
def delete_db(submit_n_clicks):
    if submit_n_clicks is not None:
        with server.app_context():
        #    BatteryDB.query.delete()
        #    db.session.commit()
            db.drop_all()
         #   db.create_all()



@app.callback(dash.dependencies.Output('placeholder_confirm', 'children'),
              [dash.dependencies.Input('confirm', 'submit_n_clicks')])
def display_confirm(submit_n_clicks):
    return ''

@app.callback(
    dash.dependencies.Output('store_location', 'children'),
    [dash.dependencies.Input('button_loc', 'n_clicks')],
    [dash.dependencies.State('location', 'value')])
def change_loc(n_clicks, location):
    return location


@app.callback(

    [dash.dependencies.Output('store_p_sol', 'children'),
     dash.dependencies.Output('store_p_cons', 'children'),
     dash.dependencies.Output('store_rad', 'children'),
     dash.dependencies.Output('store_e_batt', 'children'),
     dash.dependencies.Output('store_e_grid', 'children'),
     dash.dependencies.Output('store_e_sell', 'children'),
     dash.dependencies.Output('store_grid_costs', 'children'),
     dash.dependencies.Output('store_solar_costs', 'children')],
    [dash.dependencies.Input('sandia_database', 'value'),
     dash.dependencies.Input('battery_database', 'value'),
     dash.dependencies.Input('store_location', 'children'),
     dash.dependencies.Input('button_calc', 'n_clicks')],
    [dash.dependencies.State('cost_bat', 'value'),
     dash.dependencies.State('checkbox_battery','on'),
     dash.dependencies.State('capacity', 'value'),
     dash.dependencies.State('years', 'value'),
     dash.dependencies.State('cost_kwh', 'value'),
     dash.dependencies.State('cost_wp', 'value'),
     dash.dependencies.State('A_cells', 'value'),
     dash.dependencies.State('panel_tilt','value'),
     dash.dependencies.State('panel_orient','value'),
     dash.dependencies.State('inc_cost_ener','value'),
     dash.dependencies.State('inflation','value'),
     ],
)
def update_cost(module,battery_sel, loc, n_clicks, cost_bat, database_bat, cap_bat, years_input, cost_kwh, cost_wp,
                area_cells, tilt, orient, cost_inc, infl):
    ##Update everything with input data
    Temp = 298  # Ambient Temperature
    years_input = int(years_input)

    # Find today's date and end date in 5 days
    time_vec6d = np.linspace(0, 8580, 24 * 6)
    today = datetime.datetime.today().strftime('2008-%m-%dT00:00')
    time_end = datetime.date.today() + datetime.timedelta(days=5)
    end_time = time_end.strftime('2008-%m-%dT23:00')

    # 1 year consumption
    dff = consumption
    # consumption for short term forecast
    dff2 = dff.loc[today:end_time]


    # rad_val=loc_rad[0][:8760]
    # rad_time = np.linspace(1, 8760*years_input, 8760*years_input)

    # t_len = len(rad_val)
    # d_len = int(t_len / 24)

    df_num = pd.to_numeric(dff['Global_active_power'])
    df_num = df_num.values

    for bat in all_batteries:
        if bat.name == battery_sel:
            bat_obj = bat


    if database_bat == True:
        bat_capacity = bat_obj.capacity
        bat_cost = bat_obj.cost
    else:
        bat_capacity = cap_bat
        bat_cost = float(cost_bat) * float(cap_bat)

    #if n_clicks:

        # Solar Model
    cost_inc= float(cost_inc)
    infl = float(infl)
    area_cells = float(area_cells)
    tilt = float(tilt)
    orient = float(orient)
    sol2 = Solar2()
    sol2.surface_tilt = tilt
    sol2.surface_azimuth = orient
    sol2.get_location(loc)
    times = pd.DatetimeIndex(start='2016-01-01', end='2016-12-31 23:00', freq='1h', tz=sol2.tz)
    irradiation = sol2.calc_irrad(times, sol2.latitude, sol2.longitude, sol2.tz, loc)
    irrad_global = irradiation['poa_global']
    p_sol = sol2.pv_system(times, irradiation, module, area_cells)

    # End Solar Model

    # sol = Solar(rad_val)

    # Sol.calc_Pmpp(Ncells,Temp,rad_ampl,rad_width,Isc,Uoc)
    #        p_sol = sol.calc_power(rad_val, area_cells, cell_obj)
    p_peak = area_cells * sol2.efficiency * 1000
    bat = Battery(irrad_global)
    bat.calc_soc(irrad_global, bat_capacity, df_num, p_sol)
    e_batt = bat.get_stored_energy()
    e_grid = bat.get_from_grid()
    e_sell = bat.get_w_unused()

    cost = Costs(irrad_global, years_input, cost_kwh, p_peak, cost_inc, infl)
    cost.calc_costs(irrad_global, years_input, bat_cost, p_peak, cost_wp, df_num, e_grid, e_sell)
    grid_costs = cost.total_costs
    solar_costs = cost.total_costs_sol

    p_cons = df_num
    irrad_array = irrad_global.values


    return json.dumps(p_sol.tolist()), json.dumps(p_cons.tolist()), json.dumps(irrad_array.tolist()), \
           json.dumps(e_batt.tolist()), json.dumps(e_grid.tolist()), json.dumps(e_sell.tolist()),\
           json.dumps(grid_costs.tolist()), json.dumps(solar_costs.tolist())


@app.callback(

    dash.dependencies.Output('graph_solpower', 'figure'),
    [dash.dependencies.Input('store_p_sol', 'children')])

def solar_power(sol_power_json):

        try:
            sol_power = json.loads(sol_power_json)
        except TypeError:
            sol_power= np.zeros(8785)

        rad_time = list(range(1,8785))
        trace1 = []
        trace1.append(go.Scatter(
            x=rad_time[0:8000],
            y=sol_power[0:8000],
            mode='lines',
            marker={
                'size': 5,
                'line': {'width': 0.5, 'color': 'blue'}
            }
        ))

        return {
            'data': trace1,
            'layout': go.Layout(
                title='Solar Power',
                xaxis={'title': 'Days/Years'},
                yaxis={'title': 'Power [W]'},
                legend=dict(x=-.1, y=1.2))
        }


@app.callback(
    dash.dependencies.Output('graph-with-slider', 'figure'),
    [dash.dependencies.Input('select_Graph', 'value'),
    dash.dependencies.Input('years', 'value'),
    dash.dependencies.Input('store_rad', 'children'),
    dash.dependencies.Input('store_e_batt', 'children'),
    dash.dependencies.Input('store_e_grid', 'children'),
    dash.dependencies.Input('store_e_sell', 'children'),
    dash.dependencies.Input('store_grid_costs', 'children'),
    dash.dependencies.Input('store_solar_costs', 'children')],
)

def update_graph_costs(sel_plot, years_input, rad_val_json, e_batt_json, e_grid_json, e_sell_json, grid_costs_json, solar_costs_json):

    traces= []


#    p_cons = json.loads(p_cons_json)
    try:
        rad_val = json.loads(rad_val_json)
        e_batt = json.loads(e_batt_json)
        e_grid = json.loads(e_grid_json)
        e_sell = json.loads(e_sell_json)
        grid_costs = json.loads(grid_costs_json)
        solar_costs = json.loads(solar_costs_json)
    except TypeError:
        rad_val = np.zeros(8785)
        e_batt = np.zeros(8785)
        e_grid = np.zeros(8785)
        e_sell = np.zeros(8785)
        grid_costs = np.zeros(21)
        solar_costs = np.zeros(21)


    years = int(years_input)

    # rad_time = np.linspace(1, 8760 * years, 8760)
    rad_time = list(range(0, 8785))
#    t_len = len(rad_val)
#    d_len = int(t_len / 24)

    # Create Graphs
    traces= []
    traces.append(go.Scatter(
        x=list(range(0, years + 1)),
        y=grid_costs,
        mode='lines',
        name= 'Cost without Solar Panels',
        marker={
            'size': 5,
            'line': {'width': 0.5, 'color': 'blue'}
        }
    ))

    traces.append(go.Scatter(
        x=list(range(0, years + 1)),
        y=solar_costs,
        mode='lines',
        name= 'Cost with Solar Panels',
        marker={
            'size': 5,
            'line': {'width': 0.5, 'color': 'blue'}
        }
    ))

    traces.append(go.Scatter(
            x=rad_time[0:119],
            y=e_batt[0:119],
            name='Energy Stored',
            mode='lines',
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            }
        ))

    traces.append(go.Scatter(
            x=rad_time[0:119],
            y=e_grid[0:119],
            name='Energy Bought',
            mode='lines',
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'green'}
            },
        ))

    traces.append(go.Scatter(
        x=rad_time[0:119],
        y=e_sell[0:119],
        name='Energy Sold',
        mode='lines',
        marker={
            'size': 15,
            'line': {'width': 0.5, 'color': 'green'}
        },
    ))

    traces.append(go.Scatter(
            x=rad_time[0:8784],
            y=rad_val[0:8784],
            name='Radiation',
            yaxis='y1',
            mode='lines',
            marker={
                'size': 15,
                'line': {'width': 0.5, 'color': 'white'}
            },
        ))

#    if sel_plot == 'cost_graph':
    return {
        'data': list(traces[0:2]),
        'layout': go.Layout(
            title='Costs',
            xaxis={'title': 'Years'},
            yaxis={'title': 'Costs [EUR]'},
            legend=dict(x=-.1, y=1.2))

    }
#    elif sel_plot == 'power_graph':
#    return {
#        'data': list(traces[2:5]),
#        'layout': go.Layout(
#            title='Energy Overview',
#            xaxis={'title': 'Time'},
#            yaxis={'title': 'Energy [kWh]', 'rangemode': 'tozero'},
#            legend=dict(x=-.1, y=1.1, orientation='h'))
#    }

#    elif sel_plot == 'rad_graph':
#        return {
#            'data': list(traces[5]),
#            'layout': go.Layout(
#                title='Daily Radiation and Consumption',
#                xaxis={'title': 'Time'},
#                yaxis={'title': 'Radiation [W/m2]', 'range': [0, 1000]},
#                legend=dict(x=-.1, y=1.2)
#            )
#        }


#

#    traces = [trace1, trace2]

    #plt.plot(list(range(0, years + 1)), grid_costs, 'r--', list(range(0, years + 1)), solar_costs, 'bs')

#    return{
#        'data': traces[0],
#        'layout': go.Layout(
#                    title='Cost Estimation',
#                    xaxis={'title': 'Days/Years'},
#                    yaxis={'title': 'Costs [Eur]'},
#                    legend=dict(x=-.1, y=1.2)
#                )
#    }

@app.callback(
    dash.dependencies.Output('cons_graph', 'figure'),
    [dash.dependencies.Input('button_calc', 'n_clicks'),
     dash.dependencies.Input('checkbox_cons_data', 'value'),
     dash.dependencies.Input('season', 'value')])

def change_loc(n_clicks, sel_output, season):

    if season == 'spring':
        start= pd.Timestamp('2018-03-21')
        end= pd.Timestamp('2018-06-20 23:59:00')
    elif season == 'summer':
        start = pd.Timestamp('2018-06-21')
        end = pd.Timestamp('2018-09-20 23:59:00')
    elif season == 'autumn':
        start = pd.Timestamp('2018-09-21')
        end = pd.Timestamp('2018-12-20 23:59:00')
    else:
        start = pd.Timestamp('2018-01-01')
        end = pd.Timestamp('2018-03-20 23:59:00')

#    start = pd.Timestamp('2018-08-01')
 #   end = pd.Timestamp('2018-08-31 23:59:00')
 #   end1 = pd.Timestamp('2018-08-01 23:59:00')
    select = (alpg_data.index >= start) & (alpg_data.index <= end)

    data_range = alpg_data.loc[select]

    traces = []
    for data in sel_output:
        traces.append(go.Scatter(
            x=data_range.index,
            y=data_range[data],
            mode='lines',
            name= data,
            marker={
                'size': 5,
                'line': {'width': 0.5, 'color': 'blue'}
            },
        ))

    return {
        'data': traces,
        'layout': go.Layout(
            title='alpg consumer data',
            xaxis={'title': 'Time'},
            yaxis={'title': 'Power Consumption [W]'},
            legend=dict(x=-.1, y=1.2))

    }

#app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})

if __name__ == '__main__':
    app.run_server(debug = True)