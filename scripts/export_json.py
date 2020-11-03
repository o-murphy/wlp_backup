from scripts import pywlapi
import json


def load_item(host, eid, item_id):
    svc = 'core/search_item'
    params = {
        "id": item_id,
        "flags": 9007199254740991
    }
    return pywlapi.request(host=host, svc=svc, params=params, eid=eid)['item']


def load_resource_data(host, eid, item_id, cols):
    svc = 'core/batch'
    with open('param_json/resource_data.json', 'r') as fp:
        params = json.load(fp)
    for i in range(len(params['params'])):
        params['params'][i]['params']['itemId'] = item_id
        col = cols[i].values()
        for c in col:
            params['params'][i]['params']['col'].append(c['id'])
    return pywlapi.request(host=host, svc=svc, params=params, eid=eid)


def load_object_data(host, eid, item_id, hw_id):
    svc = 'core/batch'
    with open('param_json/object_data.json', 'r') as fp:
        params = json.load(fp)
    for i in range(len(params['params'])):
        params['params'][i]['params']['itemId'] = item_id
    params['params'][0]['params']['hwId'] = hw_id
    return pywlapi.request(host=host, svc=svc, params=params, eid=eid)


def get_hw_params(host, eid, hw_id):
    svc = 'core/get_hw_types'
    params = {
        "filterType": "id",
        "filterValue": [hw_id],
        "includeType": "0",
        "ignoreRename": "1"
    }
    return pywlapi.request(host=host, svc=svc, params=params, eid=eid)


def json_adder(json_keys, responce_key):
    json_keys_list = json_keys.split(',')
    json_list = []
    default = ''
    for key in json_keys_list:
        json_list.append(responce_key.get(key, default))
    return json_list


def export_unit(host, eid, item_id):
    # eid = pywlapi.login(host=host, token=token)['eid']  # get eid
    item = load_item(host, eid, item_id)  # get item
    hw_id = item['hw']  # get hw type id

    # get hw type name & other params:
    hw_params = get_hw_params(host, eid, hw_id)

    # get hwConfig, reportProps, driver_activity, msgFilter, commands, driving:
    data = load_object_data(host, eid, item_id, hw_id)

    default = ''

    json_file = {  # add default .wlp keys
        'mu': 0,
        'type': 'avl_unit',
        'version': 'b4',
        'imgRot': item['prp'].get('img_rot', default)
    }

    counters = {  # счетчики
        'cfl': item['cfl'],
        'cnm': item['cnm'],
        'cneh': item['cneh'],
        'cnkb': item['cnkb']
    }
    general = {  # настройки подключения
        'n': item['nm'],
        'uid': item['uid'],
        'uid2': item['uid2'],
        'ph': item['ph'],
        'ph2': item['ph2'],
        'psw': item['psw'],
        'hw': hw_params[0]['name']
    }

    reportProps = data[1]  # свойства для отчетов
    reportProps['driver_activity'] = data[2]  # insert driver_activity

    advProps = item['prp']  # дополнительные свойства
    if advProps.get('img_rot', False):
        advProps.pop('img_rot')
    if advProps.get('img_rot', False):
        advProps.pop('idrive')
    advProps['msgFilter'] = data[3]  # insert "Фильтрация сообщений"

    trip = item['rtd']  # Детектор поездок
    fuel = item['rfc']  # Расход топлива
    hwConfig = {  # hwConfig (есть в .wlp, не обязательно)
        'fullData': 1,
        'hw': hw_params[0]['name'],  # insert hw type name
        'params': data[0]  # insert update_hw_params
    }

    json_file['sensors'] = list(item['sens'].values())  # датчики
    json_file['fields'] = list(item['flds'].values())  # произвольные поля
    json_file['afields'] = list(item['aflds'].values())  # административные поля
    json_file['aliases'] = data[4]  # команды
    json_file['intervals'] = list(item['si'].values())  # интервалы техобслуживания
    json_file['counters'] = counters
    json_file['general'] = general
    json_file['reportProps'] = reportProps
    json_file['advProps'] = advProps
    json_file['trip'] = trip
    json_file['fuel'] = fuel
    json_file['profile'] = list(item['pflds'].values())  # характеристики ТС
    json_file['driving'] = data[5]  # качество вождения
    json_file['hwConfig'] = hwConfig

    return json_file


def export_resource(host, eid, item_id):
    json_file = {'mu': 0,
                 'type': 'avl_resource',
                 'version': 'b4'}

    # eid = pywlapi.login(host=host, token=token)['eid']  # get eid
    item = load_item(host, eid, item_id)  # get item

    cols = [item['zl'],
            item['ujb'],
            item['unf'],
            item['rep']]

    # get zones, tasks, notifications, reports:
    data = load_resource_data(host, eid, item_id, cols)

    json_file['zones'] = data[0]
    json_file['jobs'] = data[1]
    json_file['notifications'] = data[2]
    json_file['reports'] = data[3]
    json_file['drivers'] = list(item['drvrs'].values())
    json_file['trailers'] = list(item['trlrs'].values())
    json_file['tags'] = list(item['tags'].values())

    return json_file


def export_user(host, eid, item_id):
    json_file = {'mu': 0,
                 'type': 'user',
                 'version': 'b4'}

    # eid = pywlapi.login(host=host, token=token)['eid']  # get eid
    item = load_item(host, eid, item_id)  # get item
    svc = 'user/get_locale'
    params = {"userId": item_id}
    locale = pywlapi.request(host=host, svc=svc, params=params, eid=eid)  # get locale
    json_file['locale'] = locale

    default = ''
    prp = item.get('prp', default)
    with open('param_json/user_keys_list.json', 'r') as jkl:
        json_keys_list = json.load(jkl)

    for json_keys in json_keys_list:
        json_file[json_keys] = json_adder(json_keys, responce_key=prp)

    json_file['acs_tmpl'] = prp.get('access_templates', default)
    json_file['usr_ugef,usr_uhom'] = prp.get('usr_ugef,usr_uhom', default)

    return json_file


if __name__ == "__main__":
    with open('../config.json', 'r') as cfg:
        config = json.load(cfg)

    host = config['servers']['https://gps.uonline.com.ua']['host']
    token = config['servers']['https://gps.uonline.com.ua']['token']

