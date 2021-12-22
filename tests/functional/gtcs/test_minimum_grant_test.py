#coding:utf-8
#
# id:           functional.gtcs.minimum_grant_test
# title:        GTCS/tests/CF_ISQL_34. minimum-grant-test
# decription:   
#               	::: NB ::: 
#               	### Name of original test has no any relation with actual task of this test: ###
#                   https://github.com/FirebirdSQL/fbtcs/blob/master/GTCS/tests/CF_ISQL_34.script
#               
#                   Checked on: 4.0.0.1804 SS; 3.0.6.33271 SS; 2.5.9.27149 SC.
#                
# tracker_id:   
# min_versions: ['2.5.0']
# versions:     2.5
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5
# resources: None

substitutions_1 = [('[ \t]+', ' '), ('no permission for (read/select|SELECT) access.*', 'no permission for read access'), ('no permission for (insert/write|INSERT) access.*', 'no permission for write access'), ('-{0,1}[ ]{0,1}Effective user is.*', '')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;

    set term ^;
    execute block as
    begin
        begin
            execute statement 'drop user tmp$qa_user1' with autonomous transaction;
            when any do begin end
        end

        begin
            execute statement 'drop user tmp$qa_user2' with autonomous transaction;
            when any do begin end
        end
     
    end^
    set term ;^
    commit;
     
    create user tmp$qa_user1 password '123';
    create user tmp$qa_user2 password '456';
    commit;

    create table test (c1 int);
    commit;

    grant insert on test to tmp$qa_user1;
    grant select on test to tmp$qa_user2;
    commit;

    -------------------------------------------------
    connect '$(DSN)' user tmp$qa_user1 password '123';
    select current_user as whoami from rdb$database;
    insert into test values(1); -- should pass
    select * from test;    -- should fail
    commit;

    -------------------------------------------------
    connect '$(DSN)' user tmp$qa_user2 password '456';
    select current_user as whoami from rdb$database;
    insert into test values(2);    -- should fail
    select * from test; -- should pass
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    WHOAMI                          TMP$QA_USER1
    WHOAMI                          TMP$QA_USER2
    C1                              1
"""
expected_stderr_1 = """
    Statement failed, SQLSTATE = 28000
    no permission for read/select access to TABLE TEST

    Statement failed, SQLSTATE = 28000
    no permission for insert/write access to TABLE TEST
"""

@pytest.mark.version('>=2.5')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr

    assert act_1.clean_stdout == act_1.clean_expected_stdout

