import datetime as dt

from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px

import up_interface as up

app = Dash(__name__)

ACCOUNTS = up.get_accounts()
account_names = sorted(ACCOUNTS.keys(), key=lambda s: s.encode("ascii", "ignore")) # encoding with ascii to drop emojis

app.layout = html.Div(
    [
        html.H1(children="Account Grapher", style={"textAlign": "center"}),
        dcc.Dropdown(account_names, account_names[0], id="dropdown-selection"),
        dcc.Graph(id="graph-content"),
    ]
)


@callback(Output("graph-content", "figure"), Input("dropdown-selection", "value"))
def update_graph(value):
    account_id = ACCOUNTS[value]
    df = up.get_balance_df(account_id, lookback=dt.timedelta(weeks=104))
    return px.line(df, x="datetime", y="balance", line_shape="vh")


if __name__ == "__main__":
    app.run()
