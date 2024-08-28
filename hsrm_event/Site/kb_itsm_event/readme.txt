KB ITSM Event 연동
exe : 실행파일 kb_itsm_event.exe
src : source => 추후 수정 필요할시 사용.

1. HSRM Event 발생시 KB ITSM System 과 socket 통신

2. query file : ./config/query.sql
    {YG} : yesterday
    {TD} : today
    {CD} : check date


       where
               log_date >= '{YD}'::date
               and log_date <= '{TD}'::date
               and q_event_level = 'Critical'
               --log_date >= '2022-03-01'::date  ==> 테스트 시 수정 사용
               --and log_date <= '2022-03-31'::date ==>  테스트 시 수정 사용
               --and q_event_level = 'Critical'
               and check_date >='{CD}' == 테스트 시 수정 사용

    * 어제 와 오늘 파티션 테이블 에서 마지막 check date 이후에 발생한 이벤트 수집.

3. config.cfg
[database]  ==> HSRM Postgresql 접속정보.


[message]
req_emp = 5011815   ==> KB 담당자 직원 번호.
req_src1 = HSRM     ==> app 코드 값.
req_src2 = HSRM     ==> 프로그램 명.
req_dev = NA        ==> 요청구분키 / ID / 근거 => 없으면 NA


4. log
    ./logs/yyyymmdd.log 의 형태로 발생한 이벤트 loggin



5. ./config/c_date.txt => 마지막 check date
    ib_itsm_event.exe 실행시 check date 이후에 발생항 이벤트 만 쿼리.
