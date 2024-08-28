# hsrm_event
event 통합 공통 모듈


hsrm_event_out.py or hsrm_event_out.exe

event_log 에서 읽어와 target 파일에 add


config/config.cfg

[common]
event_file = E:\Fleta\eventout.txt
#1: event_date yyyymmddss
#2: serial_number
#3: event_code
#4: event_level , vender event level
#5: q_event_level , hsrm event level
#6: device_type
#7: device_alias
#8: desc_summary
#[2022-09-26 00:00:53][Critical][SFP RX][N/A (JAF1542CERT)][Index:fc1/2,Slot:1,Port:2] SFP Rx Power 493.17uW [Port Speed:8, Threshold:500uW]
#[2022-09-30 00:02:25][Warning][SFP RX][N/A (1002ALJ5EM)][Index:4,Slot:N/A,Port:4] SFP Rx Power 461.2uW [Port Speed:8, Threshold:500uW], Linked Devices : [SVR] FLETA-ESXI1,FLETA-ESXI2  [STG] 200A0828B1A(N/A)

msg_format = [{1}][{5}][{6}][{7}({2})][{8}]

msg_format 의 number 는 ./config/query.sql 에서 걸러지는 쿼리의 순서

1 = event_date ,2=serial_number 의 col 로 치환 되어 event_file 엣 적재됨.

20221007 수정.

SELECT
event_date,
serial_number,
event_code,
event_level,
q_event_level ,
device_type ,
al.device_alias,
desc_summary
FROM EVENT.event_log el LEFT JOIN
 (
    SELECT stg_serial ss, stg_alias device_alias FROM master.master_stg_info msi
    UNION ALL
    SELECT nas_name ss,nas_alias device_alias FROM master.master_nas_info mni
    UNION ALL
    SELECT swi_serial ss,swi_serial device_alias FROM master.master_swi_info
) al
ON el.serial_number = al.ss


nas,storage,switch 의 alias 컬럼 추가.


20221118 수정
메세지 한글 포함 또는 config/config.cfg 에 한글 포함 일때 에러 패치.

20231124 수정

swi message 의 경우 desc 에 
의 형태로 모든 메세지가 담겨 있음.

메세지 파싱후 조합 가능
#1: event_date
#2: event_level
#3 : SFP TX/SFP RX/ CRC/
#3: device_alias
#4: serial_number
#5: desc_summary
swi_msg_format = [{3}] [{4}] {5}  {6} [{1}][{2}]
example) 
[2023-11-24 00:01:04][Critical][SFP RX][N/A (ALJ2503G08G)][Index:5,Slot:N/A,Port:5] SFP Rx Power 407.7uW [Port Speed:8, Threshold:500uW], Linked Devices : [N/A] N/A(N/A)
[SFP RX] [N/A] (ALJ2503G08G)  [Index:5,Slot:N/A,Port:5] SFP Rx Power 407.7uW [Port Speed:8, Threshold:500uW], Linked Devices : [N/A] N/A(N/A) [2023-11-24 00:01:04][Critical]


2023-12-12 수정
1. swi message 이면서 snmp 로 받은 문자열 처리.
2. alias 에 공백이 있을때 짤리는 현상 patch

20240401 수정

"""
[2022-06-13 14:25:21][Critical][SFP RX][SAN 스위치 #43L10M (BRCALJ1943L10M)][Index:1,Slot:0,Port:1] SFP Rx Power 334.2uW [Port Speed:N16, Threshold:400uW], Linked Devices : [SVR] nfddbo02  [STG] CKM00155102948(스토리지 #102948)
[SFP RX][N/A (JAF1542CERT)][Index:fc1/2,Slot:1,Port:2] SFP Rx Power 481.95uW [Port Speed:8, Threshold:590uW], Linked Devices : N/A
"""
event_log 의 description message 포멧 변경으로 인한 swi_msg 포멧 변경.
기존 처럼 [시간][등급] 으로 메세지 연동은
swi_msg_format = [{1}][{2}] [{3}] [{4}] {5}  {6}

config.cfg 
#1: event_date
#2: event_level
#3 : SFP TX/SFP RX/ CRC/
#3: device_alias
#4: serial_number
#5: desc_summary
#[SFP TX] [N/A] (1002ALJ5EM)  [Index:5,Slot:N/A,Port:5] SFP Tx Power 455.0uW [Port Speed:8, Threshold:500uW], Linked Devices : [SVR] FLETA-ESXI1,FLETA-ESXI2  [STG] 200A0828B1A(N/A) [2022-08-31 00:00:35][Warning]

swi_msg_format = [{3}] [{4}] {5}  {6} # 시간 등급 제외한 메세지 연동.



2024--04-12 하나증권 패치
opcmsg s=critical a=00000000001002ALJ5EM  o=SWI msg_grp=FSRM msg_t="[2024-03-26 16:19:57] [ [Memory Usage : 47.32% [Threshold:45%]] Stop monitoring, Cuase : High Memory Usage]"

