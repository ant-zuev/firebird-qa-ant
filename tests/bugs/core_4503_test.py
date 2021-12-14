#coding:utf-8
#
# id:           bugs.core_4503
# title:        ISQL command SHOW USERS display only me
# decription:
#                  29.07.2016: instead of issuing SHOW USERS which has unstable output (can be changed multiple times!)
#                  it was decided to replace it with SQL query which actually is done by this command.
#                  This query can be easily found in trace when we run SHOW USERS.
#                  Also, we limit output with only those users who is enumerated here thus one may do not warry about
#                  another user logins which could left in securitiN.fdb after some test failed.
#
#                  29.03.2018: changed user names, replaced count of SYSDBA attachments with literal 1.
#                  Checked on:
#                      fb30Cs, build 3.0.4.32924: OK, 3.781s.
#                      FB30SS, build 3.0.4.32939: OK, 1.312s.
#                      FB40CS, build 4.0.0.918: OK, 4.547s.
#                      FB40SS, build 4.0.0.943: OK, 2.094s.
#
# tracker_id:   CORE-4503
# min_versions: ['3.0']
# versions:     3.0
# qmid:

import pytest
from firebird.qa import db_factory, python_act, Action, user_factory, User

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = ""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# import os
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#
#  db_conn.close()
#
#  con_0a = kdb.connect(dsn=dsn.encode())
#  con_0b = kdb.connect(dsn=dsn.encode())
#
#  con_1a = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_BILL',password='123')
#  con_1b = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_BILL',password='123')
#  con_1c = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_BILL',password='123')
#  con_1d = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_BILL',password='123')
#  con_1e = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_BILL',password='123')
#
#  con_2a = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_JOHN',password='456')
#  con_2b = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_JOHN',password='456')
#  con_2c = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_JOHN',password='456')
#  con_2d = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_JOHN',password='456')
#
#  con_3a = kdb.connect(dsn=dsn.encode(),user='TMP$C4503_MICK',password='789')
#  script = '''
#      set list on;
#      -- "SHOW USERS" command actually runs following query:
#      select
#          case
#              when coalesce(mon$user, sec$user_name) = current_user
#                  then '#'
#              when sec$user_name is distinct from null
#                  then ' '
#              else '-'
#          end is_current_user
#          ,coalesce(m.mon$user, u.sec$user_name) user_name
#          ,iif( m.mon$user = upper('SYSDBA'), 1, count(m.mon$user) ) keeps_attachments
#      from mon$attachments m
#      full join sec$users u on m.mon$user = u.sec$user_name
#      where
#          coalesce(mon$system_flag, 0) = 0
#          and coalesce(m.mon$user, u.sec$user_name) in ( upper('TMP$C4503_BILL'), upper('TMP$C4503_BOSS'), upper('TMP$C4503_JOHN'), upper('TMP$C4503_MICK'), upper('SYSDBA') )
#      group by mon$user, sec$user_name
#      order by coalesce(mon$user, sec$user_name);
#      commit;
#
#      drop user TMP$C4503_BILL;
#      drop user TMP$C4503_JOHN;
#      drop user TMP$C4503_MICK;
#      drop user TMP$C4503_BOSS;
#  '''
#  runProgram('isql',[dsn,'-q'],script)
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
     IS_CURRENT_USER                 #
     USER_NAME                       SYSDBA
     KEEPS_ATTACHMENTS               1

     IS_CURRENT_USER
     USER_NAME                       TMP$C4503_BILL
     KEEPS_ATTACHMENTS               5

     IS_CURRENT_USER
     USER_NAME                       TMP$C4503_BOSS
     KEEPS_ATTACHMENTS               0

     IS_CURRENT_USER
     USER_NAME                       TMP$C4503_JOHN
     KEEPS_ATTACHMENTS               4

     IS_CURRENT_USER
     USER_NAME                       TMP$C4503_MICK
     KEEPS_ATTACHMENTS               1
"""


user_bill = user_factory('db_1', name='TMP$C4503_BILL', password='123')
user_john = user_factory('db_1', name='TMP$C4503_JOHN', password='456')
user_mick = user_factory('db_1', name='TMP$C4503_MICK', password='789')
user_boss = user_factory('db_1', name='TMP$C4503_BOSS', password='000')

@pytest.mark.version('>=3.0')
def test_1(act_1: Action, user_bill: User, user_john: User, user_mick: User, user_boss: User):
    with act_1.db.connect() as con_0a, act_1.db.connect(), \
         act_1.db.connect(user='TMP$C4503_BILL', password='123'), \
         act_1.db.connect(user='TMP$C4503_BILL', password='123'), \
         act_1.db.connect(user='TMP$C4503_BILL', password='123'), \
         act_1.db.connect(user='TMP$C4503_BILL', password='123'), \
         act_1.db.connect(user='TMP$C4503_BILL', password='123'), \
         act_1.db.connect(user='TMP$C4503_JOHN', password='456'), \
         act_1.db.connect(user='TMP$C4503_JOHN', password='456'), \
         act_1.db.connect(user='TMP$C4503_JOHN', password='456'), \
         act_1.db.connect(user='TMP$C4503_JOHN', password='456'), \
         act_1.db.connect(user='TMP$C4503_MICK', password='789'):
        #
        script = """
        set list on;
        -- "SHOW USERS" command actually runs following query:
        select
            case
                when coalesce(mon$user, sec$user_name) = current_user
                    then '#'
                when sec$user_name is distinct from null
                    then ' '
                else '-'
            end is_current_user
            ,coalesce(m.mon$user, u.sec$user_name) user_name
            ,iif( m.mon$user = upper('SYSDBA'), 1, count(m.mon$user) ) keeps_attachments
        from mon$attachments m
        full join sec$users u on m.mon$user = u.sec$user_name
        where
            coalesce(mon$system_flag, 0) = 0
            and coalesce(m.mon$user, u.sec$user_name) in ( upper('TMP$C4503_BILL'), upper('TMP$C4503_BOSS'), upper('TMP$C4503_JOHN'), upper('TMP$C4503_MICK'), upper('SYSDBA') )
        group by mon$user, sec$user_name
        order by coalesce(mon$user, sec$user_name);
        commit;
        """
        act_1.expected_stdout = expected_stdout_1
        act_1.isql(switches=['-q'], input=script)
        assert act_1.clean_stdout == act_1.clean_expected_stdout
