#!/usr/bin/python3

from __future__ import print_function, unicode_literals

from functools import wraps
from sys import stderr

from flask_script import Manager
from peewee import DoesNotExist, IntegrityError

from adapi import app, db, APIUser, APIAuditRecord

manager = Manager(app)

db.create_tables([APIUser, APIAuditRecord], safe=True)


def _get_api_user(user_string):
    """
    Gets an APIUser or prints an error and exits
    Args:
        user_string: the user's name or API key

    Returns:
        The user APIUser object

    """
    try:
        user_string = user_string.lower()
        user = APIUser.select().where((APIUser.name == user_string) |
                                      (APIUser.api_key == user_string)).get()
        return user

    except DoesNotExist:
        print("Error: {0} does not exist".format(user_string), file=stderr)
        exit(-1)


@manager.command
def create_api_user(username):
    """Create an API user"""
    try:
        user = APIUser.create(name=username.lower())
        print(user.name)
        print(user.api_key)

    except IntegrityError:
        print("Error: {0} already exists".format(username), file=stderr)
        exit(-1)


@manager.command
def disable_api_user(username):
    """Disable access for an API user"""
    user = _get_api_user(username)
    user.enabled = False
    user.save()

    print("{0} disabled".format(username))


@manager.command
def enable_api_user(username):
    """Enable access for an API user"""
    user = _get_api_user(username)
    user.enabled = True
    user.save()

    print("{0} enabled".format(username))


@manager.command
def rename_api_user(current_name, new_name):
    """Rename an API user"""
    user = _get_api_user(current_name)
    user.name = new_name
    user.save()
    print("{0} is now {1}".format(current_name, new_name))


@manager.command
def reset_api_user(username):
    """Generate a new API key for an API user"""
    user = _get_api_user(username)
    api_key = user.reset()
    print(username)
    print(api_key)


@manager.command
def list_api_users():
    """List the names of all API users"""
    users = APIUser.select()
    for user in users:
        print(user.name)


@manager.command
def show_api_user(lookup_string):
    """Lookup an API user by name or API key"""
    user = _get_api_user(lookup_string)
    print("Username: {0}".format(user.name))
    print("API Key: {0}".format(user.api_key))
    print("Enabled: {0}".format(user.enabled))
    print("Created: {0}".format(user.created.strftime("%x %X UTC")))
    print("Updated: {0}".format(user.updated.strftime("%x %X UTC")))


if __name__ == "__main__":
    manager.run()
