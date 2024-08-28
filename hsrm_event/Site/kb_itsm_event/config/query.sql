select
       event_date ,
       telephone,
       serial_number dev_serial,
       view.device_alias_zero(serial_number) dev_alias,
       device_type ,
       vendor_name ,
       desc_summary
from
       (
       select
               event_date ,
               serial_number ,
               device_type ,
               vendor_name ,
               desc_summary
       from
               "event".event_log el
       where
               log_date >= '{YD}'::date
               and log_date <= '{TD}'::date

               --log_date >= '2022-03-01'::date
               --and log_date <= '2022-03-31'::date

               and q_event_level = 'Critical'
               --and check_date >='{CD}'
)kk1
left join (
       select
               kk1.*,
                      replace(cellphone, '-', '') telephone
       from
               (
               select
                      stg_serial dev_serial,
                             trim(unnest(string_to_array(temp_2, '/'))) user_name
               from
                      master.master_stg_add_info msai
       union all
               select
                      swi_serial,
                             trim(unnest(string_to_array(temp_2, '/'))) user_name
               from
                      master.master_swi_add_info msai
       )kk1
       left join "member".member_info kk2
       on
               kk1.user_name = kk2.user_name
               or kk1.user_name = kk2.user_id
       where
               kk2.cellphone is not null
)kk2 on
       kk1.serial_number = kk2.dev_serial
where
       kk2.dev_serial is not null
order by
       1,
       3
