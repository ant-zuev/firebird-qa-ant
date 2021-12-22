#coding:utf-8
#
# id:           bugs.core_3242
# title:        Recursive stored procedure shouldnt require execute right to call itself
# decription:   
#                   Checked on: 4.0.0.1635: OK, 2.337s; 3.0.5.33180: OK, 2.497s.
#                
# tracker_id:   CORE-3242
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
    set wng off;
    set bail on;

    -- Drop old account if it remains from prevoius run:
    set term ^;
    execute block as
    begin
        begin
            execute statement 'drop user tmp$c3242' with autonomous transaction;
            when any do begin end
        end
    end
    ^
    set term ;^
    commit;

    create user tmp$c3242 password '123';
    commit;

    set term ^;
    create or alter procedure sp_recur(i smallint) returns(o bigint) as
    begin
        if ( i > 1 ) then
            o = i * (select o from sp_recur( :i - 1 ));
        else
            o = i;

        suspend;

    end
    ^

    create or alter function fn_recur(i smallint) returns bigint as
    begin
        if ( i > 1 ) then
            return i * fn_recur( i-1 );
        else
            return i;
    end
    ^
    
    create or alter procedure sp_factorial(i smallint) returns (o bigint) as
    begin
        for select o from sp_recur( :i ) into o do suspend;
    end
    ^
    create or alter function fn_factorial(i smallint) returns bigint as
    begin
        return fn_recur( i );
    end
    ^

    recreate package pg_factorial as
    begin
        procedure pg_sp_factorial(i smallint) returns (o bigint);
        function pg_fn_factorial(i smallint) returns bigint;
    end
    ^

    create package body pg_factorial as
    begin
        procedure pg_sp_factorial(i smallint) returns(o bigint) as
        begin
            if ( i > 1 ) then
                o = i * (select o from sp_recur( :i - 1 ));
            else
                o = i;

            suspend;

        end

        function pg_fn_factorial(i smallint) returns bigint as
        begin
            if ( i > 1 ) then
                return i * fn_recur( i-1 );
            else
                return i;
        end
    end
    ^
    set term ;^
    commit;


    ---------------------------------------------------------------------------
   
    revoke all on all from tmp$c3242;
    commit;

    grant execute on function fn_factorial to tmp$c3242; 
    grant execute on procedure sp_factorial to tmp$c3242;
    grant execute on package pg_factorial to tmp$c3242;

    grant execute on function fn_recur to function fn_factorial;
    grant execute on procedure sp_recur to procedure sp_factorial;
    grant execute on function fn_recur to package pg_factorial;
    grant execute on procedure sp_recur to package pg_factorial;
    commit;

    connect '$(DSN)' user tmp$c3242 password '123';

    set list on;
    select p.o as standalone_sp_result from sp_factorial(5) p;
    select fn_factorial(7) as standalone_fn_result from rdb$database;

    select p.o as packaged_sp_result from pg_factorial.pg_sp_factorial(9) p;
    select pg_factorial.pg_fn_factorial(11) as packaged_fn_result from rdb$database;
    commit;

    connect '$(DSN)' user sysdba password 'masterkey';
    drop user tmp$c3242;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    STANDALONE_SP_RESULT            120
    STANDALONE_FN_RESULT            5040
    PACKAGED_SP_RESULT              362880
    PACKAGED_FN_RESULT              39916800
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

