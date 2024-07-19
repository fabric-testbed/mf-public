
# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import flask
from flask import Flask, render_template, redirect, request, session, make_response, url_for, jsonify
from flask_session import Session
from flask_csv import send_csv

from late_app import late_app

import os
import sys
import base64
import jwt
import gzip

import requests
#import weather_queries.py
import yaml

# Flask constructor takes the name of 
# current module (__name__) as argument.
app = Flask(__name__)


#app_flask.secret_key = (os.getenv('FLASK_APP_SECRET_KEY'))

#app.config["SESSION_PERMANENT"] = False
#app.config["SESSION_TYPE"] = "filesystem"


#Session(app)

####################
#     ROUTES       #
####################

#@app.route('/latency')
#def dash_app():
#    print(dir(late_app))
#    return late_app.index()


@app.route('/welcome')
def welcome():
    return render_template("welcome.html")

@app.route('/weather')
def get_weather():

    weather_queries = read_weather_queries()

    ret_val = []
    csv = "siteA,siteB,bytes"
    for link in weather_queries["links"]:
        print(link["query"])
        print(link["title"])
        sites = link['title'].split(' - ')
        b = get_link_weather(link["query"])
        ret_val.append( { "siteA":sites[0], "siteB":sites[1], "sites": link['title'], 'bytes':(b)} )
        #print(f"{link['title']} {b} bytes")

        #csv += f"{sites[0]},{sites[1]},{b}" + '\n'

    #return send_csv(ret_val, "weather.csv", ["siteA", "siteB", "sites", "bytes"] )  
    return jsonify(ret_val)


def read_weather_queries():
    with open("weather_queries.yml", "r") as stream:
        try:
            queries = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(f"Failed to read weather queries yaml: {exc}")
        print(queries)
        return queries


def get_link_weather(link_query):

    basic_url = "http://public-metrics_mimir:8080/prometheus/api/v1/query"
    org_headers = {'X-Scope-OrgID':'public-data'}
    query_params = {"query":link_query}

    r = requests.get( f"{basic_url}",headers=org_headers, params=query_params )
    if r.status_code != 200:
        print("get_link_weather failed")
        return 0
    try:
        results = r.json()
        print(results)
        #bytes_per_second = results['data']['result'][0]["value"][1]
        bytes_per_second = results['data']['result'][0]["value"][1]

        return bytes_per_second
    except:
        print("Failed to get results")
    return 0


if __name__ == '__main__':
    print("!!!!!!!!!!!!Running as main!!!!!!!!!!!!!")
    app_flask.run(debug=True)

