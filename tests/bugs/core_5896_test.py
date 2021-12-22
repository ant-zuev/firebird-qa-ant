#coding:utf-8
#
# id:           bugs.core_5896
# title:        NOT NULL constraint is not synchronized after rename column
# decription:   
#                  Confirmed bug on: 4.0.0.1166
#                  Checked on: 4.0.0.1172: OK, 1.875s - works fine.
#                  Added check of rdb$relation_fields.rdb$null_flag after suggestion by Adriano, 26.08.2018 19:12.
#                
# tracker_id:   CORE-5896
# min_versions: ['4.0']
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
    set bail on;
    set count on;
    set list on;


    create or alter view v_chk as
        select 
             --cc.rdb$constraint_name constr_name
             rc.rdb$relation_name rel_name 
            ,cc.rdb$trigger_name trg_name
            ,rf.rdb$null_flag null_flag
          from rdb$check_constraints cc 
               join rdb$relation_constraints rc on cc.rdb$constraint_name = rc.rdb$constraint_name 
               left join rdb$relation_fields rf 
                  on rc.rdb$relation_name = rf.rdb$relation_name 
                 and cc.rdb$trigger_name = rf.rdb$field_name 
         where rc.rdb$constraint_type = upper('not null')
    ; 
    commit;

    recreate table test ( 
        old_name bigint not null 
    ); 
    commit;

    select * from v_chk;
    commit;

    alter table test alter old_name to new_name;
    commit;

    select * from v_chk;

    -- Output BEFORE fix was:
    -------------------------
    -- REL_NAME                        TEST
    -- TRG_NAME                        OLD_NAME
    -- NULL_FLAG                       <null>
    commit;

"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    REL_NAME                        TEST
    TRG_NAME                        OLD_NAME
    NULL_FLAG                       1
    Records affected: 1

    REL_NAME                        TEST
    TRG_NAME                        NEW_NAME
    NULL_FLAG                       1
    Records affected: 1
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

