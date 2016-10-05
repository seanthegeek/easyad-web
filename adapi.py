from os import urandom
import binascii
from datetime import datetime

from flask import Flask, jsonify, request
from functools import wraps
from ldap import LDAPError
from peewee import *

from easyad import EasyAD

app = Flask(__name__)
app.config.from_pyfile("config.py")

ad = EasyAD(app.config)
db = SqliteDatabase('easyad.db')

def generate_api_key(bytes=16):
    return str(binascii.hexlify(urandom(bytes)))


class BaseModel(Model):
    class Meta:
        database = db


class APIUser(BaseModel):
    name = CharField(unique=True)
    api_key = CharField(default=generate_api_key, unique=True)
    enabled = BooleanField()
    created = DateTimeField(datetime.now)
    updated = DateTimeField()

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


def parse_ldap_error(e):
    return "An LDAP error occurred - {0}".format(e.args[0]["desc"])


def api_call(function):
    @wraps(function)
    def process_api_call(*args, **kwargs):
        try:
           return function(*args, **kwargs)

        except ValueError as e:
            return jsonify(dict(error=str(e))), 404
        except LDAPError as e:
            return jsonify(dict(error=parse_ldap_error(e))), 500

    return process_api_call


@app.route("/")
def index():
    return "Hello world!"


@app.route("/user/<user_string>")
@api_call
def get_user(user_string):
    return jsonify(ad.get_user(user_string, json_safe=True))


@app.route("/user/<user_string>/groups")
@api_call
def user_groups(user_string):
    return jsonify(ad.get_all_user_groups(user_string, json_safe=True))


@app.route("/user/<user_string>/member-of/<group_string>")
@api_call
def user_is_member_of_group(user_string, group_string):
    return jsonify(dict(member=ad.user_is_member_of_group(user_string, group_string)))


@app.route("/group/<group_string>")
@api_call
def get_group(group_string):
    return jsonify(ad.get_group(group_string, json_safe=True))


@app.route("/group/<group_string>/members")
@api_call
def get_group_members(group_string):
    return jsonify(ad.get_all_users_in_group(group_string, json_safe=True))


@app.route("/search/user/<user_string>")
@api_call
def search_for_users(user_string):
    search_attributes = None
    return_attributes = None

    if "search_attributes" in request.args:
        search_attributes = request.args["search_attributes"].split(",")
    if "return_attributes" in request.args:
        return_attributes = request.args["return_attributes"].split(",")

    return jsonify(ad.search_for_users(user_string,
                                       search_attributes=search_attributes,
                                       return_attributes=return_attributes,
                                       json_safe=True))


@app.route("/search/group/<group_string>")
@api_call
def search_for_groups(group_string):
    search_attributes = None
    return_attributes = None

    if "search_attributes" in request.args:
        search_attributes = request.args["search_attributes"].split(",")
    if "return_attributes" in request.args:
        return_attributes = request.args["return_attributes"].split(",")

    return jsonify(ad.search_for_groups(group_string,
                                        search_attributes=search_attributes,
                                        return_attributes=return_attributes,
                                        json_safe=True))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
