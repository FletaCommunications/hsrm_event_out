import fletaDbms

class event_out():
    def __init__(self):
        self.db=fletaDbms.FletaDb()
    
    
    def main(self):
        query="""select * from event.event_log
where serial_number not in (
   select target_dev_name serial_number from ref.ref_svr_event_prevent_setting_history 
   where start_time::date <= now() and end_time::date > now()
 ) and user_id = '' and check_date::date > now()::date + interval '-2 minutes' order by seq_no desc;
        """
        print query
        rows=self.db.getRaw(query)
        
        for row in rows:
            print row


if __name__=='__main__':
    event_out().main()    