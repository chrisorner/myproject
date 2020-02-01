import dash
from flask import Flask


external_stylesheets = ['https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css']

server = Flask(__name__)
app = dash.Dash(__name__, server=server, external_stylesheets=external_stylesheets)
app.title = 'Energy Systems Simulator'
#app = dash.Dash(__name__)
#server = app.server
app.config.suppress_callback_exceptions = True