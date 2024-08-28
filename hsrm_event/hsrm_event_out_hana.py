'''
Created on 2012. 10. 12.
Modify on 2023-01-06
@author: muse
현재 시간 기준 마지막 쿼리 시간 부터 => lost seq_no 이후 로 쿼리 수정.
'''

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
import fleta_crypto
import smtplib
import ssl
from email.mime.text import MIMEText

class itsm_event():
    def __init__(self):
        self.now = datetime.datetime.now()
        self.seq_file = os.path.join('config','seq_no.txt')
        self.seq_no = self.get_seq_no()
        self.flogger = self.get_logger
        self.cfg = self.get_cfg()
        self.c_file = os.path.join('config','c_date.txt')
        self.fc = fleta_crypto.AESCipher('kes2719!')
        self.conn_string = self.get_conn_str()
        print(self.conn_string)

    def get_seq_no(self):

        if not os.path.isfile(self.seq_file):
            self.set_seq_no('1')
        with open(self.seq_file) as f:
            seq_no = f.read()
        return seq_no

    def set_seq_no(self,seq_no):
        with open(self.seq_file,'w') as fw:
            fw.write(str(seq_no))


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
        log_file = os.path.join('logs', self.now.strftime('%Y%m%d.log'))
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(u'%(asctime)s %(levelname)s ==> %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger




    def get_conn_str(self):
        ip = self.cfg.get('database', 'ip', fallback='localhost')
        user = self.cfg.get('database', 'user', fallback='webuser')
        dbname = self.cfg.get('database', 'dbname', fallback='qweb')
        passwd = self.cfg.get('database', 'password', fallback='qw19850802@')
        port = self.cfg.get('database', 'port', fallback='5432')
        if len(passwd) > 20:
            passwd = self.fc.decrypt(passwd)
            if isinstance(passwd, bytes):
                passwd = passwd.decode('utf-8')
        return "host='%s' dbname='%s' user='%s' password='%s' port='%s'" % (ip, dbname, user, passwd, port)

    def get_cfg(self):
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config','config.cfg')
        print(cfg_file,os.path.isfile(cfg_file))
        cfg.read(cfg_file)
        print(cfg.sections())
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

    def send_smtp(self, msg_content):
        smtp_host = self.cfg.get('smtp', 'smtp_host', fallback='smtp.fletacom.com')
        smtp_user = self.cfg.get('smtp', 'smtp_user', fallback='fleta@fletacom.com')
        smtp_passwd = self.cfg.get('smtp', 'smtp_passwd', fallback='fleta123')
        target_user = self.cfg.get('smtp', 'target_user', fallback='fleta@fletacom.com')
        target_user = self.cfg.get('smtp', 'target_user', fallback='fleta@fletacom.com')
        target_user = self.cfg.get('smtp', 'target_user', fallback='fleta@fletacom.com')
        smtp_title = self.cfg.get('smtp', 'smtp_title', fallback='[HSRM] Event Message')


        msg = MIMEText(msg_content)
        msg['Subject'] = smtp_title
        msg['To'] = smtp_user
        print(smtp_host)
        print(smtp_user)
        print(smtp_passwd)
        print(target_user)

        smtp = smtplib.SMTP(smtp_host, 587)
        smtp.ehlo()  # say Hello
        smtp.starttls()  # TLS 사용시 필요
        smtp.login(smtp_user, smtp_passwd)
        try:
            smtp.sendmail(smtp_user, target_user, msg.as_string())
            self.flogger.info('smtp send {} {}'.format(target_user, msg_content))
        except Exception as e:
            self.flogger.errot('smtp send error {} {}'.format(target_user, msg_content))
            self.flogger.error(str(e))
        print(msg.as_string())
        smtp.quit()
    def send_cmd(self,msg_info):
        """
        Warning : major
        Critical : critical

        :param msg_info:
        :return:
        """
        if msg_info['q_level'] == 'Warning':
            severity = 'major'
        elif msg_info['q_level'] == 'Critical':
            severity = 'critical'
        else:
            severity = 'major'
        cmd = 'opcmsg s={SEVERITY} a="{ALIAS}" o={DEVICE} msg_grp=FSRM msg_t="{MSG}"'.format(SEVERITY=severity, ALIAS=msg_info['alias'], DEVICE=msg_info['device'], MSG=msg_info['msg'])
        print(cmd)
        ret = os.popen(cmd).read()
        print(ret)
        self.flogger.info(cmd)
        self.flogger.info(ret)

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
        if '{SEQ_NO}' in q:
            q = q.replace('{SEQ_NO}',self.seq_no)
        print(q)
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
        seq_no = '1'

        for evt in q_list:
            evt_info = dict()
            for i in range(len(evt)):
                arg_num = i+1
                arg_msg = evt[i]
                if arg_msg == None:
                    arg_msg="None"
                evt_info['arg_{}'.format(str(arg_num))] = str(arg_msg).strip()
                seq_no = evt[-1]
            # evt_info = dict()
            # date_str = datetime.datetime.strftime(datetime.datetime.strptime(evt[0],'%Y-%m-%d %H:%M:%S'),'%Y%m%d%H%M%S')
            # evt_info['event_date']    = date_str
            # evt_info['serial_number'] = evt[1]
            # evt_info['event_code']    = evt[2]
            # evt_info['event_level']   = evt[3]
            # evt_info['q_event_level'] = evt[4]
            # evt_info['desc_summary']  = evt[5]
            evt_list.append(evt_info)
        if len(q_list) > 0:
            self.set_seq_no(seq_no)
        # print("seq no :",seq_no)
        return evt_list

    def event_test_list(self):
        with open('test.csv') as f:
            lines = f.readlines()
        evt_list = list()
        q_list = list()
        # for line in lines[1:]:
        #     print(line)
        #     evt = list()
        #     tmp = line.split(',')
        #     print(tmp)
        #     evt.append(tmp[0].strip())
        #     evt.append(tmp[1].strip())
        #     evt.append(tmp[2].strip())
        #     evt.append(tmp[3].strip())
        #     evt.append(tmp[4].strip())
        #     evt.append(tmp[5].strip())
        #     msg = ','.join(tmp[7:-1])
        #     msg = msg.replace('"','')
        #     msg = msg.strip()
        #     print(msg)
        #
        #     evt.append(','.join(tmp[7:-1]).strip())
        #
        #     evt.append(tmp[-1].strip())
        #
        #     q_list.append(evt)

        evt = list()
        evt.append('2023-12-06 9:02')
        evt.append('000000000BRW4012N002')
        evt.append('C3-1014')
        evt.append('warning')
        evt.append('Warning')
        evt.append('SWI')
        evt.append('000000000BRW4012N002')
        evt.append('C3-1014  Link Reset on Port S0,P45(26) vc_no=0 crd(s)lost=2 auto trigger.')
        evt.append('65799')
        q_list.append(evt)

        evt = list()
        evt.append('2023-12-06 09:47')
        evt.append('000000000BRW4012N002')
        evt.append('SWI.MON.CRC.I46')
        evt.append('Critical')
        evt.append('Critical')
        evt.append('SWI')
        evt.append('DR #0018')
        evt.append('[2023-12-06 09:47:00][Critical][CRC ERR][DWDM SAN #2 (BRW4012N002)][Index:46,Slot:N/A,Port:46] CRC ERR value changed (0->2), Linked Devices : ')
        evt.append('65803')
        q_list.append(evt)
        for evt in q_list:
            # evt = line.split(',')
            print(evt)
            evt_info = dict()
            for i in range(len(evt)):
                arg_num = i+1
                arg_msg = evt[i]
                if arg_msg == None:
                    arg_msg="None"
                evt_info['arg_{}'.format(str(arg_num))] = str(arg_msg).strip()
                seq_no = evt[-1].strip()
            # evt_info = dict()
            # date_str = datetime.datetime.strftime(datetime.datetime.strptime(evt[0],'%Y-%m-%d %H:%M:%S'),'%Y%m%d%H%M%S')
            # evt_info['event_date']    = date_str
            # evt_info['serial_number'] = evt[1]
            # evt_info['event_code']    = evt[2]
            # evt_info['event_level']   = evt[3]
            # evt_info['q_event_level'] = evt[4]
            # evt_info['desc_summary']  = evt[5]
            evt_list.append(evt_info)
        if len(q_list) > 0:
            self.set_seq_no(seq_no)
        print(evt_list)
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
        log_file = os.path.join('logs', self.now.strftime('%Y%m%d.log'))
        with open(log_file) as f:
            log_str = f.read()
        return log_str

    def get_arg_set(self,msg_format):
        fd=re.findall('\{\d\}',msg_format)
        return fd

    def get_swi_msg(self, msg):
        print(msg)
        print(type(msg))
        ret = msg.split(']')
        print("RET :",ret)

        """
        Memory Usage : 48.78% [Threshold:45%]
        [SFP TX][N/A (JAF1542CERT)][Index:fc1/4,Slot:1,Port:4] SFP Tx Power 466.66uW [Port Speed:8, Threshold:800uW], Linked Devices : N/A
        """
        dt = ret[0].replace('[', '')
        level = ret[1].replace('[', '')
        dev = ret[2].replace('[', '')
        if len(ret) > 3:

            alias = ret[3].replace('[', '').split('(')[0]
            serial = ret[3].replace('[', '').split('(')[1]
            serial = serial.replace(')','')
            descript = ']'.join(ret[4:])
        else:
            alias = 'None'
            serial = 'None'
            try:
                descript = ret[3]
            except:
                descript = ''

        evt_info = dict()
        evt_info['arg_1'] = dt
        evt_info['arg_2'] = level
        evt_info['arg_3'] = dev
        evt_info['arg_4'] = alias
        evt_info['arg_5'] = serial
        evt_info['arg_6'] = descript
        """
        #1: event_date 
        #2: event_level 
        #3 : 구분 (TX,RX)
        #3: device_alias
        #4: serial_number
        #5: desc_summary
        """
        swi_msg = self.cfg.get('common', 'swi_msg_format', fallback='[{3}][{4}][{5}]{6}[{1}][{2}]')
        fd = re.findall('\{\d\}', swi_msg)
        # print(fd)
        for arg in fd:
            # print('arg : ', arg)
            arg_num = re.search('\d', arg).group()
            evt_arg = 'arg_{}'.format(arg_num)
            # print(evt_arg)
            # print(evt_info[evt_arg])
            tg_msg = evt_info[evt_arg]
            swi_msg = swi_msg.replace(arg, tg_msg)
        print('# swi msg :',swi_msg)
        return swi_msg, alias

    def main(self):
        yd_date = self.now - datetime.timedelta(days=1)
        yd = yd_date.strftime('%Y-%m-%d')
        td = self.now.strftime('%Y-%m-%d')
        qcd,cd = self.get_cdate()
        evt_list = self.get_evt_list(yd, td, qcd)
        print('event count :', len(evt_list))
        print('event :', evt_list)
        log_str = self.get_log_str()
        swi_msg_bit = False
        swi_msg = str()
        msg_info = dict()
        #cmd = 'opcmsg s={SEVERITY} a={ALIAS} o={DEVICE} msg_grp=FSRM msg_t="{MSG}"'.format(SEVERITY=severity, ALIAS=msg_info['alias'], DEVICE=msg_info['device'], MSG=msg_info['msg'])
        for evt_info in evt_list:

            print('evt_info :',evt_info)
            msg_info['q_level'] = evt_info['arg_5']
            msg_info['alias'] = evt_info['arg_7']
            msg_info['device'] = evt_info['arg_6']

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

            event_format = self.cfg.get('common', 'msg_format', fallback='[{1}][{2}][{3}][{5}][{6}]')
            msg = event_format

            # print('format :',msg)
            # print(evt_info)
            fd = re.findall('\{\d\}', msg)
            # print(fd)
            for arg in fd:
                arg_num = re.search('\d',arg).group()
                evt_arg = 'arg_{}'.format(arg_num)
                tg_msg = str(evt_info[evt_arg]).strip()
                msg = msg.replace(arg,tg_msg)
                print('-'*40)
                print(evt_info['arg_6'])
                print(len(re.findall('\[',tg_msg)))
                msg_info['msg'] = evt_info['arg_8']
                if evt_info['arg_6'] == 'SWI' and  len(re.findall('\[',tg_msg)) > 2:
                    # print('#'*50)
                    # print(evt_info['arg_6'] == 'SWI')
                    # print(len(re.findall('\[',tg_msg)) > 2)
                    # print(evt_info['arg_6'])
                    # print(msg)
                    swi_msg_bit = True
                    swi_msg = tg_msg
                else:
                    swi_msg = evt_info['arg_7']

            # print(evt_info['event_date'])
            # msg = msg.replace('{1}', evt_info['event_date'])
            # print(msg)
            # msg = msg.replace('{2}', evt_info['serial_number'].strip())
            # msg = msg.replace('{3}', evt_info['event_code'].strip())
            # msg = msg.replace('{4}', evt_info['event_level'].strip())
            # msg = msg.replace('{5}', evt_info['q_event_level'].strip())
            # msg = msg.replace('{6}', evt_info['desc_summary'].strip())
            print('swi_msg_bit :',swi_msg_bit)
            if swi_msg_bit :
                """
                [2022-06-13 14:25:21][Critical][SFP RX][SAN 스위치 #43L10M (BRCALJ1943L10M)][Index:1,Slot:0,Port:1] SFP Rx Power 334.2uW [Port Speed:N16, Threshold:400uW], Linked Devices : [SVR] nfddbo02  [STG] CKM00155102948(스토리지 #102948)
                [SFP RX][N/A (JAF1542CERT)][Index:fc1/2,Slot:1,Port:2] SFP Rx Power 481.95uW [Port Speed:8, Threshold:590uW], Linked Devices : N/A
                """
                print(evt_info['arg_1'])
                print(evt_info['arg_5'])
                if not swi_msg[1:3] == '20':
                    print(evt_info['arg_1'])
                    print(evt_info['arg_5'])
                    swi_msg= "[{}][{}]{}".format(evt_info['arg_1'], evt_info['arg_5'], swi_msg)

                msg, alias = self.get_swi_msg(swi_msg)
                msg_info['alias'] = alias
                msg_info['msg'] = msg

            print(msg)
            if msg in log_str:
                self.flogger.error('dup mag : {}'.format(msg))
            else:
                self.flogger.info(msg)
                self.send_cmd(msg_info)
                #self.send_file(msg)
                # self.send_smtp(msg)
        # self.set_seq_no()
        print('-'*50)

if __name__=='__main__':
    itsm_event().main()
    # city = u'서울'
    # print(isinstance(city,str))
    # city1=city.encode('utf-8')
    # print(city1)
    # print(isinstance(city1,bytes))
    # print(city1.decode('utf-8'))