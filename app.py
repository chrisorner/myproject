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

from calculations import Solar, Battery, Consumer, Costs

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
    type = db.Column(db.String(30))
    efficiency = db.Column(db.Float)

    def __init__(self, id, type, efficiency):
        self.id = id
        self.type = type
        self.efficiency = efficiency


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
                    html.Label('Number of Cells', id='N_cells_label'),
                    dcc.Input(id='N_cells', value='150', type='text', className='form-control')
                ], className='col-4 offset-md-1'),
                html.Div([
                    html.Label('Battery Capacity [kWh]', id='cap_label'),
                    dcc.Input(id='capacity', value='10', type='text', className='form-control')
                ], className='col-4 offset-md-1')
            ], className='row my-4'),
            html.Div([
                html.H4('Data Sheet Solar Panel', className='col-12'),
                html.Div([
                    html.Label('Short Circuit Current [A]', id='Isc_label'),
                    dcc.Input(id='Isc', value='6', type='text', className='form-control'),
                ], className='col-4 offset-md-1'),
                html.Div([
                    html.Label('Open Circuit Voltage [V]', id='Uoc_label'),
                    dcc.Input(id='Uoc', value='0.67', type='text', className='form-control')
                ], className='col-4 offset-md-1')
            ], className='row my-4'),
            html.Div([
                html.H4('Cost Data', className='col-12'),
                html.Div([
                    html.Label('Battery [EUR/kWh]', id='cost_label'),
                    dcc.Input(id='cost_bat', value='1000', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Grid supply [EUR/kWh]', id='cost_label2'),
                    dcc.Input(id='cost_kwh', value='0.3', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Solar Panels [EUR/kWp]', id='cost_label3'),
                    dcc.Input(id='cost_wp', value='600', type='text', className='form-control')
                ], className='col-3'),
                html.Div([
                    html.Label('Number of Days to View', id='days_label'),
                    dcc.Input(id='days', value='2', type='number', className='form-control')
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
            html.H4('Tune Solar Radiation', className='col-12'),
            html.Div([
                html.Div([html.Label('Location', id='location_label'),
                          dcc.Input(id='location', type='text', className='form-control')
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
    return (rad_data7d[0], rad_data7d[1])


@app.callback(
    dash.dependencies.Output('placeholder', 'children'),
    [dash.dependencies.Input('confirm', 'submit_n_clicks')],
    [dash.dependencies.State('typeSP', 'value'),
     dash.dependencies.State('efficiency', 'value')])
# Add new solar cell to database
def update_db(submit_n_clicks, typeSP, effic):
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
     dash.dependencies.Input('button_calc', 'n_clicks'),
     dash.dependencies.Input('output-provider2', 'value')],
    [dash.dependencies.State('cost_bat', 'value'),
     dash.dependencies.State('capacity', 'value'),
     dash.dependencies.State('days', 'value'),
     dash.dependencies.State('cost_kwh', 'value'),
     dash.dependencies.State('cost_wp', 'value'),
     dash.dependencies.State('Isc', 'value'),
     dash.dependencies.State('Uoc', 'value'),
     dash.dependencies.State('N_cells', 'value'),
     dash.dependencies.State('editable-table', 'data')],
)
def update_cost(sel_graph, sel_calc, n_clicks, loc_rad, cost_bat, cap_bat, days_input, cost_kwh, cost_wp, Isc, Uoc,
                n_cells, rows):
    ##Update everything with input data
    Temp = 298  # Ambient Temperature
    days_input = float(days_input)

    if sel_calc == 'forec':
        rad_val = loc_rad[1]
        rad_time = [x / 60 for x in loc_rad[0]]
    else:
        df = pd.read_csv('hist_irrad.csv')
        # print(df['PeriodEnd'].head())
        last_year = '2018'
        rad_val = []

        for num in range(len(df['PeriodEnd'])):
            if last_year in df['PeriodEnd'].iloc[num]:
                rad_val.append(df['Ghi'].iloc[num])

        rad_time = np.linspace(1, 8760, 8760)
        rad_time = rad_time[0:2000]
        rad_val = rad_val[0:2000]

    t_len = len(rad_val)
    d_len = int(t_len / 24)

    # if days_input > 5 and sel_graph=='power_graph':
    #    days_input = 5

    dff = pd.DataFrame(rows)
    # dff_conc=pd.concat([dff]*d_ges)
    df_num = pd.to_numeric(dff['Energy Consumption [kWh]'])
    df_num = df_num.as_matrix()

    grid_costs = []
    solar_costs = []
    e_batt = []
    p_sol = []
    e_grid = []
    p_cons = []

    if n_clicks:
        cost = Costs(rad_val)
        sol = Solar(rad_val)
        n_cells = float(n_cells)
        # Sol.calc_Pmpp(Ncells,Temp,rad_ampl,rad_width,Isc,Uoc)
        sol.calc_Pmpp(n_cells, Temp, rad_val, Isc, Uoc)

        p, p_sol = sol.get_P_Pmpp()

        sol_power = sol.get_Pmax()
        cost.calc_costs(n_cells, Temp, rad_val, days_input, cost_kwh, cap_bat, cost_bat, sol_power, cost_wp, Isc, Uoc,
                        df_num)
        grid_costs = cost.total_costs
        solar_costs = cost.total_costs_sol

        bat = Battery(rad_val)
        bat.calc_SOC(n_cells, Temp, rad_val, cap_bat, Isc, Uoc, df_num)
        e_batt = bat.get_stored_energy()
        e_grid = bat.get_from_grid()

        cons = Consumer(rad_val)
        cons.calc_power(n_cells, Temp, rad_val, Isc, Uoc, df_num)
        p_cons = cons.get_power()

    # Create Graphs
    trace1 = (go.Scatter(
        x=np.arange(0, d_len + 1, 1),
        y=grid_costs,
        name='Without Solar Panels',
    ))

    trace2 = (go.Scatter(
        x=np.arange(0, d_len + 1, 1),
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
        x=rad_time,
        y=rad_val,
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
                xaxis={'title': 'Days'},
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
