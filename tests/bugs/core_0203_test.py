#coding:utf-8
#
# id:           bugs.core_0203
# title:        CREATE VIEW ignores PLAN
# decription:   
#                   Test verifies that:
#                   1. "PLAN <...>" clause inside view DLL is always ignored and actual plan will be one of following:
#                       1.1. That is specified explicitly by client who runs a query to this view;
#                       1.2. If no explicitly specified plan that optimizer will be allowed to choose that.
#                   2. One may to specify PLAN on client side and it *WILL* be taken in account.
#               
#                   ::: NOTE :::
#                   Suppose that some view contains explicitly specified PLAN NATURAL it its DDL.
#                   If underlying query became suitable to be run with PLAN INDEX (e.g. such index was added to the table)
#                   then this 'PLAN NATURAL' will be IGNORED until it is explicitly specified in the client query.
#                   See below example #4 for view v_test1 defined as "select * from ... plan (t natural)".
#               
#                   Checked on:
#                       4.0.0.1743 SS: 1.781s.
#                       4.0.0.1714 CS: 6.500s.
#                       3.0.6.33236 SS: 1.313s.
#                       3.0.6.33236 CS: 1.891s.
#                       2.5.9.27149 SC: 1.047s.
#                
# tracker_id:   CORE-0203
# min_versions: ['2.5']
# versions:     2.5
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5
# resources: None

substitutions_1 = [('[ ]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set bail on;

    recreate view v_test4 as select 1 x from rdb$database;
    recreate view v_test3 as select 1 x from rdb$database;
    recreate view v_test2 as select 1 x from rdb$database;
    recreate view v_test1 as select 1 x from rdb$database;

    recreate table test(x int, y int);
    commit;

    insert into test(x,y) select rand()*100, rand()*10000 from rdb$types,rdb$types rows 10000;
    commit;

    create index test_x_asc on test(x);
    create descending index test_x_desc on test(x);

    create index test_y_x on test(y, x);
    create index test_x_y on test(x, y);

    create index test_sum_x_y on test computed by (x+y);
    create descending index test_sub_x_y on test computed by (x-y);

    commit;

    recreate view v_test1 as select * from test t where x = 0 plan (t natural);
    recreate view v_test2 as select * from test t where x = 0;
    recreate view v_test3 as select * from test t where x = 0 plan (t index(test_x_desc));
    recreate view v_test4 as select * from v_test3;
    commit;


    set planonly;
    --set echo on;

    select * from test t where x = 0 plan (t natural);                                              --  1

    select * from v_test1 v1;                                                                       --  2

    select * from v_test1 v2;                                                                       --  3

    select * from v_test1 v1 where v1.x = 0 plan (v1 natural);                                      --  4

    select * from v_test2 v2 where v2.x = 0 plan (v2 natural);                                      --  5

    select * from v_test1 v1 where v1.x = 0 PLAN (V1 INDEX (TEST_X_DESC)) ;                         --  6

    select * from v_test2 v2 where v2.x = 0 PLAN (V2 INDEX (TEST_X_DESC)) ;                         --  7

    select * from v_test1 v1 where v1.x = 50 and v1.y = 5000 PLAN (V1 INDEX (test_x_y)) ;           --  8

    select * from v_test1 v2 where v2.x = 50 and v2.y = 5000 PLAN (V2 INDEX (test_y_x)) ;           --  9

    select * from v_test1 v1 where v1.x + v1.y = 1000 PLAN (V1 INDEX (test_x_y));                   -- 10

    select * from v_test2 v2 where v2.x - v2.y = 1000 PLAN (V2 INDEX (test_x_y));                   -- 11

    select * from v_test1 v1 where v1.x + v1.y = 1000 PLAN (V1 INDEX (test_sum_x_y));               -- 12

    select * from v_test2 v2 where v2.x - v2.y = 1000 PLAN (V2 INDEX (test_sub_x_y));               -- 13

    -- NB: here optimizer will use index __NOT__ from view V3 DDL:
    -- PLAN (V3 T INDEX (TEST_X_ASC))
    select * from v_test3 v3;                                                                       -- 14

    select * from v_test3 v3 plan ( v3 index(test_x_y) );

    -- NB: here optimizer will use index __NOT__ from view V3 DDL:
    -- PLAN (V4 V_TEST3 T INDEX (TEST_X_ASC))
    select * from v_test4 v4;                                                                       -- 15

    select * from v_test4 v4 PLAN (V4 V_TEST3 T INDEX (TEST_X_Y));                                  -- 16
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    PLAN (T NATURAL)

    PLAN (V1 T INDEX (TEST_X_ASC))

    PLAN (V2 T INDEX (TEST_X_ASC))

    PLAN (V1 T NATURAL)

    PLAN (V2 T NATURAL)

    PLAN (V1 T INDEX (TEST_X_DESC))

    PLAN (V2 T INDEX (TEST_X_DESC))

    PLAN (V1 T INDEX (TEST_X_Y))

    PLAN (V2 T INDEX (TEST_Y_X))

    PLAN (V1 T INDEX (TEST_X_Y))

    PLAN (V2 T INDEX (TEST_X_Y))

    PLAN (V1 T INDEX (TEST_SUM_X_Y))

    PLAN (V2 T INDEX (TEST_SUB_X_Y))

    PLAN (V3 T INDEX (TEST_X_ASC))

    PLAN (V3 T INDEX (TEST_X_Y))

    PLAN (V4 V_TEST3 T INDEX (TEST_X_ASC))

    PLAN (V4 V_TEST3 T INDEX (TEST_X_Y))

"""

@pytest.mark.version('>=2.5')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

