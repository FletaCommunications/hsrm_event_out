import re
a="[{1}][{2}] {3} {5} {6}"

aa=re.findall('\{\d\}',a)
print (aa)


for arg in aa:

    arg=arg.replace('}','')
    arg=arg.replace('{','')
    print(re.search('\d',arg).group())



bb='[2022-09-30 00:02:25][00000000001002ALJ5EM][SWI.MON.SFP.RX.I4][Warning][[2022-09-30 00:02:25][Warning][SFP RX][N/A (1002ALJ5EM)][Index:4,Slot:N/A,Port:4] SFP Rx Power 461.2uW [Port Speed:8, Threshold:500uW], Linked Devices : [SVR] FLETA-ESXI1,FLETA-ESXI2  [STG] 200A0828B1A(N/A)]'
msg_format = "[{1}][{2}][{3}][{5}][{6}]"


print(re.findall('\[',bb))