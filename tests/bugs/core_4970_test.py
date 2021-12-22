#coding:utf-8
#
# id:           bugs.core_4970
# title:        Table trigger does not see its mode: inserting or updating or deleting
# decription:   
# tracker_id:   CORE-4970
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;

    create or alter view v_chk as select 1 id from rdb$database;
    recreate sequence g;

    recreate table test( id int, x int );
    recreate table tlog( 
         id int generated by default as identity 
        ,expected_mode_in_before_trg varchar(20) 
        ,expected_mode_in_after_trg varchar(20) 
        ,actual_mode_in_before_trg varchar(20) 
        ,actual_mode_in_after_trg varchar(20) 
    );
    commit;

    create or alter view v_chk as
    select * from tlog
    order by id;
    commit;

    set term ^;
    create or alter trigger test_biud for test active before insert or update or delete
    as
    begin
        update tlog set actual_mode_in_before_trg = trim( iif(inserting,'INSERTING', iif(updating,'UPDATING', iif(deleting, 'DELETING', '??? NULL ???'))) )
        where actual_mode_in_before_trg is null
        rows 1;
    end
    ^

    create or alter trigger test_aiud for test active after insert or update or delete
    as
    begin
        update tlog set actual_mode_in_after_trg = trim( iif(inserting,'INSERTING', iif(updating,'UPDATING', iif(deleting, 'DELETING', '??? NULL ???'))) )
        where actual_mode_in_after_trg is null
        rows 1;
    end
    ^
    set term ;^
    commit;

    insert into tlog(expected_mode_in_before_trg, expected_mode_in_after_trg) values ('INSERTING', 'INSERTING');
    insert into test default values;

    insert into tlog(expected_mode_in_before_trg, expected_mode_in_after_trg) values ('UPDATING', 'UPDATING');
    update test set id = -id;

    insert into tlog(expected_mode_in_before_trg, expected_mode_in_after_trg) values ('DELETING', 'DELETING');
    delete from test;

    select * from v_chk;

    rollback;

    drop table test;
    drop view v_chk;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    ID                              1
    EXPECTED_MODE_IN_BEFORE_TRG     INSERTING
    EXPECTED_MODE_IN_AFTER_TRG      INSERTING
    ACTUAL_MODE_IN_BEFORE_TRG       INSERTING
    ACTUAL_MODE_IN_AFTER_TRG        INSERTING

    ID                              2
    EXPECTED_MODE_IN_BEFORE_TRG     UPDATING
    EXPECTED_MODE_IN_AFTER_TRG      UPDATING
    ACTUAL_MODE_IN_BEFORE_TRG       UPDATING
    ACTUAL_MODE_IN_AFTER_TRG        UPDATING

    ID                              3
    EXPECTED_MODE_IN_BEFORE_TRG     DELETING
    EXPECTED_MODE_IN_AFTER_TRG      DELETING
    ACTUAL_MODE_IN_BEFORE_TRG       DELETING
    ACTUAL_MODE_IN_AFTER_TRG        DELETING
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

