import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import app2, app3

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

home_page_layout= html.Div([
    dcc.Link('Go to Energy System Simulator', href='/apps/app1'),
    html.Br(),
    dcc.Link('Load Profile Generator', href='/apps/app2'),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/':
        return home_page_layout
    elif pathname == '/apps/app1':
        return app2.layout
    elif pathname == '/apps/app2':
        return app3.layout
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(debug=False)