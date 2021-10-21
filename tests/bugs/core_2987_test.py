#coding:utf-8
#
# id:           bugs.core_2987
# title:        Don't send full length of field over the wire when field is null
# decription:
#                   Checked on: WI-V3.0.0.32484 (SS/SC/CS), LI-T4.0.0.138 (SS)
#
# tracker_id:   CORE-2987
# min_versions: ['3.0']
# versions:     3.0
# qmid:

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    -- Measurement showed than on 3.0 (SS/SC/CS) transfer of NULLs is more than 5 (five) times
    -- faster than text data with length = 32K. As of 2.5 (SC) than ration is about 1.7 ... 1.8.
    -- Test fills up two tables: one with text data and another with only nulls.
    -- Then we receive data from these tables via ES/EDS, evaluate elapsed time for both cases
    -- and calculate its ratio. This ratio in 3.0 should be not less than 4x.
    create or alter procedure sp_test returns(sel_data_ms int, sel_null_ms int) as begin end;
    create or alter procedure sp_test as begin end;

    recreate global temporary table test1(f01 char(32760)) on commit delete rows;
    recreate global temporary table test2(f01 char(32760)) on commit delete rows;
    commit;


    set term ^;
    create or alter procedure sp_fill as
      declare c_added_rows int = 2000;
    begin
        execute statement
           'insert into test1 '
           || 'with recursive r as (select 0 i from rdb$database union all select r.i+1 from r where r.i<99) '
           || 'select rpad('''', 32760, uuid_to_char(gen_uuid()) ) from r r1,r r2 rows ' || c_added_rows
           on external 'localhost:' || rdb$get_context('SYSTEM','DB_NAME')
           as user 'SYSDBA' password 'masterkey'
           role 'R001' ------------------------------- this will create new attach #1 that will be used later!
        ;
        execute statement
           'insert into test2 '
           || 'with recursive r as (select 0 i from rdb$database union all select r.i+1 from r where r.i<99) '
           || 'select null from r r1,r r2 rows ' || c_added_rows
           on external 'localhost:' || rdb$get_context('SYSTEM','DB_NAME')
           as user 'SYSDBA' password 'masterkey'
           role 'R002' ------------------------------- this will create new attach #2 that will be used later!
        ;
    end
    ^

    create or alter procedure sp_test returns( sel_data_ms int, sel_null_ms int, ratio numeric(10,2) ) as
      declare v_f01 type of column test1.f01;
      declare t0 timestamp;
      declare t1 timestamp;
      declare t2 timestamp;
    begin

        t0='now';
        for
            execute statement
               'select f01 from test1' on external 'localhost:' || rdb$get_context('SYSTEM','DB_NAME')
               as user 'SYSDBA' password 'masterkey'
               role 'R001' --------------- here we use EXISTING attach #1 (from internal FB connection pool)
               into v_f01
        do begin end

        t1='now';

        for
            execute statement
               'select f01 from test2' on external 'localhost:' || rdb$get_context('SYSTEM','DB_NAME')
               as user 'SYSDBA' password 'masterkey'
               role 'R002'  --------------- here we use EXISTING attach #2 (from internal FB connection pool)
               into v_f01
        do begin end

        t2='now';

        sel_data_ms = datediff(millisecond from t0 to t1);
        sel_null_ms = datediff(millisecond from t1 to t2);
        ratio = coalesce( sel_data_ms * 1.000 / nullif(sel_null_ms,0), 9999999.99);

        suspend;

    end
    ^
    set term ;^
    --commit;

    set list on;

    --set stat on;
    -- must be ~15 sec
    execute procedure sp_fill; -- will add data into GTT test1 (in attach #1) and GTT test2 (in attach #2)
    --set stat off;

    set term ^;
    execute block returns( measure_result varchar(40) ) as
      declare min_profit_ratio numeric(3,1) = 3.8;  -- #####  T H R E S H O L D  ####
      declare sel_data_ms int;
      declare sel_null_ms int;
      declare ratio numeric(10,2);
    begin

      -- These four calls will extract rows from GTT test1  (in attach #1) and from GTT test2 (in attach #2).
      -- We have to register statistics only for 2nd...4th measurements due to probable file cache affects.

      select ratio, '' from sp_test into ratio, measure_result;
      --- do not suspend now --
      select sel_data_ms, sel_null_ms, ratio, iif( ratio >= :min_profit_ratio, 'WINS >= '||:min_profit_ratio||'x', 'LOOSES, '||ratio||'x')
        from sp_test
        into sel_data_ms, sel_null_ms,ratio, measure_result;
      suspend;
      select sel_data_ms, sel_null_ms, ratio, iif( ratio >= :min_profit_ratio, 'WINS >= '||:min_profit_ratio||'x', 'LOOSES, '||ratio||'x')
        from sp_test
        into sel_data_ms, sel_null_ms,ratio, measure_result;
      suspend;
      select sel_data_ms, sel_null_ms, ratio, iif( ratio >= :min_profit_ratio, 'WINS >= '||:min_profit_ratio||'x', 'LOOSES, '||ratio||'x')
        from sp_test
        into sel_data_ms, sel_null_ms,ratio, measure_result;
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

# [pcisar] 20.10.2021
# This test fails on my system due to (unexpected) error output from test script:
# Statement failed, SQLSTATE = 42000
# Execute statement error at isc_dsql_execute2 :
# 335544321 : arithmetic exception, numeric overflow, or string truncation
# 335544381 : Implementation limit exceeded
# Statement : insert into test1 with recursive r as (select 0 i from rdb$database union all select r.i+1 from r where r.i<99) select rpad('', 32760, uuid_to_char(gen_uuid()) ) from r r1,r r2 rows 2000
# Data source : Firebird::localhost:/tmp/pytest-of-pcisar/pytest-7/test_1514/test.fdb
# -At procedure 'SP_FILL' line: 4, col: 9
#
# Also, the stdout from test script differs:
# MEASURE_RESULT                  WINS >= 3.8x
# MEASURE_RESULT                  LOOSES, 0.00x
# MEASURE_RESULT                  LOOSES, 0.00x

expected_stdout_1 = """
   MEASURE_RESULT                  WINS >= 3.8x
   MEASURE_RESULT                  WINS >= 3.8x
   MEASURE_RESULT                  WINS >= 3.8x
  """

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.charset = 'NONE'
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_expected_stdout == act_1.clean_stdout

