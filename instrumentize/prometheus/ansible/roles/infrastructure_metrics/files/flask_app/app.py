# Importing flask module in the project is mandatory
# An object of Flask class is our WSGI application.
import flask
from flask import Flask, render_template, redirect, request, session, make_response, url_for
from flask_session import Session

from datetime import timedelta

import os
import sys
import base64
import jwt
import gzip

import fabric_auth


# Flask constructor takes the name of
# current module (__name__) as argument.
app = Flask(__name__)

app.secret_key = (os.getenv('FLASK_APP_SECRET_KEY'))

app.config["SESSION_PERMANENT"] = False   # Session goes away when browser is closed
#app.config["SESSION_PERMANENT"] = True  # Session goes away when permanent session lifetime expires
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=600) # does this depend on session permanent being True ??
app.config["SESSION_TYPE"] = "filesystem"

Session(app)

####################
#     ROUTES       #
####################

@app.route('/welcome')
def welcome():
  status = ""
  jwt_cookie = request.cookies.get('fabric-service')
  if not jwt_cookie:
      cilogon_status = False
      status = "Failed to get fabric JWT Cookie"
  else:
      cilogon_status = True
      status = "Have fabric JWT cookie"

  existing_uuid = session.get('uuid')
  existing_name = session.get('name')
  if existing_uuid:
    fabric_user_session = True
    status = f"{status}  Session with {existing_name} as  {existing_uuid}"
  else:
    status = f"{status} No Session Found"
    fabric_user_session = False


  err_msg = request.args.get('err_msg')
############## set welome to show neeeded buttons
  return render_template("welcome.html", user_status=status, err_msg=err_msg, cilogon_status=cilogon_status, fabric_user_session=fabric_user_session, user_name=existing_name)


#@app.route('/show_headers')
#def show_headers():
#    print("show headers")
#    print(request.headers)
#    for header in request.headers:
#      print(header)
#    return 'OK', 200



#@app.route('/cookie_check')
#def cookie_check():
#
#  print("checking cookie to see if cookie exists")
#  #print(request.headers)
#  jwt_cookie = request.cookies.get('fabric-service')
#  if not jwt_cookie:
#      return "Failed to get JWT Cookie"
#  else:
#      return "Got cookie"


# @app.route('/login')
# def login():
#   print("!!!!!!flask login method is no longer used!!!!!!!")
#   # Checks to see if user is a valid fabric user
#   # If true, then session is confirmed or created & user is redirected to grafana
#   # Check if already logged on
#   existing_uuid = session.get('uuid')
#   if existing_uuid:
#       print(f'logged in already as {existing_uuid}')
#       return "OK", 200
#   else:
#       print("No session found")

#   # Check if vouch cookie exists
#   print("loggin in, checking cookie to get api_user")
#   #print(request.headers)
#   jwt_cookie = request.cookies.get('fabric-service')
#   if not jwt_cookie:
#       print("JWT Cookie not found.")
#       return "Failed to get JWT Cookie", 401
#   print(jwt_cookie)
#   # api_user = fabric_auth.get_api_user(request)

#   # Check if user is a member of fabric
#   api_user = fabric_auth.auth_user_by_cookie(jwt_cookie)
#   if not api_user:
#       print("failed to get api user by cookie")
#       return "Failed to get api user by cookie", 401

#   #print("----------------flask app login----------")
#   #print(api_user)
#   #print("++++++++++++")

# #  if session.get('uuid'):
# #    #already logged in
# #    uuid = session.get('uuid')
# #    print(f'Already logged in as {uuid}')
# #  else:

#   session['uuid'] = api_user.whoami['uuid']
#   uuid = session['uuid']
# #  print(f'uuid is {uuid}')
#   session['projects'] = len(api_user.projects)

#   print("------Session----------")
#   print(vars(session))
#   print("=====================")

#   if not uuid:
#     return f'Failed to logon {api_user.uuid}', 401
#   print(f"Logged on as {uuid}" )

#   return redirect("/grafana"), 303


@app.route('/set_fabric_user_session')
def set_fabric_user_session():
  # This will check if the user session has been setup
  # If true returns OK, 200
  # If false, session creation is attempted
  #    if session created returns OK, 200
  #    if session cannot be created returns Fail reason, 401


  print("set-fabric-user-session")

  #--check if already logged on
  existing_uuid = session.get('uuid')
  if existing_uuid:
      print(f'logged in already as {existing_uuid}')
      return "OK", 200
  else:
      print("No session found")

  print("loggin in, checking cookie to get api_user")
  #print(request.headers)

  #--check if fabric-serice cookie is available
  jwt_cookie = request.cookies.get('fabric-service')
  if not jwt_cookie:
      print("JWT Cookie not found.")
      #return redirect(url_for('welcome', errmsg="Failed to find CiLogon information. Have you logged on?")), 303
      return "Failed to get JWT Cookie", 401

  #print(jwt_cookie)

  #--check if user is a fabric member
  api_user = fabric_auth.auth_user_by_cookie(jwt_cookie)
  if not api_user:
      print("failed to get api user by cookie")
      return redirect(url_for('welcome', err_msg="Failed to get Fabric information. Are you a Fabric member?")), 303
      #return "Failed to get api user by cookie", 401


  print("----------------flask app login----------")
  print(api_user)
  print("++++++++++++")

  #--Now create the new session
  if api_user:
    session['uuid'] = api_user.whoami['uuid']
    session['active'] = api_user.whoami['active']
    session['email'] = api_user.whoami['email']
    session['name'] = api_user.whoami['name']
    session['enrolled'] = api_user.whoami['enrolled']
    session['vouch_expiry'] = api_user.whoami['vouch_expiry']


    #Unneded info for now. will need to log in as research user
  #  session['affiliation'] = api_user.fabric_person['']
  #  session['bastion_login'] = api_user.fabric_person['']
  #  session['cilogon_email'] = api_user.fabric_person['']
  #  session['email_addresses'] = api_user.fabric_person['']
  #  session['name'] = api_user.fabric_person['']
  #  session[''] = api_user.fabric_person['']
  #  session[''] = api_user.fabric_person['']



    #session[''] = api_user.whoami['']

    #session['projects'] = len(api_user.projects)

    print("------Session----------")
    print(vars(session))
    print("=====================")

    uuid = session['uuid']
    print(f'uuid is {uuid}')
    if not uuid:
      #return redirect(url_for('welcome', errmsg="Session failed to set")), 303
      return f'Failed to logon {api_user.uuid}', 401

  print(f"Logged on as {uuid}" )

  #return 'OK', 200
  return redirect("/grafana"), 303


@app.route('/check_fabric_user_session')
def check_fabric_user_session():
    # Validates that the user fabric user session has been set
    # this means that the user has been verified by uis
    uuid = session.get('uuid')
    if uuid:
        print(f'User is logged in as {uuid}')
        print(session)
        return uuid, 200
    else:
        print("session not found")
        return "No session found",  401


@app.route('/clear_fabric_user_session')
def clear_fabric_user_session():
    if session:
        print("session exists")
    else:
        print("no session to logout of")
    if 'uuid' in session:
        uuid = session['uuid']
    else:
        uuid = "No uuid found."

    session.clear()
    print("Cleared Session (clear)")
    print(session)
    print(uuid)
    return redirect("/"), 303

@app.route('/clear_fabric_service_cookie')
def clear_fabric_service_cookie():
  resp = flask.make_response()

  resp.set_cookie('fabric-service', '', expires=0)
  resp.headers['location'] = "/"
  return resp


@app.route('/logout')
def logout():
    if session:
        print("session exists")
    else:
        print("no session to logout of")
#TODO add session expire
    if 'uuid' in session:
        uuid = session['uuid']
    else:
        uuid = "No uuid found."

    session.clear()
    print("Cleared sessin (logout)")
    print(session)
    print(uuid)
    return redirect("/"), 303



# main driver function
if __name__ == '__main__':

    print("***********************APP MAIN STARTING port 6666*****************")
    # run() method of Flask class runs the application 
    # on the local development server.
    #app.run()
    app.run_server(debug=True, host="0.0.0.0", port=6666)
