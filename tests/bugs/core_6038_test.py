#coding:utf-8
#
# id:           bugs.core_6038
# title:        Srp user manager sporadically creates users which can not attach
# decription:
#                   Explanation of bug nature was provided by Alex, see letter 05-jun-19 13:51.
#                   Some iteration failed with probability equal to occurence of 0 (zero) in the
#                   highest BYTE of some number. Byte is 8 bit ==> this probability is 1/256.
#                   Given 'N_LIMIT' is number of iterations, probability of success for ALL of
#                   them is 7.5%, and when N_LIMIT is 1000 then p = 0.004%.
#                   Because of time (speed) it was decided to run only 256 iterations. If bug
#                   will be 'raised' somewhere then this number is enough to catch it after 2-3
#                   times of test run.
#
#                   Reproduced on WI-V3.0.5.33118, date: 11-apr-19 (got fails not late than on 250th iteration).
#                   Works fine on WI-V3.0.5.33139, date: 04-apr-19.
#
#                   :::NOTE:::
#                   A new bug was found during this test implementation, affected 4.0 Classic only: CORE-6080.
#
#                   Checked on:
#                       3.0.5.33140, SS: OK, 14.864s.
#                       4.0.0.1530,  SS: OK, 22.478s.
#                       4.0.0.1530,  Cs: OK, 39.576s. -- NB: Classic mode failed until core-6080 was fixed
#
# tracker_id:   CORE-6038
# min_versions: ['3.0.5']
# versions:     3.0.5
# qmid:         None

import pytest
from firebird.qa import db_factory, python_act, Action, User

# version: 3.0.5
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
#
#  import os
#  import fdb
#
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#
#  N_LIMIT = 256
#  #          ^
#  #          |                   ###############################
#  #          +-------------------###  number of iterations   ###
#  #                              ###############################
#
#  CHECK_USR = 'tmp$c6038_srp'
#  CHECK_PWD = 'QweRty#6038$='
#
#  for i in range(0, N_LIMIT):
#      db_conn.execute_immediate( "create or alter user %(CHECK_USR)s password '%(CHECK_PWD)s' using plugin Srp" % locals() )
#      db_conn.commit()
#      con_check = fdb.connect( dsn = dsn, user = CHECK_USR, password = CHECK_PWD )
#      con_check.close()
#      db_conn.execute_immediate( "drop user %(CHECK_USR)s using plugin Srp" % locals() )
#      db_conn.commit()
#
#
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

CHECK_USR = 'tmp$c6038_srp'
CHECK_PWD = 'QweRty#6038$='

@pytest.mark.version('>=3.0.5')
def test_1(act_1: Action):
    N_LIMIT = 256
    for i in range(N_LIMIT):
        with User(act_1.db, name=CHECK_USR, password=CHECK_PWD, plugin='Srp', charset='utf8'):
            with act_1.db.connect(user=CHECK_USR, password=CHECK_PWD):
                pass
    # Passed.


