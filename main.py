import os
import json
from datetime import date

import requests

EODMETRICS_QID = os.environ["EODMETRICS_QID"]
EODMETRICS_EMAIL = os.environ["EODMETRICS_EMAIL"]
EODMETRICS_PASSWORD = os.environ["EODMETRICS_PASSWORD"]
EODMETRICS_USER_AGENT = os.environ["EODMETRICS_USER_AGENT"]


def get_iv_data():
    # login to get more data
    s = requests.Session()
    s.headers.update({"User-Agent": ""})

    url = "https://eodmetrics.com/login"
    res = s.get(url)
    assert res.status_code == 200, res.text

    url = "https://eodmetrics.com/service/login"
    csrf = s.cookies["c"]
    headers = {"X-Requested-By-EOD": "1"}
    data = {"email": EODMETRICS_EMAIL, "password": EODMETRICS_PASSWORD, "r": str(csrf)}
    res = s.post(url, data=data, headers=headers)
    assert res.status_code == 200, res.text

    url = "https://eodmetrics.com/service/query-results?qid=" + EODMETRICS_QID
    res = s.get(url)
    assert res.status_code == 200, res.text

    required_idx = []
    required = ["Industry", "Sector"]
    data = res.json()
    cols = data["columnNames"]
    for i, c in enumerate(cols):
        if c in required:
            required_idx.append(i)

    res = []
    records = data["records"]
    for r in records:
        if any(r[i] is None for i in required_idx):
            continue

        res.append({k: v for k, v in zip(cols, r)})

    return res


def create_json_file(filename):
    data = get_iv_data()
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def md_table(d):
    """
    Loop through a list of dicts and return a markdown table as a multi-line string

    https://github.com/codazoda/tomark/blob/master/tomark/tomark.py
    """
    markdowntable = ""
    # Make a string of all the keys in the first dict with pipes before after and between each key
    markdownheader = '| ' + ' | '.join(map(str, d[0].keys())) + ' |'
    # Make a header separator line with dashes instead of key names
    markdownheaderseparator = '|-----' * len(d[0].keys()) + '|'
    # Add the header row and separator to the table
    markdowntable += markdownheader + '\n'
    markdowntable += markdownheaderseparator + '\n'
    # Loop through the list of dictionaries outputting the rows
    for row in d:
        markdownrow = ""
        for key, col in row.items():
            markdownrow += '| ' + str(col) + ' '
        markdowntable += markdownrow + '|' + '\n'
    return markdowntable


def create_readme(src):
    with open("README.tmpl.md", "r") as f:
        tmpl = f.read()

    with open(src, "rb") as f:
        data = json.load(f)
    
    # Update tickers to include a url to finviz
    for d in data:
        t = d["Ticker"]
        d["Ticker"] = f"[{t}](https://finviz.com/quote.ashx?t={t}&p=w)"
        del d["Market Cap"]
        del d["Volume"]

    table = md_table(data)
    s = tmpl.format(table=table, date=date.today().isoformat())
    with open("README.md", "w") as f:
        f.write(s)


if __name__ == "__main__":
    filename = 'data.json'
    create_json_file(filename)
    create_readme(src=filename)
