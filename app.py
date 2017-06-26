#!/usr/bin/env python

from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
import requests
from xml.dom import minidom


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
    yql_query = makeYqlQuery(req)
    print (yql_query)
    if yql_query is None:
        return {}
    query = urlencode({'search': yql_query})
    wiki_query = {'action':'opensearch', 'format': 'xml',
                  'namespace': '0', 'limit': '1', 'redirects':'resolve', 'warningsaserror':'1', 'utf8': '1'}
    yql_url = baseurl + urlencode(wiki_query) + "&" + query
    result = urlopen(yql_url).read().decode("utf8")
    search_term = get_title(result)
    return search_term

def get_answer(title):
    baseurl = "https://en.wikipedia.org/w/api.php?"

    query = title.strip().replace(" ", "+")
    wiki_query = {'action':'query', 'format': 'xml', 'prop': 'extracts',
                  'list': '', 'redirects': '1', 'exintro': '', 'explaintext': ''}
    yql_url = baseurl + urlencode(wiki_query) + "&titles=" + query
    print ("ANSWER URL = " + yql_url)
    result = requests.get(yql_url).text
    print ("RESULT:\n" + result)
    res = makeWebhookResult(result)
    return res

def get_title(data):
    xmldoc = minidom.parseString(data)
    url = xmldoc.getElementsByTagName('Text')[0].childNodes[0].data
    title = url
    return title

def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    query = parameters.get("phrase")
    if query is None:
        return None
    print ('QUERY' + query)
    return query


def makeWebhookResult(data):
    xmldoc = minidom.parseString(data)
    extract = xmldoc.getElementsByTagName('extract')[0].childNodes[0].data

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
