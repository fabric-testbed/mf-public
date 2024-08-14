
# Use flask for simple server for extra pages for public-metrics site.
import flask
from flask import Flask, render_template, redirect, request, session, make_response, url_for, jsonify

# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)


####################
#     ROUTES       #
####################


@app.route('/welcome')
def welcome():
    return render_template("welcome.html")


@app.route('/extra')
def extra():
    print("extra!")
    return render_template("welcome2.html")


if __name__ == '__main__':
    print("!!!!!!!!!!!!Running as main!!!!!!!!!!!!!")
    app_flask.run(debug=True)