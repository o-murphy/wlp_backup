from scripts import pywlapi
from scripts import export_json
import sqlite3
import json
from tqdm import tqdm
from datetime import datetime, timedelta
import logging


def search_items(host, eid, items_type):
    svc = 'core/search_items'
    params = {
        "spec": {
            "itemsType": items_type,
            "propName": "sys_id",
            "propValueMask": "*",
            "sortType": "sys_id"
        },
        "force": 1,
        "flags": 1,
        "from": 0,
        "to": 0}
    return pywlapi.request(host=host, svc=svc, params=params, eid=eid)


def backup(host, token, item_type):
    date = datetime.now().date()
    eid = pywlapi.login(host=host, token=token)['eid']
    item = search_items(host, eid, item_type)['items']

    for i in tqdm(item, desc=f'{item_type} backup'):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        if item_type == 'avl_unit':
            try:
                json_data = export_json.export_unit(host, eid, item_id=i['id'])

                json_object = json.dumps(json_data, ensure_ascii=False)
                json_gen = json_data['general']
                json_gen['sid'] = i['id']
                json_gen['date'] = date
                json_gen['json'] = json_object
                json_gen['status'] = 'OK'
                cursor.execute("""INSERT INTO unit (sid, status, date, nm, hw, uid, ph, ph2, json)
                                VALUES (:sid, :status, :date, :n, :hw, :uid, :ph, :ph2, :json)""", json_gen)
                conn.commit()
            except Exception as e:
                print(e)
                json_gen['sid'] = i['id']
                json_gen['n'] = i['nm']
                json_gen['hw'] = 'undefined'
                json_gen['date'] = date
                json_gen['json'] = str(e)
                json_gen['status'] = 'ERROR'
                cursor.execute("""INSERT INTO unit (sid, status, date, nm, hw, json)
                                VALUES (:sid, :status, :date, :n, :hw, :json)""", json_gen)
                conn.commit()

        elif item_type == 'avl_resource':
            try:
                json_data = export_json.export_resource(host, eid, item_id=i['id'])
                json_object = json.dumps(json_data, ensure_ascii=False)
                json_gen = {'sid': i['id'], 'n': i['nm'], 'date': date, 'status': 'OK', 'json': json_object}
                cursor.execute("""INSERT INTO resource (sid, status, date, nm, json)
                                VALUES (:sid, :status, :date, :n, :json)""", json_gen)
                conn.commit()
            except Exception as e:
                print(e)
                json_gen = {'sid': i['id'], 'n': i['nm'], 'date': date, 'status': 'ERROR', 'json': str(e)}
                cursor.execute("""INSERT INTO resource (sid, status, date, nm, json)
                                VALUES (:sid, :status, :date, :n, :json)""", json_gen)
                conn.commit()

        elif item_type == 'user':
            try:
                json_data = export_json.export_user(host, eid, item_id=i['id'])
                json_object = json.dumps(json_data, ensure_ascii=False)
                json_gen = {'sid': i['id'], 'n': i['nm'], 'date': date, 'status': 'OK', 'json': json_object}
                cursor.execute("""INSERT INTO user (sid, status, date, nm, json)
                                VALUES (:sid, :status, :date, :n, :json)""", json_gen)
                conn.commit()
            except Exception as e:
                print(e)
                json_gen = {'sid': i['id'], 'n': i['nm'], 'date': date, 'status': 'ERROR', 'json': str(e)}
                cursor.execute("""INSERT INTO user (sid, status, date, nm, json)
                                VALUES (:sid, :status, :date, :n, :json)""", json_gen)
                conn.commit()

        conn.close()
    log.info('backup success')

def delete_old_data(table):
    log.info('removing old data...')
    # print('deleting old records')
    date = datetime.now().date()
    last_day = date - timedelta(days=14)
    conn = sqlite3.connect("wlpbackup.db")
    cursor = conn.cursor()
    sql = f"""DELETE from {table} where date = '{last_day}'"""
    cursor.execute(sql)
    conn.commit()
    conn.close()
    # print('old records deleted')
    log.info('old data removed')

def main():
    log.info("starting backup...")
    try:
        # print(f'{datetime.now()} : backup started')

        try:
            log.info('resources backup started...')
            backup(host, token, item_type='avl_resource')
            delete_old_data(table='resource')
        except Exception:
            log.exception('backup error')

        try:
            log.info('units backup started...')
            backup(host, token, item_type='avl_unit')
            delete_old_data(table='unit')
        except Exception:
            log.exception('backup error')

        try:
            log.info('units backup started...')
            backup(host, token, item_type='user')
            delete_old_data(table='user')
        except Exception:
            log.exception('backup error')

        log.info('backup ended')
        # print('backup ready')
    except Exception as ex:
        log.exception('Fatal Error occurred!')
        log.critical('')


if __name__ == "__main__":
    logging.basicConfig(filename='trace.log', filemode='a', level='INFO',
                        format='%(asctime)s %(name)s %(levelname)s: %(message)s')
    log = logging.getLogger('trace')
    log.info("reading config...")
    try:
        with open('config.json', 'r') as cfg:
            config = json.load(cfg)
        host = config['host']
        token = config['token']
        db_path = config['db_path']

        log.info("success")
        main()
    except Exception:
        log.exception('wrong config file!')

