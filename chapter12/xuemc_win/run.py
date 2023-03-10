# -*- coding: utf-8 -*-
from web.app import app, api
from Utils import Util, ProtocolItem
import json
import threading
import datetime
from DB import orm
from Logic import logic, restful

from flask import request
from flask_restful import Resource
import flask_restless

from web.views import *


def post_get_one(result=None, **kw):
    if result:
        logic.SetDefaultImage(result)
    return result


def post_get_many(result=None, search_params=None, **kw):
    if result and restful.ITEM_OBJECTS in result:
        for obj in result[restful.ITEM_OBJECTS]:
            logic.SetDefaultImage(obj)
    return result


def backup_pre_put_single_account(instance_id=None, data=None, **kw):
    if instance_id is None:
        return
    account = orm.Account.query.filter_by(username=instance_id).first()
    if account is None:
        account = orm.Account(instance_id, None, None, None, 0, 0, None)
        orm.db.session.add(account)
        orm.db.session.commit()
    if restful.ITEM_CODE in data:
        terminal = orm.Terminal.query.filter_by(
            code=data[restful.ITEM_CODE]).first()
        if terminal is None:
            terminal = orm.Terminal(account.id, data.get(restful.ITEM_OS),
                                    data[restful.ITEM_CODE])
            orm.db.session.add(terminal)
        terminal.account_id = account.id
        terminal.os = data.get(restful.ITEM_OS)
        orm.db.session.commit()
    data.pop(restful.ITEM_CODE, None)
    data.pop(restful.ITEM_OS, None)


def pre_put_single_account(instance_id=None, data=None, **kw):
    if instance_id is None:
        return
    account = orm.Account.query.get(int(instance_id))
    if account is None:
        return
    if restful.ITEM_CHECKCODE in data:
        dtNow = datetime.datetime.now()
        dtValidTime = account.dtcreate if account.dtcreate else datetime.datetime.now(
        )
        dtValidTime = dtValidTime + datetime.timedelta(minutes=15)
        if account.checkcode == data.get(
                restful.ITEM_CHECKCODE) and dtNow < dtValidTime:
            account.flag_telephone = 1
            orm.db.session.commit()
    if restful.ITEM_TELEPHONE in data:
        if account.telephone != data.get(restful.ITEM_TELEPHONE):
            account.flag_telephone = 0
            orm.db.session.commit()
    data.pop(restful.ITEM_FLAG_TELEPHONE, None)
    data.pop(restful.ITEM_CHECKCODE, None)


def pre_post_account(data=None, **kw):
    """Accepts a single argument, `data`, which is the dictionary of
    fields to set on the new instance of the model.

    """
    if restful.ITEM_USERNAME not in data:
        data[restful.ITEM_USERNAME] = data.get(restful.ITEM_TELEPHONE)
    data[restful.ITEM_DTCREATE] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    pass


import random


def post_post_account(result=None, **kw):
    """Accepts a single argument, `result`, which is the dictionary
    representation of the created instance of the model.

    """
    if result and restful.ITEM_ID in result:
        account = orm.Account.query.get(int(result.get(restful.ITEM_ID)))
        account.checkcode = str(random.randint(100001, 999999))
        orm.db.session.commit()
        # send sms verification here
        message = '??????????????????%s, ?????????????????????15???????????? ???????????????' % account.checkcode
        Util.SendSMSByZA(account.telephone, message)
    return result
    pass


def pre_post_test(data=None, **kw):
    if restful.ITEM_USERNAME not in data:
        data[restful.ITEM_USERNAME] = data.get(restful.ITEM_TELEPHONE)
    pass


class Account(Resource):
    def post(self):
        body = json.loads(request.data)
        account = orm.Account.query.filter_by(
            telephone=body.get(restful.ITEM_TELEPHONE)).first()
        if account:
            # send sms verification here
            if account.flag_telephone != 1:
                account.dtcreate = datetime.datetime.now()
                account.checkcode = str(random.randint(100001, 999999))
                orm.db.session.commit()
                message = '??????????????????%s, ?????????????????????15???????????? ???????????????' % account.checkcode
                Util.SendSMSByZA(account.telephone, message)

            dtcreate = account.dtcreate.strftime(
                "%Y-%m-%dT%H:%M:%S") if account.dtcreate else None

            return {
                restful.ITEM_ID: account.id,
                restful.ITEM_FLAG_TELEPHONE: account.flag_telephone,
                restful.ITEM_TELEPHONE: account.telephone,
                restful.ITEM_USERNAME: account.username,
                restful.ITEM_NAME: account.name,
                restful.ITEM_DTCREATE: dtcreate,
                restful.ITEM_SOURCE: account.source
            }
        else:
            return restful.PostAccount(body)
        return {'hello': 'world'}


api.add_resource(Account, '/bd/api/v1.0/account')

# Create the Flask-Restless API manager.
orm.db.create_all()
manager = flask_restless.APIManager(app, flask_sqlalchemy_db=orm.db)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.create_api(orm.Advert, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(orm.Agespan, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(orm.Area, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(
    orm.Bulletin,
    methods=['GET'],
    url_prefix='/bd/api/v1.0',
    postprocessors={
        'GET_SINGLE': [post_get_one],
        'GET_MANY': [post_get_many]
    })
manager.create_api(orm.Feature, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(orm.Feetype, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(
    orm.Institution,
    methods=['GET'],
    url_prefix='/bd/api/v1.0',
    postprocessors={
        'GET_SINGLE': [post_get_one],
        'GET_MANY': [post_get_many]
    })
manager.create_api(
    orm.InstitutionFeature, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(
    orm.School,
    results_per_page=7,
    methods=['GET'],
    url_prefix='/bd/api/v1.0',
    postprocessors={
        'GET_SINGLE': [post_get_one],
        'GET_MANY': [post_get_many]
    })
manager.create_api(
    orm.SchoolFeature, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(orm.Schooltype, methods=['GET'], url_prefix='/bd/api/v1.0')
manager.create_api(
    orm.Account,
    methods=['GET', 'PUT', 'PATCH'],
    url_prefix='/bd/api/v1.0',
    preprocessors={'PATCH_SINGLE': [pre_put_single_account]},
    exclude_columns=['checkcode', 'password'])
manager.create_api(
    orm.Account,
    methods=['POST'],
    url_prefix='/bd/api/v1.0/back',
    preprocessors={'POST': [pre_post_account]},
    postprocessors={'POST': [post_post_account]},
    exclude_columns=['checkcode', 'password'])
manager.create_api(
    orm.Test,
    methods=['POST', 'PATCH'],
    preprocessors={'POST': [pre_post_test]},
    url_prefix='/bd/api/v1.0')


class Messages(Resource):
    def post(self):
        pass
        print("POST a Message:", request.data, "--")
        body = json.loads(request.data)
        if body[ProtocolItem.MESSAGES][
                ProtocolItem.DEST_TYPE] == ProtocolItem.VALUE_IOS:
            threading.Thread(
                target=Util.push_ios,
                args=([body[ProtocolItem.MESSAGES][ProtocolItem.DEST_ID]],
                      "alarm",
                      body[ProtocolItem.MESSAGES][ProtocolItem.CONTENT]
                      )).start()


#            Util.push_ios([body[ProtocolItem.MESSAGES][ProtocolItem.DEST_ID]], 'alarm', body[ProtocolItem.MESSAGES][ProtocolItem.CONTENT])
        return {'_id': '0'}

    def get(self):
        return {'get': 'None'}


api.add_resource(Messages, '/bd/api/messages')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5010)
