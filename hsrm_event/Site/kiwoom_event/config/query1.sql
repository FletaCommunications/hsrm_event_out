-- log_date >= '{YD}'::date,
-- and log_date <= '{TD}'::date,
-- and q_event_level = 'Critical'
-- and check_date >='{CD}'

SELECT
       event_date ,
       serial_number ,
       al.device_alias dev_alias,
       device_type ,
       vendor_name ,
       desc_summary,
       event_code,
        seq_no
FROM EVENT.event_log el LEFT JOIN
 (
    SELECT stg_serial ss, stg_alias device_alias FROM master.master_stg_info msi
    UNION ALL
    SELECT nas_name ss,nas_alias device_alias FROM master.master_nas_info mni
    UNION ALL
    SELECT swi_serial ss,swi_serial device_alias FROM master.master_swi_info
) al
ON el.serial_number = al.ss
WHERE
    1=1
    --AND el.log_date >= '{YD}'::date
    --AND el.log_date <= '{TD}'::date
    --AND el.check_date >='{CD}'
    --and el.q_event_level = 'Critical'
    AND el.seq_no > '{SEQ_NO}'
order by seq_no asc