#coding:utf-8
#
# id:           bugs.core_4604
# title:        EXECUTE STATEMENT rise varchar char_length() size
# decription:   
#                   Checked on:
#                       4.0.0.1635 SS: 1.006s.
#                       4.0.0.1633 CS: 1.389s.
#                       3.0.5.33180 SS: 0.677s.
#                       3.0.5.33178 CS: 0.932s.
#                       2.5.9.27119 SS: 0.189s.
#                       2.5.9.27146 SC: 0.192s.
#                
# tracker_id:   CORE-4604
# min_versions: ['2.5.4']
# versions:     2.5.4
# qmid:         

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5.4
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;
    set term ^;
    execute block returns (str_size integer)
    as
        declare variable tmp_guid varchar(38);
        declare variable tmp_sqltext varchar(300);
        declare v_dbname type of column mon$database.mon$database_name;
        declare v_usr varchar(31) = 'SYSDBA';
        declare v_pwd varchar(31) = 'masterkey';
    begin
        
        v_dbname = 'localhost:' || rdb$get_context('SYSTEM', 'DB_NAME');

        ---------------------------------------------------------------
        
        tmp_guid = uuid_to_char(gen_uuid());

        str_size = char_length(tmp_guid);
        suspend;

        ---------------------------------------------------------------
        
        tmp_sqltext = 'select ''' || tmp_guid || ''' from rdb$database';

        execute statement (:TMP_SQLTEXT) 
        into :tmp_guid;
        
        str_size = char_length(tmp_guid);
        suspend;

        ---------------------------------------------------------------
        
        execute statement (:TMP_SQLTEXT) 
        on external v_dbname as user v_usr password v_pwd
        into :tmp_guid;
        
        str_size = char_length(tmp_guid);
        
        --  Confirmed on WI-T3.0.0.31374 Firebird 3.0 Beta 1/tcp (csprog)/P13
        -- STR_SIZE                        36
        -- STR_SIZE                        36
        -- STR_SIZE                        144        

        suspend;

    end
    ^
    set term ;^
    commit;

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


"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    STR_SIZE                        36
    STR_SIZE                        36
    STR_SIZE                        36
"""

@pytest.mark.version('>=2.5.4')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

