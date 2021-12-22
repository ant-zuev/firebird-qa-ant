#coding:utf-8
#
# id:           bugs.core_4870
# title:        Incorrect number of affected rows for UPDATE against VIEW created WITH CHECK OPTION
# decription:   
#                  Issue about 2.5.x: added artificial sort inside MERGE source: "using( select ... from test ORDER BY X ) s"
#                  - for suppressing undesirable effect of unstable cursor.
#                  Until 21-may-2016 ISQL 2.5 did not contain portion that fixed CORE-4817
#                  (see: https://github.com/FirebirdSQL/firebird/commit/845120fdb9b5934e3af32b5404ffde7ed363724d )
#                  - letter from dimitr, 21-may-2016 14:51.
#                
# tracker_id:   CORE-4870
# min_versions: ['2.5.6']
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
    -- Checked on LI-V3.0.0.32008, build after commiting rev. http://sourceforge.net/p/firebird/code/62140
    create or alter view v_test3 as select 1 id from rdb$database;
    create or alter view v_test2 as select 1 id from rdb$database;
    create or alter view v_test1 as select 1 id from rdb$database;
    commit;
    
    recreate table test(id int primary key, x int);
    commit;
    insert into test values(1, 100);
    insert into test values(2, 200);
    insert into test values(3, 300);
    insert into test values(4, 400);
    insert into test values(5, 500);
    insert into test values(6, 600);
    commit;
    
    recreate view v_test1 as select * from test where mod(id, 3)=0; 
    recreate view v_test2 as select * from test where mod(id, 3)=0 with check option; 
    recreate view v_test3 as select * from v_test2 where mod(id, 3)=0 with check option; 
    commit;
    
    set count on;
    update v_test1 set x = -x where mod(id,3) = 0;
    rollback;
    
    update v_test2 set x = -x where mod(id,3) = 0;
    rollback;
    
    update v_test3 set x = -x where mod(id,3) = 0;
    rollback;
    
    merge into v_test1 t using( select id, x from test ) s on t.id = s.id
    when matched then update set x = -s.x
    when not matched then insert(id, x) values( -3 * s.id, -s.x )
    ;
    rollback;
    
    merge into v_test2 t using( select id, x from test ) s on t.id = s.id
    when matched then update set x = -s.x
    when not matched then insert(id, x) values( -3 * s.id, -s.x )
    ;
    rollback;
    
    merge into v_test3 t using( select id, x from test ) s on t.id = s.id
    when matched then update set x = -s.x
    when not matched then insert(id, x) values( -3 * s.id, -s.x )
    ;
    rollback;
    
    insert into v_test1(id, x) values( 9,  900);
    insert into v_test2(id, x) values(12, 1200);
    insert into v_test3(id, x) values(15, 1500);
    rollback;
    
    set count off;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    Records affected: 2
    Records affected: 2
    Records affected: 2
    Records affected: 6
    Records affected: 6
    Records affected: 6
    Records affected: 1
    Records affected: 1
    Records affected: 1
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

