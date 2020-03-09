import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from flask_mail import Mail, Message

from app import app, server
from apps import app2_noDB, app3

server.config['MAIL_SERVER']='smtp.gmail.com'
server.config['MAIL_PORT'] = 465
server.config['MAIL_USERNAME'] = 'christianorner8@gmail.com'
server.config['MAIL_PASSWORD'] = 'oo4+hdafnr'
server.config['MAIL_USE_TLS'] = False
server.config['MAIL_USE_SSL'] = True

mail = Mail(server)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

first_card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Load Profile", className="card-title"),
                html.P("Create a individual load profile"
                       ""),
                dbc.Button("Create Load Profile", color="primary"),
            ]
        )
    )

second_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Simulation", className="card-title"),
            html.P(
                "Simulate solar panels and batteries to predict your energy costs"
            ),
            dbc.Button("Simulate System", color="primary"),
        ]
    ), style= {'height':'50'}
)

third_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("White Paper", className="card-title"),
            html.P("If you want to know more, please download our White Paper"),
            dbc.Button("Download", id = "open_email", color="primary"),
        ]
    )
)

cards = dbc.Row([dbc.Col(first_card, width=4), dbc.Col(second_card, width=4), dbc.Col(third_card, width=4)])

modal = html.Div(
            [
                dbc.Modal(
                    [
                        dbc.ModalHeader("Request White Paper"),
                        dbc.ModalBody("Please enter your email address and we will send you the link to download the White Paper"),
                        dbc.Input(id="email_input", placeholder="Your email address", type="text"),
                        dbc.ModalFooter(
                            dbc.Button("Send", id="close_email", className="ml-auto")
                        ),
                    ],
                    id="modal",
                ),
            ]
        )

home_page_layout = dbc.Container([

    dbc.Nav(
        [
            dbc.NavItem(dbc.NavLink('Home Page', active=True, href='/', style= {'color': 'white'})),
            dbc.NavItem(dbc.NavLink('Load Configuration',  href='/apps/app1', style= {'color': 'white'})),
            dbc.NavItem(dbc.NavLink('Simulation', href='/apps/app2_noDB', style= {'color': 'white'})),

        ],
        className= 'navbar navbar-expand-lg navbar-dark bg-dark fixed-top'
    ),

    html.Div([
        html.Div([
            html.H1('Turn leads into customers by creating transparent and detailed offers '
                    'for solar energy systems within minutes', className = 'display-4')
        ], className='jumbotron', style = {'background':'transparent'}),
        html.Div([
            html.H1('Digital Sales of Energy Technology', className = 'h1 mb-4'),
            html.H5('Reduce time and costs for pre-sales consultation processes', className='mb-5'),
        ], className='col-lg-12 text-center')
    ]),

    html.Div([
        html.Div([

            html.H5('Load profiles', className='text-center'),
            html.Img(src='images/statistical-chart.png', width='50', height='50', className='rounded mx-auto d-block'),
            html.P('Create energy consumption profiles based on statistical data and stochastic processes')

        ], className='col-3 p-4 text-justify'),

        html.Div([
            html.H5('Optimum energy system', className='text-center'),
            html.Img(src='images/algorithm.png', width='50', height='50', className='rounded mx-auto d-block'),
            html.P('Our algorithms identify the'
                   ' optimum size of an energy system and maximize self-consumption')

        ], className='col-3 p-4 text-justify'),

        html.Div([
            html.H5('Create individual offers', className='text-center'),
            html.Img(src='images/offer.png', width='50', height='50', className='rounded mx-auto d-block'),
            html.P('Create "push" offers with individual system solutions')

        ], className='col-3 p-4 text-justify'),

        html.Div([
            html.H5('Full transparency', className='text-center'),
            html.Img(src='images/transparency.png', width='50', height='50', className='rounded mx-auto d-block'),
            html.P('Allow your customers to compare different energy systems regarding return of investment, '
                   'degree of autarky and reduced emissions')

        ], className='col-3 p-4 text-justify'),

    ], className='row mb-5'),

    dbc.Row(cards, style={'display':'flex', 'flex-wrap':'wrap'}),
    dbc.Row(modal),

     html.Footer([
        html.Div([
            html.Div([
                html.H5('Get in Touch'),
                html.Ul([
                    html.Li('christianorner8@gmail.com'),
                    html.Li('+4917664908433')
                ], className='list-unstyled text-small'),
                html.Div([
                    html.A(href='https://www.linkedin.com/in/christian-orner-7aa17880/', children=[
                        html.Img(src='https://prismic-io.s3.amazonaws.com/plotly%2Fb3ffa9a8-1af6-4bb4-8e6a-8161d9dba450_icon_linkedin.svg')
                    ])

                ]),

                html.Div(id='dummy_div', style={'display': 'none'}),
                html.Div(id='email_address', style={'display': 'none'}),

            ], className='col-6 col-md')

        ], className='row')
    ], className= 'pt-4 my-md-5 pt-md-5 border-top'),



])





@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return home_page_layout
    elif pathname == '/apps/app1':
        return app3.layout
    elif pathname == '/apps/app2_noDB':
        return app2_noDB.layout
    else:
        return '404'

@app.callback(Output('dummy_div', 'children'),
              [Input('close_email', 'n_clicks')],
              [State('email_input', 'value')])
def white_paper(n_clicks, email):
    if n_clicks != None:



        msg = Message("White Paper - Digital Sales of Energy Technology",
                    sender="christianorner8@gmail.com",
                    recipients=[email],
                    body = "Thank you for your interest in our white paper. Download the paper here:"
                           "https://www.pythonanywhere.com/user/chrisorn/files/home/chrisorn/myproject/myproject/assets/files/WhitePaper_EnergySales.pdf")

        mail.send(msg)


@app.callback(
    Output("modal", "is_open"),
    [Input("open_email", "n_clicks"), Input("close_email", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

if __name__ == '__main__':
    app.run_server(debug=True)