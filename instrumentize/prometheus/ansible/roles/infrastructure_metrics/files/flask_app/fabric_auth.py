import base64
import gzip
import hashlib
import os
import uuid
from datetime import datetime, timedelta, timezone

import jwt
import requests

import sys

class ApiUser():
    uuid = ""
    name = ""
    projects = []
    fabric_roles = []
    access_expires = None
    whoami = {}
    fab_person = {}

    def __str__(self):
        return f"{self.whoami}  {self.fab_person}"
        #return( f"uuid: {self.uuid} name: {self.name} ")# proj: {self.projects} roles: {self.fabric_roles} exp: {self.access_expires}" )


def get_api_user(request) -> ApiUser:
    """
    Read user info from fabric-service cookie found in request
    Return user info or None if error
    """
    api_user = ApiUser()
    api_user.uuid= 'Uknown_UUID'
    api_user.name='Unknown_NAME'
    api_user.projects=[]
    api_user.fabric_roles=[]

    cookie = request.cookies.get("fabric-service")

    now = datetime.now(timezone.utc)

    if cookie:
        oidc_sub = get_oidc_sub_from_cookie(cookie=cookie)
        if oidc_sub:
            api_user = auth_user_by_cookie(cookie=cookie)
            api_user.access_expires = now + timedelta(minutes=int(os.getenv('API_USER_REFRESH_CHECK_MINUTES')))
        else:
            print("Failed to get oidc_sub")
            return None
    else:
        print("No cookie provided.")
        return None
    print( '-----api_user-----')
    print( api_user.__str__() )
    print( '=====api_user=====')
    return api_user

def get_oidc_sub_from_cookie(cookie: str) -> str | None:
    try:
        # get base64 encoded gzipped vouch JWT
        base64_encoded_gzip_vouch_jwt = cookie
        # decode base64
        encoded_gzip_vouch_jwt_bytes = base64.urlsafe_b64decode(base64_encoded_gzip_vouch_jwt)
        # gzip decompress
        vouch_jwt_bytes = gzip.decompress(encoded_gzip_vouch_jwt_bytes)
        # decode bytes
        vouch_jwt = vouch_jwt_bytes.decode('utf-8')
        # decode JWT using Vouch Proxy secret key (do not verify aud)
        vouch_json = jwt.decode(
            jwt=vouch_jwt,
            key=os.getenv('VOUCH_JWT_SECRET'),
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        print("-----vouch json-----")
        print(vouch_json)
        print("=====vouch json=====")
        # vouch_jwt holder for decoded JWT
        oidc_sub = vouch_json.get('CustomClaims').get('sub')
        return oidc_sub
    except Exception as exc:
        print(exc)
        return None


def auth_user_by_cookie(cookie: str) -> ApiUser:
    """
    Use cookie to authorize user
    - get user uuid from core-api using cookie
    - with user uuid populate user information from core-api /people/{uuid}?as_self=true
    """
    #api_user = ApiUser(uuid=os.getenv('API_USER_ANON_UUID'), projects=[], fabric_roles=[])
    api_user = ApiUser()
    #api_user.uuid= 'Unknown UUID'
    #api_user.name='Unknown NAME'
    #api_user.projects=[]
    #api_user.fabric_roles=[]

    s = requests.Session()
    try:
        s.cookies.set('fabric-service', cookie)

        #----- Get whoami info from uis request
        whoami_request = s.get('https://uis.fabric-testbed.net/whoami')

        print("-----whoami json-----")
        print(whoami_request.json())
        print("======whoami json=====")

        #----- Get whoami results
        whoami = whoami_request.json().get('results', None)
        if not whoami:
            print("No whoami results")
            return None
        whoami = whoami[0]
        print(whoami)
        api_user.whoami = whoami

        #----- Get uuid
        api_user.uuid = whoami.get('uuid', None)
        if not api_user.uuid:
            print("no uuid")
            return None

        #----- Get fab person
        fab_person_request = s.get(url='https://uis.fabric-testbed.net/people/{0}?as_self=true'.format(api_user.uuid))

        fab_person = fab_person_request.json().get('results', None)
        if fab_person:
            fab_person = fab_person[0]
        else:
            return None

        api_user.fab_person = fab_person

        #api_user.affiliation = fab_person.json().get('results', [])[0].get('affiliation')
        #api_user.email = fab_person.json().get('results', [])[0].get('email')
        #api_user.name = fab_person.json().get('results', [])[0].get('name')
        #api_user.cilogon_id = fab_person.json().get('results', [])[0].get('cilogon_id')
        #api_user.access_type = ApiUser.COOKIE
        projects = []
        fabric_roles = []
        print("_____________________fab person json___________")
        print(fab_person)
        print("==============================================")

        for r in fab_person['roles']:
            if is_valid_uuid(r.get('name')[:-3]):
                projects.append(r.get('name')[:-3])
                continue
            else:
                fabric_roles.append(r.get('name'))

        api_user.projects = list(set(projects))
        api_user.fabric_roles = list(set(fabric_roles))
    except Exception as exc:
        print(exc)
    s.close()
    print(vars(api_user))

    return api_user


# def auth_user_by_token(token):
#     """
#     Use token to authorize user
#     - get user uuid from core-api using cookie
#     - with user uuid populate user information from core-api /people/{uuid}?as_self=true
#     """
#     api_user = ApiUser(uuid=os.getenv('API_USER_ANON_UUID'), projects=[], fabric_roles=[])
#     s = requests.Session()
#     try:
#         s.headers['Authorization'] = 'Bearer {0}'.format(token)
#         whoami = s.get(url=os.getenv('FABRIC_CORE_API') + '/whoami')
#         api_user.uuid = whoami.json().get('results', [])[0].get('uuid', os.getenv('API_USER_ANON_UUID'))
#         fab_person = s.get(url=os.getenv('FABRIC_CORE_API') + '/people/{0}?as_self=true'.format(api_user.uuid))
#         api_user.affiliation = fab_person.json().get('results', [])[0].get('affiliation')
#         api_user.email = fab_person.json().get('results', [])[0].get('email')
#         api_user.name = fab_person.json().get('results', [])[0].get('name')
#         api_user.cilogon_id = fab_person.json().get('results', [])[0].get('cilogon_id')
#         api_user.access_type = ApiUser.TOKEN
#         projects = []
#         fabric_roles = []
#         for r in fab_person.json().get('results', [])[0].get('roles'):
#             if is_valid_uuid(r.get('name')[:-3]):
#                 projects.append(r.get('name')[:-3])
#                 continue
#             else:
#                 fabric_roles.append(r.get('name'))

#         api_user.projects = list(set(projects))
#         api_user.fabric_roles = list(set(fabric_roles))
#     except Exception as exc:
#         print(exc)
#     s.close()
#     return api_user


# def is_token_revoked(token: str) -> bool:
#     """
#     Check all incoming tokens against a token revocation list (TRL)
#     - TODO: SHA256 simple hash <-- needs to mirror whatever CM is doing
#     """
#     revocation_list = ['ba8a9d292308e55ac9ca1f995625aecb2876fb4ba16935152a69a0efc28e4cbe']
#     try:
#         token_hash = hashlib.new('sha256')
#         token_hash.update(token.encode())
#         if token_hash.hexdigest() in revocation_list:
#             return True
#     except Exception as exc:
#         print(exc)
#         return True
#     return False


def is_valid_uuid(val) -> bool:
     try:
         uuid.UUID(str(val))
         return True
     except ValueError:
         return False