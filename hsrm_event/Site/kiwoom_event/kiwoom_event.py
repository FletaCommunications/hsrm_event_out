import psycopg2
import cx_Oracle
import datetime
import socket
import json
import sys
import configparser
import os
import logging
from logging.handlers import TimedRotatingFileHandler

os.putenv('NLS_LANG', '.UTF8')

class itsm_event():
    def __init__(self):
        self.now = datetime.datetime.now()
        self.flogger = self.get_logger
        self.cfg = self.get_cfg()
        self.conn_string = self.get_conn_str()
        print(self.conn_string)
        self.c_file = os.path.join('config','c_date.txt')
        self.oracle_path()
        self.seq_file = os.path.join('config', 'seq_no.txt')
        self.user_tel_list = self.get_user_tels()


    def get_seq_no(self):
            if not os.path.isfile(self.seq_file):
                self.set_seq_no('1')
            with open(self.seq_file) as f:
                seq_no = f.read()
            return seq_no

    def set_seq_no(self,seq_no):
        with open(self.seq_file,'w') as fw:
            fw.write(str(seq_no))

    def get_user_tels(self):
        user_tel_list = list()
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config', 'users.cfg')
        cfg.read(cfg_file,encoding="UTF-8")
        for user in cfg.sections():
            user_tel_list.append(cfg.get(user,'tel',fallback=''))
        return user_tel_list

    def oracle_path(self):
        oracle_path = self.cfg.get('oracle','oracle_client_path')
        os.environ['PATH'] = '{};{}'.format(oracle_path,os.environ['PATH'])

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

    def send_oracle(self,msg):

        msg = msg.replace("'","`")

        print(msg)
        title = self.cfg.get('message','title',fallback='title = HSRM Event Massage')
        callback = self.cfg.get('message','callback',fallback='02-2644-2241')
        oracle_ip = self.cfg.get('oracle', 'oracle_ip')
        oracle_sid = self.cfg.get('oracle', 'oracle_sid')
        oracle_port = self.cfg.get('oracle', 'oracle_port')
        oracle_user = self.cfg.get('oracle', 'oracle_user')
        oracle_password = self.cfg.get('oracle', 'oracle_password')

        connStr = "{}/{}@{}:{}/{}".format(oracle_user,oracle_password,oracle_ip,oracle_port,oracle_sid)
        print(connStr)
        # connection = cx_Oracle.connect(conn_str)
        # cursor = connection.cursor()
        # connStr = 'fleta/fleta123@121.170.193.203:1522/ORCL'
        connection = cx_Oracle.connect(connStr)
        cursor = connection.cursor()
        log_str = self.get_log_str()
        for user_tel in self.user_tel_list:
            sql = """INSERT INTO em_mmt_tran(
            mt_pr,
            date_client_req,
            subject,
            content,
            attach_file_group_key,
            callback,
            service_type,
            broadcast_yn,
            msg_status,
            recipient_num
        ) 
        values 
        (
            sq_em_mmt_tran_01.nextval,
            sysdate,
            '{SUBJECT}',
            '{CONTENT}',
            '0',
            '{CALLBACK}',
            '3',
            'N',
            '1',
            '{TEL}')
            """.format(SUBJECT=title,CONTENT=msg,CALLBACK=callback,TEL=user_tel)
            print(sql)
            dub_bit = self.cfg.get('common', 'dub_check', fallback='y')
            # if dub_bit == 'y':
            #     if msg in log_str:
            #         self.flogger.error('dup mag : {}'.format(msg))
            #     else:
            #         self.flogger.info(msg)
            #         cursor.execute(sql)
            # else:
            #     self.flogger.info(msg)
            #     cursor.execute(sql)

            self.flogger.info(msg)
            cursor.execute(sql)
        connection.commit()

    def send_sqlplus(self,msg):

        msg = msg.replace("'","`")

        print(msg)
        title = self.cfg.get('message','title',fallback='title = HSRM Event Massage')
        callback = self.cfg.get('message','callback',fallback='02-2644-2241')
        oracle_ip = self.cfg.get('oracle', 'oracle_ip')
        oracle_sid = self.cfg.get('oracle', 'oracle_sid')
        oracle_port = self.cfg.get('oracle', 'oracle_port')
        oracle_user = self.cfg.get('oracle', 'oracle_user')
        oracle_password = self.cfg.get('oracle', 'oracle_password')
        dup_bit = False
        print(self.user_tel_list)
        if os.path.isfile('event.sql'):
            os.remove('event.sql')
        for user_tel in self.user_tel_list:
            with open('event.sql','w',encoding='utf8') as f:
                sql = str()
                sql = """INSERT INTO em_mmt_tran(
                mt_pr,
                date_client_req,
                subject,
                content,
                attach_file_group_key,
                callback,
                service_type,
                broadcast_yn,
                msg_status,
                recipient_num
            ) 
            values 
            (
                sq_em_mmt_tran_01.nextval,
                sysdate,
                '{SUBJECT}',
                '{CONTENT}',
                '0',
                '{CALLBACK}',
                '3',
                'N',
                '1',
                '{TEL}');
                """.format(SUBJECT=title,CONTENT=msg,CALLBACK=callback,TEL=user_tel)
                print(sql)
                log_data = '{MSG}, SEND NUM :{TEL}'.format(MSG=msg,TEL=user_tel)
                log_str = self.get_log_str()
                if log_data in log_str:
                    self.flogger.error('dup mag : {}'.format(log_data))
                    dup_bit = True
                else:
                    self.flogger.info(log_data)
                    f.write(sql)

        #
        #cmd = 'sqlplus fleta/fleta123@121.170.193.203:1522/ORCL < event.sql'
        if not dup_bit:
            cmd = 'sqlplus {ORA_USER}/{ORA_PASS}@{ORA_IP}:{ORA_PORT}/{ORA_SID} < event.sql'.format(ORA_USER=oracle_user,ORA_PASS=oracle_password,ORA_IP=oracle_ip,ORA_PORT=oracle_port,ORA_SID=oracle_sid)
            print(cmd)
            print(os.popen(cmd).read())

    def send(self,msg):
        log_str = self.get_log_str()
        if msg in log_str:
            self.flogger.error('dup mag : {}'.format(msg))
        else:
            self.flogger.info(msg)
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

    def get_evt_list(self):
        """
        evt = {'datetime':'20220399120000', 'dev': 'STG', 'serial': '20924', 'message': 'Test event from HSRM', "tel_num": '01042420660'}
        evt_list.append(evt)

        :return:
        """
        # yd='2022-06-12'
        # td='2022-06-13'
        # cd='2022-06-13 00:00:00'
        evt_list = list()
        q_file = os.path.join('config','query1.sql')
        with open(q_file) as f:
            q=f.read()
        # q = q.replace('{YD}',yd)
        # q = q.replace('{TD}',td)
        # q = q.replace('{CD}',cd)
        seq_no = self.get_seq_no()
        q = q.replace('{SEQ_NO}', seq_no)
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
        device_type ,
        al.device_alias,
        vendor_name ,
        desc_summary,
        event_code,
        seq_no
        
       event_date ,
       serial_number ,
       device_type ,
       view.device_alias_zero(serial_number) dev_alias,
       vendor_name ,
       desc_summary,
       event_code
        """
        for evt in q_list:
            print(evt)
            print(evt[0])
            evt_info = dict()
            # date_str = datetime.datetime.strftime(datetime.datetime.strptime(evt[0],'%Y-%m-%d %H:%M:%S'),'%Y%m%d%H%M%S')
            print(evt[0])
            try:
                ed = datetime.datetime.strptime(evt[0].strip(),'%Y-%m-%d %H:%M:%S')
                date_str = datetime.datetime.strftime(ed,'%Y%m%d%H%M%S')
                # date_str=evt[0].strip()
                print(date_str)
                evt_info['event_date'] = date_str
                evt_info['dev_serail'] = evt[1]
                evt_info['dev_alias'] = evt[2]
                evt_info['dev_type'] = evt[3]
                evt_info['dev_vedor'] = evt[4]
                evt_info['evt_desc'] = evt[5]
                evt_info['evt_code'] = evt[6]
                evt_info['seq_no'] = evt[-1]
                evt_list.append(evt_info)
            except Exception as e:
                print(str(e))
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

    def main(self):
        yd_date = self.now - datetime.timedelta(days=1)
        yd = yd_date.strftime('%Y-%m-%d')
        td = self.now.strftime('%Y-%m-%d')
        qcd,cd = self.get_cdate()
        evt_list = self.get_evt_list()

        print('event count :',len(evt_list))

        req_info = self.get_req()
        self.flogger.debug('yd : {}, td: {}, cd: {}, qcd: {}, count:{}'.format(yd, td, cd, qcd, str(len(evt_list))))

        for evt in evt_list:
            print(evt)
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
            evt_date = evt['event_date'].strip()
            evt_dev = evt['dev_type'].strip()
            if evt['dev_alias'] == None:
                evt_alias = ""
            else:
                evt_alias = evt['dev_alias'].strip()
            evt_msg = evt['evt_desc'].strip()
            seq_no = evt['seq_no']
            print('seq_no ',seq_no)
            try:
                evt_code = evt['evt_code'].strip()
            except:
                evt_code = ""
            evt_serail = evt['dev_serail'].strip()

            desc ="[{}][{}][{}]{}".format(evt_dev,evt_serail,evt_code,evt_msg)
            send_method = self.cfg.get('common','send_method',fallback='sqlplus')

            self.send_oracle(desc)

            #
            # if send_method == 'socket':
            #     self.send(desc)
            # elif send_method == 'cx_oracle':
            #     self.send_oracle(desc)
            # else:
            #     self.send_sqlplus(desc)
        if len(evt_list) > 0:
            self.set_seq_no(seq_no)

        # self.set_cdate()
        print('-'*50)
    def smstest(self):
        sql="""INSERT INTO em_mmt_tran(
            mt_pr,
            date_client_req,
            subject,
            content,
            attach_file_group_key,
            callback,
            service_type,
            broadcast_yn,
            msg_status,
            recipient_num
        ) 
        values 
        (
            sq_em_mmt_tran_01.nextval,
            sysdate,
            'HSRM Event Massage',
            '[STG][21722004158][N/A]base service internal error',
            '0',
            '02-2644-2241',
            '3',
            'N',
            '1',
            '01094259343')
        """
        title = self.cfg.get('message', 'title', fallback='title = HSRM Event Massage')
        callback = self.cfg.get('message', 'callback', fallback='02-2644-2241')
        oracle_ip = self.cfg.get('oracle', 'oracle_ip')
        oracle_sid = self.cfg.get('oracle', 'oracle_sid')
        oracle_port = self.cfg.get('oracle', 'oracle_port')
        oracle_user = self.cfg.get('oracle', 'oracle_user')
        oracle_password = self.cfg.get('oracle', 'oracle_password')
        connStr = "{}/{}@{}:{}/{}".format(oracle_user, oracle_password, oracle_ip, oracle_port, oracle_sid)
        print(connStr)
        connection = cx_Oracle.connect(connStr)
        cursor = connection.cursor()
        print(sql)
        cursor.execute(sql)

        connection.commit()

    def test(self):
        seq_no = self.get_seq_no()
        print('seq_no :',seq_no)
        self.set_seq_no(seq_no)
if __name__=='__main__':
    # itsm_event().seq_test()


    itsm_event().main()


    # city = u'서울'
    # print(isinstance(city,str))
    # city1=city.encode('utf-8')
    # print(city1)
    # print(isinstance(city1,bytes))
    # print(city1.decode('utf-8'))