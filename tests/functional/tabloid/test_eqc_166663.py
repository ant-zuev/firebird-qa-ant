#coding:utf-8
#
# id:           functional.tabloid.eqc_166663
# title:        Index(es) should not become corrupted after two updates and raising exception in one Tx, doing inside SP
# decription:   
# tracker_id:   
# min_versions: ['2.5.0']
# versions:     2.5
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5
# resources: None

substitutions_1 = [('exception .*', 'exception'), ('line: .*', 'line')]

init_script_1 = """"""

db_1 = db_factory(page_size=4096, sql_dialect=3, init=init_script_1)

test_script_1 = """
    -- NB: changed expected value of SQLSTATE from 42000 to HY000, see:
    -- "Prevent stack trace (line/column info) from overriding the real error's SQLSTATE", 30-apr-2016 
    -- https://github.com/FirebirdSQL/firebird/commit/d1d8b36a07d4f11d98d2c8ec16fb8ec073da442b // FB 4.0
    -- https://github.com/FirebirdSQL/firebird/commit/849bfac745bc9158e9ef7990f5d52913f8b72f02 // FB 3.0
    -- https://github.com/FirebirdSQL/firebird/commit/b9d4142c4ed1fdf9b7c633edc7b2425f7b93eed0 // FB 2.5
    -- See also letter from dimitr, 03-may-2016 19:24.


    create or alter procedure sp_test ( a_id int) as begin end;
    set term ^;
    execute block as
    begin
        execute statement 'drop exception ex_foo'; when any do begin end
    end
    ^
    set term ;^
    commit;

    recreate table tdetl (
        id int primary key using index tdetl_pk,
        pid int
    );
    commit;
    
    recreate table tmain (
        id int primary key using index tmain_pk ,
        name varchar(20)
    );
    commit;
    
    alter table tdetl add constraint tdetl_fk foreign key (pid) references tmain(id);
    commit;
    
    insert into tmain (id, name) values (1, 'qwerty');
    commit;
    
    
    create exception ex_foo 'ex_foo';
    commit;
    
    set term ^;
    create or alter procedure sp_test ( a_id int)
    as
    begin
       update tdetl set id = id where id = :a_id;
       update tdetl set pid = 1 where id = :a_id;
       exception ex_foo;
    end
    ^
    set term ;^
    commit;
    
    insert into tdetl (id, pid) values (1,null);
    execute procedure sp_test(1);
    
    set plan on;
    set list on;
    set count on;
    set heading off;
    set echo on;
    
    select * from tdetl where id >= 0;
    
    select * from tdetl where pid is null;
    
    select * from tdetl;
    
    select * from tmain where id >= 0;
    
    select * from tmain;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    select * from tdetl where id >= 0;
    PLAN (TDETL INDEX (TDETL_PK))
    ID                              1
    PID                             <null>
    Records affected: 1
    
    select * from tdetl where pid is null;
    PLAN (TDETL INDEX (TDETL_FK))
    ID                              1
    PID                             <null>
    Records affected: 1
    
    select * from tdetl;
    PLAN (TDETL NATURAL)
    ID                              1
    PID                             <null>
    Records affected: 1
    
    select * from tmain where id >= 0;
    PLAN (TMAIN INDEX (TMAIN_PK))
    ID                              1
    NAME                            qwerty
    Records affected: 1
    
    select * from tmain;
    PLAN (TMAIN NATURAL)
    ID                              1
    NAME                            qwerty
    Records affected: 1
"""
expected_stderr_1 = """
    Statement failed, SQLSTATE = HY000
    exception 2
    -EX_FOO
    -ex_foo
    -At procedure 'SP_TEST' line: 6, col: 8
"""

@pytest.mark.version('>=2.5')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr

    assert act_1.clean_stdout == act_1.clean_expected_stdout

