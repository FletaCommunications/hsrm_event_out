import psycopg2
import datetime
import socket
import json
import sys
import configparser
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import re

class itsm_event():
    def __init__(self):
        self.now = datetime.datetime.now()
        self.flogger = self.get_logger
        self.cfg = self.get_cfg()
        self.conn_string = self.get_conn_str()
        # print(self.conn_string)
        self.c_file = os.path.join('config','c_date.txt')



    @property
    def get_logger(self):
        if not os.path.isdir('logs'):
            os.makedirs('logs')
        formatter = logging.Formatter(u'%(asctime)s %(levelname)s ==> %(message)s')
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        stream_hander = logging.StreamHandler()
        stream_hander.setFormatter(formatter)
        logger.addHandler(stream_hander)
        log_file = os.path.join('logs',self.now.strftime('%Y%m%d.log'))
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(u'%(asctime)s %(levelname)s ==> %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger




    def get_conn_str(self):
        ip = self.cfg.get('database','ip')
        user = self.cfg.get('database','user')
        dbname = self.cfg.get('database','dbname')
        password = self.cfg.get('database','password')
        port = self.cfg.get('database','port',fallback=5432)
        return "host='{}' dbname='{}' user='{}' password='{}' port ='{}'".format(ip,dbname,user,password,port)

    def get_cfg(self):
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config','config.cfg')
        cfg.read(cfg_file,encoding='utf-8')
        return cfg

    def getRaw(self, query_string):
        # print(query_string)
        db = psycopg2.connect(self.conn_string)

        try:
            cursor = db.cursor()
            cursor.execute(query_string)
            rows = cursor.fetchall()

            cursor.close()
            db.close()

            return rows
        except Exception as e:
            self.flogger.error(str(e))
            return []

    def send_file(self,msg):
        event_file = self.cfg.get('common','event_file')
        try:
            with open(event_file,'a') as fw:
                fw.write(msg)
                fw.write('\n')
        except Exception as e:
            self.flogger.error(str(e))
            print(str(e))

    def send_socket(self,msg):
        """
        [itsm]
        itsm_ip = 121.170.193.222
        itsm_port = 3264
        :return:
        """
        host = self.cfg.get('itsm', 'itsm_ip', fallback='127.0.0.1')
        port = self.cfg.get('itsm', 'itsm_port', fallback=3264)
        port = int(port)
        print(host,port)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Connect to server and send data
            sock.connect((host, port))
            if isinstance(msg,str):
                msg=msg.encode()
            sock.sendall(msg)
        except socket.error as e:
            self.flogger.error(str(e))
        finally:
            sock.close()

    def get_evt_list(self,yd,td,cd):
        """
        evt = {'datetime':'20220399120000', 'dev': 'STG', 'serial': '20924', 'message': 'Test event from HSRM', "tel_num": '01042420660'}
        evt_list.append(evt)
        :param yd:
        :param td:
        :param cd:
        :return:
        """
        evt_list = list()
        q_file = os.path.join('config','query.sql')
        with open(q_file) as f:
            q=f.read()
        q = q.replace('{YD}',yd)
        q = q.replace('{TD}',td)
        q = q.replace('{CD}',cd)
        q_list = self.getRaw(q)
        """
        2022-03-04 09:20:55	01077778888	00000000000000011015	411015	STG	HITACHI	is a Error test code.[PORT:5E]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        2022-03-15 10:35:55	01077778888	00000000000000011536	11536	STG	HITACHI	is a Error test code.[PORT:5E]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          
        2022-03-15 10:35:55	01077778888	00000000000000011537	11537	STG	HITACHI	is a Error test code.[PORT:5E]
        """
        """
        event_date,
        serial_number,
        event_code,
        event_level,
        q_event_level ,
        desc_summary
        """

        for evt in q_list:
            evt_info = dict()
            for i in range(len(evt)):
                arg_num = i+1
                arg_msg = evt[i]
                if arg_msg == None:
                    arg_msg="None"
                evt_info['arg_{}'.format(str(arg_num))] = arg_msg.strip()

            # evt_info = dict()
            # date_str = datetime.datetime.strftime(datetime.datetime.strptime(evt[0],'%Y-%m-%d %H:%M:%S'),'%Y%m%d%H%M%S')
            # evt_info['event_date']    = date_str
            # evt_info['serial_number'] = evt[1]
            # evt_info['event_code']    = evt[2]
            # evt_info['event_level']   = evt[3]
            # evt_info['q_event_level'] = evt[4]
            # evt_info['desc_summary']  = evt[5]
            evt_list.append(evt_info)
        return evt_list

    def get_req(self):
        req_info = dict()
        for opt in self.cfg.options('message'):
            req_info[opt] = self.cfg.get('message',opt)
        return req_info

    def get_1min_date(self,cdate):
        cd_t=datetime.datetime.strptime(cdate,'%Y-%m-%d %H:%M:%S')
        qcd = cd_t - datetime.timedelta(minutes=1)
        return qcd.strftime('%Y-%m-%d %H:%M:%S')

    def get_cdate(self):
        cd = self.now - datetime.timedelta(days=1)
        cdate = cd.strftime('%Y-%m-%d %H:%M:%S')
        if os.path.isfile(self.c_file):
            with open(self.c_file) as f:
                cdate = f.read()
        qcdate = self.get_1min_date(cdate)
        #date 변수 셋팅
        self.set_cdate()
        return qcdate,cdate

    def set_cdate(self):
        with open(self.c_file,'w') as fw:
            fw.write(self.now.strftime('%Y-%m-%d %H:%M:%S'))
        print('check date  : ',self.now.strftime('%Y-%m-%d %H:%M:%S'))

    def get_log_str(self):
        log_file = os.path.join('logs',self.now.strftime('%Y%m%d.log'))
        with open(log_file) as f:
            log_str = f.read()
        return log_str

    def get_arg_set(self,msg_format):
        fd=re.findall('\{\d\}',msg_format)
        return fd



    def main(self):
        yd_date = self.now - datetime.timedelta(days=1)
        yd = yd_date.strftime('%Y-%m-%d')
        td = self.now.strftime('%Y-%m-%d')
        qcd,cd = self.get_cdate()
        evt_list = self.get_evt_list(yd, td, qcd)

        print('event count :',len(evt_list))
        """
        KB ITSM
        INFO  : 구분자
        2  : {1 :수신직원번소 , 2:수신전화번호, 3:수신App코드그룹, 6:ITSM정의수신코드} => 2번고정
        01012341234  : 수신대상자 (전화번호) event message 대상자.
        20220329120000 : 이벤트 발생시간.
        5011815 : 요청자 (KB 담당 직원번호)
        P : 발송타입 , 고정값
        HSRM : app code 값
        HSRM : 프로그램명
        NA : 요청구분키 / ID / 근거 => 없으면 NA
        [Serailnum] message 80byte 이하 SMS , 초과  LMS
        """

        """
        [messgae]
        req_emp = 5011815
        req_src1 = HSRM
        req_src2 = HSRM
        req_dev = NA

        """
        # req_info = self.get_req()
        self.flogger.debug('yd : {}, td: {}, cd: {}, qcd: {}, count:{}'.format(yd, td, cd, qcd, str(len(evt_list))))
        log_str = self.get_log_str()
        swi_msg_bit = False
        swi_msg = str()
        for evt_info in evt_list:
            """
            evt 
                1. 이벤트 발생시간
                2. SAN/STG
                3. 장비 serial
                4. 이벤트 내용\
            evt['event_date'] = evt[0]
            evt['tel_num'] = evt[1]
            evt['dev_serail'] = evt[2]
            evt['dev_alias'] = evt[3]
            evt['dev_vedor'] = evt[4]
            evt['evt_desc'] = evt[5]
            """
            # event_format = self.cfg.get('common', 'msg_format', fallback='[{1}][{2}][{3}][{5}][{6}]')
            event_format = self.cfg.get('common', 'msg_format')
            msg = event_format
            print('event format : ',event_format)
            # print('format :',msg)
            # print(evt_info)
            fd = re.findall('\{\d\}', msg)

            for arg in fd:
                arg_num = re.search('\d',arg).group()
                evt_arg = 'arg_{}'.format(arg_num)
                tg_msg = evt_info[evt_arg]
                msg = msg.replace(arg,tg_msg)
                if len(re.findall('\[',tg_msg)) > 2:
                    swi_msg_bit = True
                    swi_msg = tg_msg
            # print(evt_info['event_date'])
            # msg = msg.replace('{1}', evt_info['event_date'])
            # print(msg)
            # msg = msg.replace('{2}', evt_info['serial_number'].strip())
            # msg = msg.replace('{3}', evt_info['event_code'].strip())
            # msg = msg.replace('{4}', evt_info['event_level'].strip())
            # msg = msg.replace('{5}', evt_info['q_event_level'].strip())
            # msg = msg.replace('{6}', evt_info['desc_summary'].strip())


            if swi_msg_bit :
                msg = swi_msg.strip()
            else:
                msg = msg.strip()
            # msg = msg.strip() + '한글'
            print(msg)
            if msg in log_str:
                self.flogger.error('dup mag : {}'.format(msg))
            else:
                self.flogger.info(msg)
                self.send_file(msg)
        # self.set_cdate()
        print('-'*50)

if __name__=='__main__':
    itsm_event().main()
