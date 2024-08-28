import configparser
import os
import datetime

class log_manager():
    def __init__(self):
        self.cfg = self.get_cfg()

    def get_cfg(self):
        cfg = configparser.RawConfigParser()
        cfg_file = os.path.join('config','config.cfg')
        cfg.read(cfg_file, encoding='utf-8')
        return cfg

    def get_last_month(self):
        today = datetime.date.today()
        first = today.replace(day=1)
        last_month = first - datetime.timedelta(days=1)
        print(last_month.strftime("%Y%m"))
        return last_month.strftime("%Y%m")

    def month_log_clear(self):
        log_file_name = self.cfg.get('common','event_file')
        last_month = self.get_last_month()
        if os.path.isfile(log_file_name):
            backup_file_name = log_file_name+'.{}'.format(last_month)
            if os.path.isfile(backup_file_name):
                os.rename(backup_file_name,backup_file_name+'.'+datetime.datetime.now().strftime('%y%m%d%H%M%S'))
            print('make file :',backup_file_name)
            os.rename(log_file_name,backup_file_name)

if __name__=='__main__':
    log_manager().month_log_clear()
