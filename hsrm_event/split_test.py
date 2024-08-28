import re
str="[2022-08-31 00:00:35][Warning][SFP TX][N/A (1002ALJ5EM)][Index:5,Slot:N/A,Port:5] SFP Tx Power 455.0uW [Port Speed:8, Threshold:500uW], Linked Devices : [SVR] FLETA-ESXI1,FLETA-ESXI2  [STG] 200A0828B1A(N/A)"
str="[2023-11-21 00:04:29][Critical][SFP RX][N/A (JAF1542CERT)][Index:fc1/4,Slot:1,Port:4] SFP Rx Power 484.17uW [Port Speed:8, Threshold:590uW], Linked Devices : [STG] 200A0828B1A(N/A)"
print(str)
ret=str.split(']')
print(ret)


dt = ret[0].replace('[','')
level = ret[1].replace('[','')
dev = ret[2].replace('[','')
alias = ret[3].replace('[','').split()[0]
serial = ret[3].replace('[','').split()[1]
event_code = ''
msg = ']'.join(ret[4:])

print(dt,level,dev,alias,msg)


"""
#1: event_date 
#2: event_level 
#3 : 구분 (TX,RX)
#3: device_alias
#4: serial_number
#5: desc_summary
"""

event_format  = '[{3}] [{4}] {5}  {6} [{1}][{2}]'

evt_info = dict()
evt_info['arg_1'] = dt
evt_info['arg_2'] = level
evt_info['arg_3'] = dev
evt_info['arg_4'] = alias
evt_info['arg_5'] = serial
evt_info['arg_6'] = msg


msg = event_format

# print('format :',msg)
# print(evt_info)
fd = re.findall('\{\d\}', msg)
print(fd)
for arg in fd:
    print('arg : ',arg)
    arg_num = re.search('\d',arg).group()
    evt_arg = 'arg_{}'.format(arg_num)
    print(evt_arg)
    print(evt_info[evt_arg])
    tg_msg = evt_info[evt_arg]
    msg = msg.replace(arg,tg_msg)

print('',msg)

print(evt_info)