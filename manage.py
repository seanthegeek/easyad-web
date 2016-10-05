#!/usr/bin/python3

from flask_script import Manager

from adapi import app, db, APIUser, APIAuditRecord

manager = Manager(app)

db.create_tables([APIUser, APIAuditRecord], safe=True)


@manager.option("-c --create", dest="username")
def create_api_user(username):
    user = APIAuditRecord.create(name=username)
    print(user.name)
    print(user.api_key)


@manager.option("-d --disable", dest="username")
def disable_api_user(username):
    return APIAuditRecord.create(name=username)


@manager.option("-e --enable", dest="username")
def enaable_api_user(username):
    return APIAuditRecord.create(name=username)