from __future__ import unicode_literals

from os import urandom
import binascii
from datetime import datetime
from functools import wraps

from flask import Flask, jsonify, request, render_template
from ldap import LDAPError
from peewee import *

from easyad import EasyAD

app = Flask(__name__)
app.config.from_pyfile("config.py")

ad = EasyAD(app.config)
db = SqliteDatabase('easyad.db')


def generate_api_key(byte_size=16):
    return binascii.hexlify(urandom(byte_size)).decode(encoding="utf-8")


class BaseModel(Model):
    class Meta:
        database = db


class APIUser(BaseModel):
    name = CharField(unique=True)
    api_key = CharField(default=generate_api_key, unique=True)
    enabled = BooleanField(default=True)
    created = DateTimeField(default=datetime.now)
    updated = DateTimeField(default=datetime.now)

    def enable(self):
        self.enabled = True
        self.updated = datetime.now()
        self.save()

    def disable(self):
        self.enabled = False
        self.updated = datetime.now()
        self.save()

    def rename(self, new_name):
        self.name = new_name
        self.updated = datetime.now()
        self.save()

    def reset(self):
        self.api_key = generate_api_key()
        self.updated = datetime.now()
        self.save()
        return self.api_key


class APIAuditRecord(BaseModel):
    user = ForeignKeyField(APIUser, related_name="audit_records")
    timestamp = DateTimeField(default=datetime.now)
    action = CharField()

db.create_tables([APIUser, APIAuditRecord], safe=True)


def parse_ldap_error(e):
    return "An LDAP error occurred - {0}".format(e.args[0]["desc"])


def api_call(function):
    @wraps(function)
    def process_api_call(*args, **kwargs):
        if "api_key" not in request.args:
            return jsonify(dict(error="You must supply an api_key parameter")), 401
        try:
            user = APIUser.get(api_key=request.args["api_key"])
            if not user.enabled:
                return jsonify(dict(error="This API key is disabled")), 403
            return function(*args, **kwargs)

        except DoesNotExist:
            return jsonify(dict(error="The API key is invalid")), 403
        except ValueError as e:
            return jsonify(dict(error=str(e))), 404
        except LDAPError as e:
            return jsonify(dict(error=parse_ldap_error(e))), 500

    return process_api_call


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/authenticate", methods=["GET", "POST"])
@api_call
def authenticate_user():
    if request.method != "POST":
        return jsonify(dict(error="Must be sent as a POST request")), 400
    if "username" not in request.args or "password" not in request.args:
        return jsonify(dict(error="Must provide a username and password")), 400
    return ad.authenticate_user(request.args["username"], request.args["password"])


@app.route("/user/<user_string>")
@api_call
def get_user(user_string):
    base = None
    if "base" in request.args:
        base = request.args["base"]
    attributes = None
    if "attributes" in request.args:
        attributes = request.args["attributes"].split(",")
    return jsonify(ad.get_user(user_string, base=base, attributes=attributes, json_safe=True))


@app.route("/user/<user_string>/groups")
@api_call
def user_groups(user_string):
    base =None
    if "base" in request.args:
        base = request.args["base"]
    return jsonify(ad.get_all_user_groups(user_string, base=base, json_safe=True))


@app.route("/user/<user_string>/member-of/<group_string>")
@api_call
def user_is_member_of_group(user_string, group_string):
    base = None
    if "base" in request.args:
        base = request.args["base"]
    return jsonify(dict(member=ad.user_is_member_of_group(user_string, group_string, base=base)))


@app.route("/group/<group_string>")
@api_call
def get_group(group_string):
    base = None
    if "base" in request.args:
        base = request.args["base"]
    attributes = None
    if "attributes" in request.args:
        attributes = request.args["attributes"].split(",")
    return jsonify(ad.get_group(group_string, base=base, attributes=attributes, json_safe=True))


@app.route("/group/<group_string>/users")
@api_call
def get_group_members(group_string):
    base = None
    if "base" in request.args:
        base = request.args["base"]
    return jsonify(ad.get_all_users_in_group(group_string, base=base, json_safe=True))


@app.route("/search/users/<user_string>")
@api_call
def search_for_users(user_string):
    search_attributes = None
    return_attributes = None
    base = None

    if "base" in request.args:
        base = request.args["base"]
    if "search_attributes" in request.args:
        search_attributes = request.args["search_attributes"].split(",")
    if "return_attributes" in request.args:
        return_attributes = request.args["return_attributes"].split(",")

    return jsonify(ad.search_for_users(user_string,
                                       base=base,
                                       search_attributes=search_attributes,
                                       return_attributes=return_attributes,
                                       json_safe=True))


@app.route("/search/groups/<group_string>")
@api_call
def search_for_groups(group_string):
    search_attributes = None
    return_attributes = None
    base = None

    if "base" in request.args:
        base = request.args["base"]
    if "search_attributes" in request.args:
        search_attributes = request.args["search_attributes"].split(",")
    if "return_attributes" in request.args:
        return_attributes = request.args["return_attributes"].split(",")

    return jsonify(ad.search_for_groups(group_string,
                                        base=base,
                                        search_attributes=search_attributes,
                                        return_attributes=return_attributes,
                                        json_safe=True))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
