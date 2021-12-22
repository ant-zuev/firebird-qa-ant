#coding:utf-8
#
# id:           functional.syspriv.change_mapping_rules
# title:        Check ability to manage auth mappings
# decription:   
#                  Verify ability to issue CREATE / ALTER / DROP MAPPING by non-sysdba user.
#                  Checked  on 5.0.0.133 SS/CS, 4.0.1.2563 SS/CS
#                
# tracker_id:   
# min_versions: ['4.0.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('.*Global mapping.*', '')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set wng off;
    -- set bail on;
    set list on;

    -- NB: without 'grant admin role' it is unable to create GLOBAL mapping:
    -- Statement failed, SQLSTATE = 28000 / ... / -CREATE OR ALTER MAPPING ... failed
    -- -Unable to perform operation /-System privilege CHANGE_MAPPING_RULES is missing
    create or alter
         user john_smith_mapping_manager
         password '123'
         grant admin role --- [ !!! ]
    ;

    set term ^;
    execute block as
    begin
        execute statement 'drop role tmp_role_for_change_mapping';
        when any do begin end
    end^
    set term ;^

    create role tmp_role_for_change_mapping set system privileges to CHANGE_MAPPING_RULES;
    commit;

    grant default tmp_role_for_change_mapping to user john_smith_mapping_manager;
    commit;

    connect '$(DSN)' user john_smith_mapping_manager password '123'; --  role tmp_role_for_change_mapping;

    create or alter mapping tmp_syspriv_local_map using plugin srp from any user to user;
    create or alter global mapping tmp_syspriv_global_map using plugin srp from any user to user;
    commit;

    show mapping;
    
    drop global mapping tmp_syspriv_global_map;
    drop mapping tmp_syspriv_local_map;
    commit;

    connect '$(DSN)' user sysdba password 'masterkey';
    drop user john_smith_mapping_manager;
    drop role tmp_role_for_change_mapping;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    TMP_SYSPRIV_LOCAL_MAP USING PLUGIN SRP FROM ANY USER TO USER
    *** Global mapping ***
    TMP_SYSPRIV_GLOBAL_MAP USING PLUGIN SRP FROM ANY USER TO USER
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

