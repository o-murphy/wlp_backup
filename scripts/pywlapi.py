import requests
import json

HEADERS = {"Content-Type":"application/x-www-form-urlencoded"}

def request(host, svc, params, eid, *args, **kwargs):
    url = f'{host}/wialon/ajax.html?svc={svc}&sid={eid}'
    data = f'&params={json.dumps(params)}'
    r = requests.post(url=url, data=data.encode('utf-8'), headers=HEADERS)
    # print(url+data)
    return r.json()

def login(host, token, user='', *args, **kwargs):
    params = {'token':token, 'operateAs':user}
    url = f'{host}/wialon/ajax.html?svc=token/login'
    data = f'&params={json.dumps(params)}'
    # print(url+str(data))
    r = requests.post(url=url, data=data.encode('utf-8'), headers=HEADERS)
    return r.json()

def avl_evts(host, eid, *args, **kwargs):
    r = request(host, svc='avl_evts', params={}, eid=eid)
    return r.json

def raw(host, svc, params, eid, *args, **kwargs):
    url = f'{host}/wialon/ajax.html?svc={svc}&sid={eid}'
    data = f'&params={json.dumps(params)}'
    # print(url+str(data))
    r = requests.post(url=url, data=data.encode('utf-8'), headers=HEADERS)
    return r
