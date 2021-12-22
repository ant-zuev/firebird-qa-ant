#coding:utf-8
#
# id:           functional.syspriv.monitor_any_attachment
# title:        Check ability to monitor any attachment.
# decription:   
#                   Checked:
#                       4.0.0.1635 SS: 1.497s.
#                       4.0.0.1633 CS: 2.024s.
#                
# tracker_id:   
# min_versions: ['4.0.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set wng off;
    set bail on;
    set list on;
    set count on;

    create or alter view v_check as
    select 
         current_user as who_ami
        ,r.rdb$role_name
        ,rdb$role_in_use(r.rdb$role_name) as RDB_ROLE_IN_USE
        ,r.rdb$system_privileges
    from mon$database m cross join rdb$roles r;
    commit;

    create or alter user u01 password '123' revoke admin role;
    revoke all on all from u01;
    commit;

    grant select on v_check to public;
    commit;

    set term ^;
    execute block as
    begin
      execute statement 'drop role role_for_monitor_any_attach';
      when any do begin end
    end
    ^
    set term ;^
    commit;

    -- Monitor (via MON$ tables) attachments from other users:
    create role role_for_monitor_any_attach 
        set system privileges to MONITOR_ANY_ATTACHMENT;
    commit;
    grant default role_for_monitor_any_attach to user u01;
    commit;

    connect '$(DSN)' user u01 password '123';
    commit;
    select * from v_check;
    commit;

    set term ^;
    execute block returns(
        who_am_i rdb$user,
        who_else_here rdb$user,
        what_he_is_doing varchar(250)
    ) as
        declare another_user varchar(31);
        declare v_other_sttm varchar(40);
    begin
        v_other_sttm = 'select current_user from rdb$database';

        execute statement (v_other_sttm)
        on external 'localhost:' || rdb$get_context('SYSTEM','DB_NAME')
        as user 'SYSDBA' password 'masterkey'
        into another_user;

        for 
            select 
                current_user,
                a.mon$user,
                s.mon$sql_text
            from mon$attachments a 
            join mon$statements s using(mon$attachment_id)
            where 
                a.mon$user<>current_user 
                and a.mon$system_flag is distinct from 1 
                -- NB: for Classic 4.0 we should prevent output from:
                -- SELECT 
                --     RDB$MAP_USING, RDB$MAP_PLUGIN, RDB$MAP_DB, 
                --     RDB$MAP_FROM_TYPE, RDB$MAP_FROM, RDB$MAP_TO_TYPE, RDB$MAP_TO 
                -- FROM RDB$AUTH_MAPPING
                -- -- so we add filter on s.mon$sql_text:
                and s.mon$sql_text containing :v_other_sttm
            into who_am_i, who_else_here, what_he_is_doing
        do 
            suspend;
    end
    ^
    set term ;^
    commit;
    set count off;

    connect '$(DSN)' user sysdba password 'masterkey';

    --                                    ||||||||||||||||||||||||||||
    -- ###################################|||  FB 4.0+, SS and SC  |||##############################
    --                                    ||||||||||||||||||||||||||||
    -- If we check SS or SC and ExtConnPoolLifeTime > 0 (config parameter FB 4.0+) then current
    -- DB (bugs.core_NNNN.fdb) will be 'captured' by firebird.exe process and fbt_run utility
    -- will not able to drop this database at the final point of test.
    -- Moreover, DB file will be hold until all activity in firebird.exe completed and AFTER this
    -- we have to wait for <ExtConnPoolLifeTime> seconds after it (discussion and small test see
    -- in the letter to hvlad and dimitr 13.10.2019 11:10).
    -- This means that one need to kill all connections to prevent from exception on cleanup phase:
    -- SQLCODE: -901 / lock time-out on wait transaction / object <this_test_DB> is in use
    -- #############################################################################################
    delete from mon$attachments where mon$attachment_id != current_connection;
    commit;    

    drop user u01;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    WHO_AMI                         U01
    RDB$ROLE_NAME                   RDB$ADMIN
    RDB_ROLE_IN_USE                 <false>
    RDB$SYSTEM_PRIVILEGES           FFFFFFFFFFFFFFFF
    WHO_AMI                         U01
    RDB$ROLE_NAME                   ROLE_FOR_MONITOR_ANY_ATTACH
    RDB_ROLE_IN_USE                 <true>
    RDB$SYSTEM_PRIVILEGES           8000000000000000
    Records affected: 2
    WHO_AM_I                        U01
    WHO_ELSE_HERE                   SYSDBA
    WHAT_HE_IS_DOING                select current_user from rdb$database
    Records affected: 1
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

