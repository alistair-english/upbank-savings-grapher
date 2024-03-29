from dataclasses import dataclass
import os
import requests
import datetime as dt
import pandas as pd
import pandas as pd

from typing import Optional, Iterator

UP_API_KEY = os.getenv("UP_API_KEY")
auth_header = {"Authorization": f"Bearer {UP_API_KEY}"}


@dataclass
class Transaction:
    datetime: dt.datetime
    value: int


def _do_paginated_json_request(url: str, params: Optional[dict] = None, page_size: int = 30) -> Iterator[dict]:
    if params is None:
        params = {}

    params["page[size]"] = page_size

    resp = requests.get(url, params=params, headers=auth_header)
    while True:
        yield resp.json()

        if resp.json()["links"]["next"] is None:
            break

        resp = requests.get(resp.json()["links"]["next"], params=params, headers=auth_header)


def get_accounts() -> dict[str, str]:
    """returns name: id"""

    accounts: dict[str, str] = {}
    for page in _do_paginated_json_request("https://api.up.com.au/api/v1/accounts", params={"filter[accountType]": "SAVER"}):
        for account in page["data"]:
            name = account["attributes"]["displayName"]
            if account["attributes"]["ownershipType"] == "JOINT":
                name += " (2UP)"
            accounts[name] = account["id"]
    return accounts


def get_balance_df(account_id: str, lookback: dt.timedelta) -> pd.DataFrame:
    """Episode 4: attack of the dataframe"""

    transactions: list[Transaction] = []
    account_resp = requests.get(f"https://api.up.com.au/api/v1/accounts/{account_id}", headers=auth_header).json()

    transactions.append(
        Transaction(dt.datetime.now().astimezone(), account_resp["data"]["attributes"]["balance"]["valueInBaseUnits"])
    )

    lookback_dt = dt.datetime.now(dt.timezone.utc) - lookback
    for page in _do_paginated_json_request(
        f"https://api.up.com.au/api/v1/accounts/{account_id}/transactions",
        params={"filter[since]": lookback_dt.isoformat()},
        page_size=100,
    ):
        for transaction in page["data"]:
            time = dt.datetime.fromisoformat(transaction["attributes"]["createdAt"])
            value = int(transaction["attributes"]["amount"]["valueInBaseUnits"])
            # value is negative as we are working backwards
            transactions.append(Transaction(time, -value))

    df = pd.DataFrame(transactions)
    df["balance"] = df["value"].cumsum() / 100

    return df
