from bn2.drivers.slavedriver import SlaveDriver
import traceback
from bn2.db import db
from bn2.db import masterdb

from bn2.utils.msgqueue \
    import create_local_task_message, INBOX_SYS_CRITICAL_MSG, INBOX_SYS_MSG, OUTBOX_SYS_MSG, \
    INBOX_TASK1_MSG, PriorityQueue, safe_copy_route_meta

import time

from flask import Flask, request, render_template, send_from_directory
from flask_socketio import SocketIO, join_room, emit, disconnect
from flask_cors import CORS

import requests
import json
import os
import sys

from datetime import datetime, timedelta
from sqlalchemy import event, or_, desc

from functools import wraps

import random
import json

driver = SlaveDriver({})

class ControlPanelv2 (object):
    alert_non_persist_id = 0
    model_tag = "CPv2"
    last_task_id = 0
    last_job_id = 0
    last_db_update = datetime.utcnow()
    master_configs = None
    emitter_inbox = None


    def _init_CPv2_configs(self):
        driver.add_bot_config(
            'cp_ip',
            'Control Panel IP',
            'str',
            default='0.0.0.0'
        )

        driver.add_bot_config(
            'cp_port',
            'Control Panel Port',
            'number',
            default=7000
        )

        driver.add_bot_config(
            'cp_dist_dir',
            'Control Panel dist dir',
            'path',
            default="%%/dist"
        )

        driver.add_bot_config(
            'master_db_engine',
            'Master Database Engine',
            'str',
        )

        driver.add_bot_config(
            'master_db_address',
            'Master Database Address/File path',
            'str',
        )

        driver.load_bot_config_from_file()


    def __init__(self, driver):
        self.driver = driver
        driver.register(self)
        self._init_CPv2_configs()
        driver.log.debug("Starting ControlPanelv2...")
        self.server_host = driver.get_bot_config("cp_ip")
        self.server_port = driver.get_bot_config("cp_port")
        self.server_args = {
            'host': self.server_host,
            'port': self.server_port
        }

        server_init = driver.create_local_task_message(
            'bd.sd.@CPv2.server.init',
            {}
        )

        driver.add_start_up_route(server_init)

        driver.add_check_func(self.check_db, 1000)
        driver.add_check_func(self.request_master_resp_times, 1000 * 10)

        self.master_db = db.DBWrapper(driver.get_bot_config('master_db_address'), masterdb.Base, driver.get_bot_config('master_db_engine'), scoped_thread=True)


    def emit(self, event, event_data, *, namespace='/', sids=[]):
        if not (type(sids) == list):
            sids = [sids]
        data = {
            'event': event,
            'event_data': event_data,
            'ns': namespace,
            'sids': sids
        }
        if self.emitter_inbox:
            self.emitter_inbox.put(data, 0)



    def send_past_objs(self, data):
        obj_class = getattr(masterdb, data['obj_type'])
        obj_args = data.get('obj_args')
        sid = data['sid']

        cnt = data.get('cnt', 0)
        per = data.get('per', 10)

        if not per or per > 100:
            per = 100

        offset = cnt * per
        with self.master_db.scoped_session() as session:
            args = None
            if obj_args:
                args = [getattr(obj_class, key)==value for key, value in obj_args.items()]

            objs_query = session.query(obj_class)

            if args:
                objs_query = objs_query.filter(*args)

            objs = objs_query\
                .offset(offset)\
                .limit(per)\
                .all()

            _map = {
                'SlaveTask': 'tasks',
                'SlaveJob': 'jobs',
                'SlaveJobReport': 'job_reports'
            }
            objs = [self.master_db.as_json(obj) for obj in objs]
            self.updateStream(_map[data['obj_type']], objs, sids=[sid])



    def send_past_updates(self, sids):
        if not sids:
            return
        if type(sids) != type(list):
            sids = [sids]


        self.send_master_configs()
        mdata = {'is_connected_master': self.driver.CONNECTED_TO_MASTER}
        self.updateStream('session/is_connected_master', mdata, sids=sids, sub_path=True)


        with self.master_db.scoped_session() as session:
            from_update = datetime.utcnow() - timedelta(hours=24)
            #tasks = self.master_db.get_updated_rows(session, masterdb.SlaveTask, from_update)

            slave_types = session.query(masterdb.SlaveType).all()
            slave_types = [self.master_db.as_json(slave_type) for slave_type in slave_types]
            self.updateStream('slave_types', slave_types, sids=sids)


            jobs = self.master_db.get_updated_rows(session, masterdb.SlaveJob, from_update, limit=500, hidden=False)
            jobs = [self.master_db.as_json(job) for job in jobs]
            self.updateStream('jobs', jobs, sids=sids)





            scheduler_groups = session.query(masterdb.SchedulerGroup)\
                .filter(masterdb.SchedulerGroup.active==True)\
                .all()


            schedulers = []

            if len(scheduler_groups):

                for sg in scheduler_groups:
                    schedulers.extend(session.query(masterdb.Scheduler)\
                                    .filter(masterdb.Scheduler.scheduler_group_id==sg.id)\
                                    .all())


                scheduler_groups = [self.master_db.as_json(sg) for sg in scheduler_groups]
                schedulers = [self.master_db.as_json(s) for s in schedulers]


            self.updateStream('scheduler_groups', scheduler_groups, sids=sids)
            self.updateStream('schedulers', schedulers, sids=sids)

            alerts = session.query(masterdb.Alert)\
                .filter(masterdb.Alert.viewed==False)\
                .all()

            alerts = [self.master_db.as_json(alert) for alert in alerts]
            self.updateStream('alerts', alerts, sids=sids)

            slaves = session.query(masterdb.Slave)\
                .filter(masterdb.Slave.active==True)\
                .all()

            slaves = [self.master_db.as_json(slave) for slave in slaves]
            self.updateStream('slaves', slaves, sids=sids)



    def check_db(self):
        if not self.emitter_inbox:
            driver.log.info("Emitter inbox is None, waiting", path='bd.sd.@CPv2.db.check')
            driver.sleep(5000)
        got = False
        update_time = datetime.utcnow() -timedelta(seconds=2)

        with self.master_db.scoped_session() as session:

            tasks = self.master_db.get_updated_rows(session, masterdb.SlaveTask, self.last_db_update)
            if tasks:
                got = True
                tasks = [self.master_db.as_json(task, remove_cols=['data', 'route_meta']) for task in tasks]
                self.updateStream('tasks', tasks)


            jobs = self.master_db.get_updated_rows(session, masterdb.SlaveJob, self.last_db_update, hidden=False)
            if jobs:
                got = True
                jobs = [self.master_db.as_json(job) for job in jobs]
                self.updateStream('jobs', jobs)

            job_reports = self.master_db.get_updated_rows(session, masterdb.SlaveJobReport, self.last_db_update)
            if job_reports:
                got = True
                job_reports = [self.master_db.as_json(jr, cols=['id', 'content', 'data', 'job_id', 'type']) for jr in job_reports]
                self.updateStream('job_reports', job_reports)


            slaves = self.master_db.get_updated_rows(session, masterdb.Slave, self.last_db_update)


            if slaves:
                got = True
                slaves = [self.master_db.as_json(slave) for slave in slaves]
                self.updateStream('slaves', slaves)

            scheduler_groups = self.master_db.get_updated_rows(session, masterdb.SchedulerGroup, self.last_db_update)
            if scheduler_groups:
                got = True
                schedulers = []
                for sg in scheduler_groups:
                    schedulers.extend(session.query(masterdb.Scheduler).filter(masterdb.Scheduler.scheduler_group_id==sg.id).all())

                scheduler_groups = [self.master_db.as_json(scheduler_group) for scheduler_group in scheduler_groups]
                schedulers = [self.master_db.as_json(scheduler) for scheduler in schedulers]
                self.updateStream('schedulers', schedulers)
                self.updateStream('scheduler_groups', scheduler_groups)

        if got:
            self.last_db_update = update_time

    def updateStream(self, obj_type, objs, deleting=False, sids=[], sub_path=False, has_obj_id=True):
        data = objs
        if not sub_path:
            data = {'objs': objs, 'type': obj_type, 'delete': deleting, 'has_obj_id':has_obj_id}

        path = 'updateStream'
        if sub_path:
            path+='/'+obj_type
        self.emit(path, data, sids=sids)

    def check_emitter(self):
        msgs = self.emitter_inbox.get(get_all=True)
        for msg in msgs:
            is_updateStream = False
            if msg['event'] == 'updateStream' and msg['event_data']['has_obj_id']:
                obj_ids = [obj['id'] for obj in msg['event_data']['objs']]
                is_updateStream = True

            if msg['sids']:
                l = len(msg['sids'])
                for sid in msg['sids']:
                    socketio.emit(msg['event'], msg['event_data'], namespace=msg['ns'], room=sid)

                if is_updateStream:
                    driver.log.debug("<updateStream:{}> <del:{}> <sids({}):{}> <obj_ids:{}>"\
                            .format(msg['event_data']['type'], msg['event_data']['delete'], l, msg['sids'],obj_ids), path='bd.sd.@CPv2.emitter')
                else:
                    driver.log.debug("Emit: {} <sids({}):{}> data: {}".format(msg['event'], l, msg['sids'], msg['event_data']), path='bd.sd.@CPv2.emitter')

            else:
                socketio.emit(msg['event'], msg['event_data'], namespace=msg['ns'], broadcast=True)

                if is_updateStream:
                    driver.log.debug("<updateStream:{}> <del:{}> <obj_ids:{}>"\
                            .format(msg['event_data']['type'], msg['event_data']['delete'], obj_ids), path='bd.sd.@CPv2.emitter')
                else:
                    driver.log.debug("Emit: {}  data: {}".format(msg['event'], msg['event_data']), path='bd.sd.@CPv2.emitter')



    @driver.route("bd.sd.@CPv2.server.init", is_async=True)
    def bd_sd_CPv2_server_init(self, data, route_meta):
        driver.log.info("Emitter inbox Init: {}".format(os.getpid()))
        self.emitter_inbox = PriorityQueue(1, manager=driver.manager)
        while(not (driver.bn2_public_key and len(driver.route_levels))):
            driver.log.debug("Waiting for master to set bn2 public key and route_levels...")
            driver.sleep(3000)

        driver.log.info("Received bn2 public key and route_levels, init server...")

        server_msg = driver.create_local_task_message(
            'bd.sd.@CPv2.server.run',
            self.server_args,
            pass_secret=True,
            is_process=True
        )

        driver.add_local_msg(server_msg, INBOX_SYS_MSG)


    @driver.route("bd.sd.@CPv2.server.run", only_process=True, level="LOCAL")
    def bd_sd_CPv2_server_run(self, data, route_meta):
        driver.set_process_name("webserver")
        driver.heartbeat.__track_process__(
            name='CPv2 Webserver',
            route='bd.sd.@CPv2.server.run',
            data=data
        )
        pulse_thread = driver.create_thread(driver.heartbeat.send_pulse_loop, start=True)
        check_emitter_thread = driver.create_loop_thread(self.check_emitter, 'Emitter Inbox')
        #check_emitter_thread = socketio.start_background_task(target=self.check_emitter)

        try:
            check_emitter_thread.start()
            #socketio.run(app, host=data['host'], port=data['port'], debug=True)
            app.run(host=data['host'], port=data['port'], threaded=True)

        except Exception as e:
            driver.log.critical("Webserver CPv2 has broke: {}".format(e))
            driver.log.critical(traceback.format_exc())

        finally:
            check_emitter_thread.join()
            pulse_thread.join()

    def create_non_persist_alert(self, msg, go_to=None, color=None, redirect_msg_id=None, redirect_resp=False):
        self.alert_non_persist_id+=1
        id_ = self.alert_non_persist_id
        data = {
            'msg': msg,
            'go_to': go_to,
            'time': str(datetime.utcnow()),
            'viewed': False,
            'id':id_
        }
        if redirect_msg_id:
            data['redirect_msg_id'] = redirect_msg_id
        data['redirect_resp'] = redirect_resp

        if color:
            data['color'] = color
        return data

    def get_redirect_msg(self, data):
        msg = ''
        go_to = None
        redirect_msg_id = data['sid']+driver.create_bot_uuid()

        data['__redirect_msg_id'] = redirect_msg_id
        if data.get('__redirect_msg', None):
            msg =  data['__redirect_msg']

        elif data['route'] ==  'bd.@md.slave.job.add':
            name = data['data']['tasks_data'][0]['name']
            if 'name' in data['data']['job_data'].keys():
                name = data['data']['job_data']['name']
            msg = 'Launching job "{}"...'.format(name)
            pass
        elif data['route'] == 'bd.@md.slave.job.pause':
            msg = "Pausing job [{}]...".format(data['data']['job_id'])
            go_to = '/jobs?job_id={}'.format(data['data']['job_id'])

        elif data['route'] == 'bd.@md.slave.job.stop':
            msg = 'Stopping job [{}]...'.format(data['data']['job_id'])
            go_to = '/jobs?job_id={}'.format(data['data']['job_id'])

        elif data['route'] == 'bd.@md.slave.task.schedule.add':
            msg = 'Adding Scheduler "{}"...'.format(data['data']['name'])
            go_to = '/jobs?tab=scheduled'

        elif data['route'] == 'bd.@md.slave.task.schedule.remove':
            msg = 'Removing scheduler(s) {}...'.format(data['data']['scheduler_group_ids'])

        elif data['route'] == 'bd.@md.slave.kill':
            msg = 'Killing slave(s) {}...'.format(data['data']['ids'])
        elif data['route'] == 'bd.@md.slave.launch':
            msg = 'Launching {} slave(s)'.format(data['data']['count'], data['data']['name'])
        else:
            msg = '{} (undefined redirect msg)'.format(data['route'])

        alert = self.create_non_persist_alert(
            msg,
            color='grey darken-2',
            go_to=go_to,
            redirect_msg_id=redirect_msg_id
        )
        self.updateStream('alerts', [alert], sids=[data['sid']])
        return msg



    @driver.route('bd.sd.@CPv2.redirect')
    def bd_sd_CPv2_redirect(self, data, route_meta):
        k ='__redirect_msg'
        redirect_msg = self.get_redirect_msg(data)
        data[k] = redirect_msg


        #pass user_token and pass it here
        #for now will use CPV2 route meta and token
        data['route_meta'] = route_meta
        data['route_meta']['origin']=driver.uuid
        msg = driver.create_local_task_message('bd.@md.Slave.CPv2.redirected', data)

        driver.send_message_to_master(msg)

    @driver.route('bd.sd.@CPv2.emit')
    def bd_sd_CPv2_emit(self, data, route_meta):
        raise NotImplemented
        #self.emit("EVENT", data)


    @driver.route('bd.sd.@CPv2.db.objs.delete')
    def bd_sd_CPv2_db_objs_delete(self, data, route_meta):
        table_event_map = {

            'SchedulerGroup': 'scheduler_groups',
            'Scheduler': 'schedulers',
            'Slave': 'slaves',
            'SlaveJob': 'jobs',
            'SlaveTask': 'tasks'
        }
        for table in data.keys():
            if len(data[table]):
                self.updateStream(
                    table_event_map[table],
                    [{'id':row} for row in data[table]],
                     deleting=True
                )

    @driver.route('bd.sd.@CPv2<warehouse.table')
    def bd_sd_CPv2_IN_warehouse_table(self, data, route_meta):
        has_headers = False
        keys = []
        if data['table_name'] == 'ChaturbateUser':
            keys = ['id', 'username', 'password', 'email', 'created_time', 'in_use', 'last_used']
            has_headers = True

        elif data['table_name'] == 'ChaturbateUserActivity':
            keys = ['id', 'chaturbate_user_id', 'bn2_job_id', 'bn2_task_id', 'minutes_used', 'time_ended', 'was_targeted']
            has_headers = True

        if has_headers:
            headers = []
            for key in keys:
                headers.append({'value': key, 'text':key})
            data['headers'] = headers

        self.updateStream('warehouse/table/rows', data, sids=[data['sid']], has_obj_id=False)

    @driver.route('bd.sd.@CPv2.users.alerts')
    def bd_sd_CPv2_user_alert(self, data, route_meta):
        self.updateStream('alerts', data['alerts'], sids=data['sids'])

    @driver.route('bd.sd.@CPv2.logs.master')
    def bd_sd_CPv2_master_logs(self, data, route_meta):
        self.updateStream('logs/master', data, sub_path=True)

    @driver.route("bd.sd.@CPv2.usage.master")
    def bd_sd_CPv2_usage_master(self, data, route_meta):
        self.updateStream('usage', data, has_obj_id=False)

    @driver.route("bd.sd.@CPv2<master.resp.times")
    def bd_sd_CPv2_IN_master_resp_times(self, data, route_meta):
        now = datetime.utcnow()
        r = (now - datetime.strptime(data['MASTER_SEND_TIME'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds() * 1000
        r = int(r)
        data['resp_back'] = r
        data['resp_total'] = data['resp_forward'] + data['resp_back']

        out = {
            "slaves": data['slaves'],
            "resp_total": data['resp_forward'] + data['resp_back'],
            "resp_forward": data['resp_forward'],
            "resp_back": r
        }

        self.updateStream('resp_times', out, has_obj_id=False)

    @driver.route("bd.sd.@CPv2>master.resp.times")
    def bd_sd_CPv2_OUT_master_resp_times(self, data, route_meta):
        self.request_master_resp_times()

    @driver.route("bd.sd.@CPv2>master.configs")
    def bd_sd_CPv2_OUT_master_configs(self, data, route_meta):
        #THIS WILL REQUEST or/and SET CONFIGS FROM MASTER
        #ACTION: WILL CAUSE MASTER TO RESPOND
        pass

        #self.request_master_configs()


    @driver.route_guard("MASTER")
    @driver.route("bd.sd.@CPv2<master.configs")
    def bd_sd_CPv2_IN_master_configs(self, data, route_meta):
        self.master_configs = data['configs']
        self.send_master_configs()

    def request_master_resp_times(self):
        msg = driver.create_local_task_message(
            'bd.@md<Slave.CPv2.resp.times',
            {"CPV2_SEND_TIME":str(datetime.utcnow())}
        )
        driver.send_message_to_master(msg)

    def request_master_configs(self):
        msg = driver.create_local_task_message(
            'bd.@md<Slave.CPv2.master.configs',
            {}
        )
        driver.send_message_to_master(msg)


    def send_master_configs(self, sids=[]):
        if self.master_configs:
            self.updateStream('master_configs', self.master_configs, has_obj_id=False)
        else:
            self.request_master_configs()




cpv2 = ControlPanelv2(driver)



def DRIVER_EVENT_MASTER_CONNECTION(is_connected):
    msg = create_local_task_message(
        'bd.@md<Slave.CPv2.master.configs',
        {}
    )
    driver.send_message_to_master(msg)

    data = {'is_connected_master': is_connected}
    if hasattr(cpv2, 'emitter_inbox'):
        cpv2.updateStream('session/is_connected_master', data, sub_path=True)

driver.add_driver_event('MASTER_CONNECTION', DRIVER_EVENT_MASTER_CONNECTION)
cp_dist_dir = driver.get_bot_config("cp_dist_dir")
app = Flask(
    __name__,
    template_folder=cp_dist_dir,
    static_folder=cp_dist_dir
)
CORS(app)

socketio = SocketIO(app, async_mode='threading')
socketio.init_app(app, cors_allowed_origins="*")

@app.route('/favicon.ico')
def return_favicon():
    return send_from_directory(cp_dist_dir,  'favicon.ico')

@app.route('/img/<path:filename>')
def return_img(filename):
    path = os.path.join(cp_dist_dir, 'img/')
    return send_from_directory(path, filename)

@app.route('/css/<path:filename>')
def return_css(filename):
    path = os.path.join(cp_dist_dir, 'css/')
    return send_from_directory(path, filename)

@app.route('/js/<path:filename>')
def return_js(filename):
    path = os.path.join(cp_dist_dir, 'js/')#, filename)
    return send_from_directory(path, filename)

@app.route('/api/slaves/launched/<launch_tag>', methods=['GET'])
def api_slaves_launched_GET(launch_tag):
        creds = driver.get_tag_data(launch_tag, delay=1)
        if not creds:
            driver.log.warning("No more credentials for launch tag [{}]".format(launch_tag), path='api/slaves/launched/.')
            #No more creds
            return "", 403
        return "{}\n{}".format(creds['uuid'], creds['token'])


@app.route('/api/user/verify', methods=['POST'])
def api_user_verifiy_POST():
    payload = {"success":False}

    out = request.get_json()
    out['tag'] = driver.create_tag()

    msg = driver.create_local_task_message(
        "bd.@md.user.verify",
        out
    )
    driver.send_message_to_master(msg, OUTBOX_SYS_MSG)
    token = driver.get_tag_data(out['tag'], delay=10)
    if token:
        payload['success'] = True
        payload['token'] = token
        payload['username'] = out['username']
    return payload

@app.route('/api/job/report/<job_report_id>/content')
def api_job_report_content(job_report_id):
    payload = {"success": False, 'row': None}
    if cpv2:
        with cpv2.master_db.scoped_session() as session:
            content = session.query(masterdb.SlaveJobReport.content).filter(masterdb.SlaveJobReport.id==job_report_id).first()
            payload['data'] =  content
            payload['success'] = True
    return payload


@app.route('/api/job/<job_id>')
def api_job_GET(job_id):
    payload = {"success":False, 'row': None}
    if cpv2:
        with cpv2.master_db.scoped_session() as session:
            job = session.query(masterdb.SlaveJob).filter(masterdb.SlaveJob.id==job_id).first()
            payload['row'] = cpv2.master_db.as_json(job)
            payload['success'] = True
    return payload

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return render_template("index.html")



def check_valid_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.args.get('token')
        """
        Remove not needed anymore
        token = jwt.decode(token, JWT_SECRET, JWT_ALGO)
        """
        return f(*args, **kwargs)
    return decorated_function

class Webserver:

    @staticmethod
    @socketio.on('connect')
    @check_valid_token
    def socket_on_connect():
        log_path = "bd.sd.@CPv2.webserver.connect"

        token = request.args.get('token')
        driver.log.info("New connection from {} -- sid: {} token:{}".format(request.remote_addr, request.sid, token), path=log_path)
        session = request.args.get('session')

        if not token:
            driver.log.warning("sid: {} did not provide token -- Disconnecting".format(request.sid), path=log_path)
            disconnect(request.sid)
            return False

        is_user = driver.check_route_level("USER", {"token": token})
        if not is_user:
            driver.log.debug("Validating user token -- Failed", path=log_path)
            disconnect(request.sid)
            return False
        driver.log.debug("Validating user token -- Successful", path=log_path)

        cpv2.send_past_updates(request.sid)
        return True

    @staticmethod
    @socketio.on('redirect')
    def socket_on_redirect(data):
        data['sid'] = request.sid
        #data = cpv2.get_redirect_msg(data)
        msg = driver.create_local_task_message('bd.sd.@CPv2.redirect', data)
        driver.inbox.put(msg)


    @staticmethod
    @socketio.on('past')
    def socket_on_past(data):
        data['sid'] = request.sid

        keys = data.keys()
        if 'obj_type' in keys:
            cpv2.send_past_objs(data)
            return


        cpv2.send_past_updates(request.sid)


    @staticmethod
    @socketio.on('warehouse/get')
    def socket_on_warehouse_get(data):
        data['sid'] = request.sid
        data['uuid'] = driver.uuid
        driver.add_global_task("bd.sd.@WCv2.model.get", data, 'Getting rows', create_job=True, timeout=30)




driver.start()
