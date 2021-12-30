#coding:utf-8
#
# id:           functional.monitoring.04
# title:        Monitoring: SYSDBA must see all attachments and their transactions, non-privileged user - only those which was of his login.
# decription:   
# tracker_id:   
# min_versions: []
# versions:     3.0
# qmid:         functional.monitoring.monitoring_04

import pytest
from firebird.qa import db_factory, python_act, Action

# version: 3.0
# resources: None

substitutions_1 = [('[=]{1,}', ''), ('[ \t]+', ' ')]

init_script_1 = """
    set wng off;
    create or alter user u01 password '123';
    create or alter user u02 password '456';
    commit;
    create or alter view v_who as
    select
        current_user as who_am_i
        ,a.mon$user who_else
        ,dense_rank()over(partition by a.mon$user order by t.mon$transaction_id) tid_rown
        ,t.mon$isolation_mode isol_mode
        -- 15.01.2019: removed detailed info about read committed TIL because of read consistency TIL that 4.0 introduces.
        -- Any record with t.mon$isolation_mode = 4 now is considered just as read committed, w/o any detalization (this not much needed here).
        ,decode( t.mon$isolation_mode, 0,'CONSISTENCY', 1,'SNAPSHOT', 2, 'READ_COMMITTED', 3, 'READ_COMMITTED', 4, 'READ_COMMITTED', '??' ) as isol_descr
    from 
        mon$attachments a 
        LEFT join mon$transactions t using(mon$attachment_id)
    where 
        a.mon$attachment_id is distinct from current_connection
        and a.mon$system_flag is distinct from 1 -- remove Cache Writer and Garbage Collector from resultset
    order by a.mon$user, t.mon$transaction_id;
    commit;

    revoke all on all from u01;
    revoke all on all from u02;
    grant select on v_who to u01;
    grant select on v_who to u02;
    commit;
  """

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# 
#  db_conn.close()
#  
#  #----------------------------------------------------------------------
#  
#  con_1 = fdb.connect(dsn=dsn, user=user_name, password=user_password )
#  con_2 = fdb.connect(dsn=dsn, user='U01', password='123')
#  con_3 = fdb.connect(dsn=dsn, user='U01', password='123')
#   
#  con_1.begin()
#  con_2.begin()
#  con_3.begin()
#  
#  #----------------------------------------------------------------------
#  
#  custom_tpb4 = fdb.TPB()
#  custom_tpb4.isolation_level = (fdb.isc_tpb_read_committed, fdb.isc_tpb_rec_version)
#  
#  custom_tpb5 = fdb.TPB()
#  custom_tpb5.isolation_level = fdb.isc_tpb_concurrency
#  
#  custom_tpb6 = fdb.TPB()
#  custom_tpb6.isolation_level = fdb.isc_tpb_consistency
#  
#  con_4 = fdb.connect(dsn=dsn, user='U02', password='456')
#  con_5 = fdb.connect(dsn=dsn, user='U02', password='456')
#  con_6 = fdb.connect(dsn=dsn, user='U02', password='456')
#  
#  con_4.begin( tpb = custom_tpb4 )
#  con_5.begin( tpb = custom_tpb5 )
#  con_6.begin( tpb = custom_tpb6 )
#  
#  sql_chk='''
#      set width who_am_i 12;
#      set width who_else 12;
#      set width isol_descr 30;
#      set count on;
#  
#      connect '$(DSN)' user 'u01' password '123';
#      select 1 as check_no, v.* from v_who v;
#      commit;
#  
#      connect '$(DSN)' user 'SYSDBA' password 'masterkey';
#  
#      select 2 as check_no, v.* from v_who v;
#      commit;
#  
#      drop user u01;
#      drop user u02;
#      commit;
#  '''
#  
#  runProgram('isql',[  '-pag','99999','-q' ], sql_chk)
#---
act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    CHECK_NO  WHO_AM_I     WHO_ELSE                  TID_ROWN ISOL_MODE  ISOL_DESCR
    1         U01          U01                              1         2  READ_COMMITTED
    1         U01          U01                              2         2  READ_COMMITTED
    Records affected: 2

    CHECK_NO  WHO_AM_I     WHO_ELSE                  TID_ROWN ISOL_MODE  ISOL_DESCR
    2         SYSDBA       SYSDBA                           1         2  READ_COMMITTED
    2         SYSDBA       U01                              1         2  READ_COMMITTED
    2         SYSDBA       U01                              2         2  READ_COMMITTED
    2         SYSDBA       U02                              1         2  READ_COMMITTED
    2         SYSDBA       U02                              2         1  SNAPSHOT
    2         SYSDBA       U02                              3         0  CONSISTENCY
    Records affected: 6
"""

@pytest.mark.version('>=3.0')
@pytest.mark.xfail
def test_1(act_1: Action):
    pytest.fail("Test not IMPLEMENTED")


