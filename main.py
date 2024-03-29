from dataclasses import dataclass
from decimal import Decimal
import os
import requests
from pprint import pp
import datetime as dt
import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

from typing import Optional


UP_API_KEY = os.getenv("UP_API_KEY")
SAVING_ACCOUNT_NAME = "Utilities"

auth_header = {"Authorization": f"Bearer {UP_API_KEY}"}


@dataclass
class Account:
    id: str
    name: str
    currency: str
    balance: int

@dataclass
class Transaction:
    datetime: dt.datetime
    value: int


found_account: Optional[Account] = None
transactions: list[Transaction] = []

accounts_resp = requests.get(
    "https://api.up.com.au/api/v1/accounts",
    params={"page[size]": 30},
    headers=auth_header,
)

for account in accounts_resp.json()["data"]:
    if (
        SAVING_ACCOUNT_NAME in account["attributes"]["displayName"]
        # and account["attributes"]["ownershipType"] == "INDIVIDUAL"
    ):
        found_account = Account(
            id=account["id"],
            name=account["attributes"]["displayName"],
            balance=int(account["attributes"]["balance"]["valueInBaseUnits"]),
            currency=account["attributes"]["balance"]["currencyCode"],
        )
        transactions.append((Transaction(dt.datetime.now().astimezone(), found_account.balance)))
        break

if found_account is None:
    print(f"Could not find account {SAVING_ACCOUNT_NAME}")
    exit(1)

print("Found account: ", found_account)

transactions_resp = requests.get(
    f"https://api.up.com.au/api/v1/accounts/{found_account.id}/transactions",
    params={
        "page[size]": 100,
        "filter[since]": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(weeks=52)).isoformat(),
    },
    headers=auth_header,
)

while True:
    # pp(transactions_resp.json())
    for transaction in transactions_resp.json()["data"]:
        time = dt.datetime.fromisoformat(transaction["attributes"]["createdAt"])
        value = int(transaction["attributes"]["amount"]["valueInBaseUnits"])
        # value is negative as we are working backwards
        transactions.append(Transaction(time, -value))

    if transactions_resp.json()["links"]["next"] is None:
        break
    
    transactions_resp = requests.get(
        transactions_resp.json()["links"]["next"],
        headers=auth_header,
    )

# pp(transactions)
df = pd.DataFrame(transactions)
df["balance"] = df["value"].cumsum() / 100
print(df)

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    dcc.Dropdown(["sike"], 'Canada', id='dropdown-selection'),
    dcc.Graph(id='graph-content')
])

@callback(
    Output('graph-content', 'figure'),
    Input('dropdown-selection', 'value')
)
def update_graph(value):
    return px.line(df, x='datetime', y='balance', line_shape="hv")

if __name__ == '__main__':
    app.run(debug=True)