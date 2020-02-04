import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

from app import app
from apps import app2, app3

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

first_card = dbc.Card(
        dbc.CardBody(
            [
                html.H5("Load Profile", className="card-title"),
                html.P("This card has some text content, but not much else"),
                dbc.Button("Go somewhere", color="primary"),
            ]
        )
    )

second_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("Simulation", className="card-title"),
            html.P(
                "This card also has some text content and not much else, but "
                "it is twice as wide as the first card."
            ),
            dbc.Button("Go somewhere", color="primary"),
        ]
    )
)

third_card = dbc.Card(
    dbc.CardBody(
        [
            html.H5("White Paper", className="card-title"),
            html.P(
                "This card also has some text content and not much else, but "
                "it is twice as wide as the first card."
            ),
            dbc.Button("Go somewhere", color="primary"),
        ]
    )
)

cards = dbc.Row([dbc.Col(first_card, width=4), dbc.Col(second_card, width=4), dbc.Col(third_card, width=4)])

home_page_layout = dbc.Container([

    dbc.Nav(
        [
            dbc.NavItem(dbc.NavLink('Home Page', active=True, href='/', style= {'color': 'white'})),
            dbc.NavItem(dbc.NavLink('Load Configuration',  href='/apps/app1', style= {'color': 'white'})),
            dbc.NavItem(dbc.NavLink('Simulation', href='/apps/app2', style= {'color': 'white'})),

        ],
        className= 'navbar navbar-expand-lg navbar-dark bg-dark fixed-top'
    ),

    html.Div([
        html.Div([
            html.Div([
                html.Img(src= 'http://placehold.it/900x400', className= 'img-fluid rounded mb-4 mb-lg-0')
            ], className='col-lg-7'),
            html.Div([
                html.H1('Business Name or Tagline', className = 'font-weight-light'),
                html.P('This is a template that is great for small businesses. It does not have too much fancy flare to it, but it makes a great use of the standard Bootstrap core components. Feel free to use this template for any project you want'),
            ], className='col-lg-5')
        ],className= 'row align-items-center my-5')
    ]),

    dbc.Row(cards)

])





@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return home_page_layout
    elif pathname == '/apps/app1':
        return app3.layout
    elif pathname == '/apps/app2':
        return app2.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=False)