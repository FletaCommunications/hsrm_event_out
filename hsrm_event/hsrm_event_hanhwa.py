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
import subprocess
import time


class itsm_event():
    def __init__(self):
        self.now = datetime.datetime.now()
        self.flogger = self.get_logger
        self.cfg = self.get_cfg()
        self.conn_string = self.get_conn_str()
        print(self.conn_string)
        self.c_file = os.path.join('config', 'c_date.txt')
        os.environ['PATH'] = '.\\curl\\bin;{}'.format(os.environ['PATH'])

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
        ip = self.cfg.get('database', 'ip')
        user = self.cfg.get('database', 'user')
        dbname = self.cfg.get('database', 'dbname')
        password = self.cfg.get('database', 'password')
        port = self.cfg.get('database', 'port', fallback=5432)
        return "host='{}' dbname='{}' user='{}' password='{}' port ='{}'".format(ip, dbname, user, password, port)

    def get_cfg(self):
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config', 'config.cfg')
        print(cfg_file, os.path.isfile(cfg_file))
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

    def get_user(self):
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config', 'user.cfg')
        cfg.read(cfg_file, encoding='utf-8')
        user_list = list()
        for sec in sorted(set(cfg.sections())):
            user_info = dict()
            for opt in cfg.options(sec):
                user_info[opt] = cfg.get(sec, opt)
            user_list.append(user_info)
        return user_list

    def format_time(self, date_str='now'):
        print('data_str :', date_str)
        if date_str == 'now':
            t = datetime.datetime.now()
            s = t.strftime('%Y%m%d%H%M%S%f')
            return_date = s[:-3]
        else:
            return_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%Y%m%d%H%M%S000')
        return return_date

    def get_ip_12(self):
        ipaddr = self.cfg.get('server', 'ip', fallback="localhost")
        ch_list = '.'.split(ipaddr)
        ip_chr = str()
        for ch in ch_list:
            ip_chr = ip_chr + ch.rjust(3, '0')
        return ip_chr

    def make_json(self, msg_info, user_info):
        """
        20221012
        hanwha life
        :param msg_info:
        :return: result

        "hpTlphSbno":"7964",
        "ntfcKindCode":"ZAU9001", <== serial 추정
        "ntfcTmplCode":"ACC00214", <== event_code 추정
        "hpTlphTlcmNo":"010",  <==
        "jobMsgeCntn":"[한화생명] 보험료 납입 관련 안내전화 예정.", <== message 내용
        "msgeTitlNm":"[한화생명] 보험료 미납 안내전화 예정", >== message title
        "hpTlphOfno":"4726",
        "trnmSysCode":"MLO",
        "ipAddr":"010001054042",
        "rqstDttm":"20220622171355506",  <== 이벤트 발생시간
        "rqsrIp":"10.19.19.38",  <== 보내는 IP
        "serverType":"P",
        "tlgrCretDttm":"20220622171355506", <== 이벤트 전송시간.
                        YYYYMMDDHHMMSS
                        20221012171610364
        "itfcId":"HLIMLO00005",
        """

        json_str = """
{
	"payload": {
		"hpTlphSbno":"0660",
		"tmplCode":"NC1067",
		"dutySendYn":"Y",
		"sndeDeptCode":"139",
		"sendCont":"1",
		"btchPrcsYn":"1",
		"hpTlphTlcmNo":"010",
		"sbsnSendMsgeCntn":"hlinxmax(Maxgauge",
		"nttkButnCntn":"",
		"custId":"0000099995",
		"hpTlphOfno":"4242",
		"sndeTlphArcd":"",
		"sndeTlphOfno":"1588",
		"ntfcKindCode":"ZAF9001",
		"trnnPrgmId":"",
		"sendRsvtDttm":"",
		"sbsnSendYn":"Y",
		"ntfcTmplCode":"AZZ00005",
		"jobMsgeCntn":"hlinxmax(Maxgauge ",
		"onlnBtchDvsnCode":"R",
		"sndeTlphInno":"6363",
		"msgeTitlNm":"test",
		"butnDvsnCode":"",
		"ntfcMdiaDvsnCode":"SMS",
		"rcvrNm":""
		}, 

	"header": {
		"rspnDvsnCode":"S",
		"rndmNo":"0936",
		"trnmSysCode":"ONT",
		"rcveSrvcId":"iniCspdDvlmUmsSendMgmtPSI004c",
		"ipAddr":"010010008082",
		"rcveSysCode":"INI",
		"ogtsTrnnNo":"",
		"prsnInfoIncsYn":"Y",
		"mciSesnId":"",
		"serverType":"P",
		"tlgrCretDttm":"20221025095223649",
		"ctfnTokn":"",
		"itfcId":"HLIONT00010",
		"hsno":"1",
		"mciNodeNo":""
	}
}

"""

        rqstDttm = self.format_time(msg_info['event_date'])
        tlgrCretDttm = self.format_time("now")

        json_data = json.loads(json_str)

        tel_list = user_info['phone'].split('-')

        json_data['payload']['hpTlphSbno'] = tel_list[2]
        json_data['payload']['hpTlphOfno'] = tel_list[1]
        json_data['payload']['sbsnSendMsgeCntn'] = msg_info['msg_desc'][:89]
        json_data['payload']['jobMsgeCntn'] = msg_info['msg_desc']
        json_data['header']['tlgrCretDttm'] = rqstDttm

        json_file = '.\send_json.json'

        with open(json_file, 'w', encoding='utf-8') as fw:
            fw.write(json.dumps(json_data, ensure_ascii=False))
        return json.dumps(json_data, ensure_ascii=False)

    def set_msg_info(self, evt_info):
        # {'arg_1': '2022-10-12 16:42:01', 'arg_2': '00000000000000011543', 'arg_3': '7E0518', 'arg_4': 'Moderate', 'arg_5': 'Warning', 'arg_6': 'STG', 'arg_7': 'None', 'arg_8': 'Error test Message.[PORT:1F]', 'msg_desc': '[2022-10-12 16:42:01][Warning][STG][None(00000000000000011543)][Error test Message.[PORT:1F]]'}
        msg_info = dict()
        msg_info['event_date'] = evt_info['arg_1']
        msg_info['serial_number'] = evt_info['arg_2']
        msg_info['event_code'] = evt_info['arg_3']
        msg_info['event_level'] = evt_info['arg_4']
        msg_info['q_event_level'] = evt_info['arg_5']
        msg_info['device_type'] = evt_info['arg_6']
        msg_info['device_alias'] = evt_info['arg_7']
        msg_info['msg_desc'] = evt_info['msg_desc']
        return msg_info

    def send_https(self, evt_info):
        msg_info = self.set_msg_info(evt_info)

        user_list = self.get_user()
        json_file = '.\send_json.json'
        # json_file = '.\hanhwa_sample.json'
        base_url = self.cfg.get('http', 'url')

        for user_info in user_list:
            print('-' * 50)
            print('user:', user_info)
            msg_info['user_phone'] = user_info['phone']
            json_str = self.make_json(msg_info, user_info)
            time.sleep(0.5)
            cmd = 'curl -X POST -H "Content-Type: application/json" {BASE_URL} -d@{JSON_FILE}'.format(BASE_URL=base_url,
                                                                                                      JSON_FILE=json_file)
            # cmd = 'curl -X POST -H "Content-Type: application/json" {BASE_URL} -d{JSON_FILE}'.format(BASE_URL=base_url,JSON_FILE=json_str)
            print(cmd)

            subprocess.Popen(cmd)
            with open(json_file, encoding='utf-8') as f:
                json_str = f.read()
            self.flogger.debug(json_str)
            time.sleep(1)

    def send_file(self, msg):
        event_file = self.cfg.get('common', 'event_file')
        try:
            with open(event_file, 'a') as fw:
                fw.write(msg)
                fw.write('\n')
        except Exception as e:
            self.flogger.error(str(e))
            print(str(e))

    def send_socket(self, msg):
        """
        [itsm]
        itsm_ip = 121.170.193.222
        itsm_port = 3264
        :return:
        """
        host = self.cfg.get('itsm', 'itsm_ip', fallback='127.0.0.1')
        port = self.cfg.get('itsm', 'itsm_port', fallback=3264)
        port = int(port)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # Connect to server and send data
            sock.connect((host, port))
            if isinstance(msg, str):
                msg = msg.encode()
            sock.sendall(msg)
        except socket.error as e:
            self.flogger.error(str(e))
        finally:
            sock.close()

    def get_evt_list(self, yd, td, cd):
        """
        evt = {'datetime':'20220399120000', 'dev': 'STG', 'serial': '20924', 'message': 'Test event from HSRM', "tel_num": '01042420660'}
        evt_list.append(evt)
        :param yd:
        :param td:
        :param cd:
        :return:
        """
        evt_list = list()
        q_file = os.path.join('config', 'query.sql')
        with open(q_file) as f:
            q = f.read()
        q = q.replace('{YD}', yd)
        q = q.replace('{TD}', td)
        q = q.replace('{CD}', cd)
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
                arg_num = i + 1
                arg_msg = evt[i]
                if arg_msg == None:
                    arg_msg = "None"
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
            req_info[opt] = self.cfg.get('message', opt)
        return req_info

    def get_1min_date(self, cdate):
        cd_t = datetime.datetime.strptime(cdate, '%Y-%m-%d %H:%M:%S')
        qcd = cd_t - datetime.timedelta(minutes=1)
        return qcd.strftime('%Y-%m-%d %H:%M:%S')

    def get_cdate(self):
        cd = self.now - datetime.timedelta(days=1)
        cdate = cd.strftime('%Y-%m-%d %H:%M:%S')
        if os.path.isfile(self.c_file):
            with open(self.c_file) as f:
                cdate = f.read()
        qcdate = self.get_1min_date(cdate)
        # date 변수 셋팅
        self.set_cdate()
        return qcdate, cdate

    def set_cdate(self):
        with open(self.c_file, 'w') as fw:
            fw.write(self.now.strftime('%Y-%m-%d %H:%M:%S'))

    def get_log_str(self):
        log_file = os.path.join('logs', self.now.strftime('%Y%m%d.log'))
        with open(log_file) as f:
            log_str = f.read()
        return log_str

    def get_arg_set(self, msg_format):
        fd = re.findall('\{\d\}', msg_format)
        return fd

    def hanhwa_msg(self, msg):
        evt_alias, evt_portnum, text = '', '', ''
        msg = msg.split('Linked Devices')[0]
        regex = '\[([^]]+)'
        text = re.sub(regex, '', msg)
        print(msg)
        print('text :', text)
        text = text.replace('[', '')
        text = text.replace(']', '')
        text = text.replace(',', '')
        print('text :', text)
        items = re.findall(regex, msg)
        try:
            evt_datetime = items[0]
            evt_severity = items[1]
            evt_device = items[2]
            evt_alias = items[3]
            # evt_alias = evt_alias.split('(')[0]
            evt_portnum = items[4]
            if 'SFP' in evt_device:
                evt_threshold = items[5]
                target_msg = """{ALIAS}의 {MSG}입니다.({PORT_NUM})""".format(ALIAS=evt_alias, PORT_NUM=evt_portnum,
                                                                         MSG=text)

            elif 'THROUGHPUT' in evt_device:
                evt_threshold = items[5]
                target_msg = """{ALIAS}의 {MSG}입니다.({PORT_NUM})""".format(ALIAS=evt_alias, PORT_NUM=evt_portnum,
                                                                         MSG=text)

            elif 'CRC' in evt_device:
                evt_threshold = ''
                target_msg = """{ALIAS}의 {MSG}입니다.({PORT_NUM})""".format(ALIAS=evt_alias, PORT_NUM=evt_portnum,
                                                                         MSG=text)
            else:
                target_msg = msg

        except Exception as e:
            target_msg = msg
            print(str(e))
        target_msg = target_msg[:89]
        return target_msg

    def main(self):
        yd_date = self.now - datetime.timedelta(days=1)
        yd = yd_date.strftime('%Y-%m-%d')
        td = self.now.strftime('%Y-%m-%d')
        qcd, cd = self.get_cdate()
        evt_list = self.get_evt_list(yd, td, qcd)

        print('event count :', len(evt_list))
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
            event_format = self.cfg.get('common', 'msg_format', fallback='[{1}][{2}][{3}][{5}][{6}]')
            msg = event_format

            # print('format :',msg)
            # print(evt_info)
            fd = re.findall('\{\d\}', msg)

            for arg in fd:
                arg_num = re.search('\d', arg).group()
                evt_arg = 'arg_{}'.format(arg_num)
                tg_msg = evt_info[evt_arg]
                msg = msg.replace(arg, tg_msg)
                if len(re.findall('\[', tg_msg)) > 2:
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

            # 20221129 dup check X
            if swi_msg_bit:
                msg = swi_msg
                msg = self.hanhwa_msg(msg)

            # 20221221 dup messege check
            self.flogger.info(swi_msg)
            evt_info['msg_desc'] = msg
            # self.send_https(evt_info)

            if swi_msg in log_str:
               self.flogger.error('dup mag : {}'.format(swi_msg))
            else:
               self.flogger.info(swi_msg)
               evt_info['msg_desc'] = msg
               self.send_https(evt_info)
            # self.send_file(msg)
        # self.set_cdate()
        print('#' * 50)


if __name__ == '__main__':
    itsm_event().main()
    # city = u'서울'
    # print(isinstance(city,str))
    # city1=city.encode('utf-8')
    # print(city1)
    # print(isinstance(city1,bytes))
    # print(city1.decode('utf-8'))