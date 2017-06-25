#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request


import json
import os
import re

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    title = search(req)
    res = get_answer(title)

    res = json.dumps(res, indent=4)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def search(req):
    if req.get("result").get("action") != "WikipediaSearch":
        return {}
    baseurl = "https://en.wikipedia.org/w/api.php?"
    action = "action=opensearch&format=json&search="
    wiki_rules = "&namespace=0&limit=1&redirects=resolve&warningsaserror=1"
    yql_query = makeYqlQuery(req)
    print (yql_query)
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({action: yql_query}) + wiki_rules
    print ("yql_url: " + yql_url)
    result = urlopen(yql_url).read().decode("utf8")

    search_term = get_title(result)
    return search_term

def get_answer(title):
    baseurl = "https://en.wikipedia.org/w/api.php?"
    action = "action=query&format=json&prop=extracts&list=&titles="
    wiki_rules = "f&redirects=1&exintro=1&explaintext=1"
    yql_query = makeYqlQuery(title)
    if yql_query is None:
        return {}
    yql_url = baseurl + action + urlencode(yql_query) + wiki_rules
    result = urlopen(yql_url).read().decode("utf8")
    print ("RESULT:\n" + result)
    res = makeWebhookResult(result)
    return res

def get_title(data):
    url = re.findall(r'https:(.*?)"', data)
    title = url.rsplit('/', 1)[-1]
    return title

def makeYqlQuery(req):
    result = req.get("result")
    query = result.get("resolvedQuery")
    if query is None:
        return None

    return query


def makeWebhookResult(data):
    pages_dict = data["query"]["pages"]
    if pages_dict is None:
        return {}
    page_id = next(iter(pages_dict))
    if page_id is None:
        return {}
    extract = data["query"]["pages"][page_id]["extract"]
    if extract is None:
        return {}

    print(json.dumps(extract, indent=4))

    speech = extract

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-wikipedia-webhook"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')
