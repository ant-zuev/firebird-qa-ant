#coding:utf-8
#
# id:           bugs.core_2075
# title:        Parts of RDB$DB_KEY of views may be inverted when using outer joins
# decription:   
# tracker_id:   CORE-2075
# min_versions: []
# versions:     2.5.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5.0
# resources: None

substitutions_1 = []

init_script_1 = """create table t1 (n integer);
create table t2 (n integer);

insert into t1 values (1);
insert into t1 values (2);
insert into t1 values (3);
insert into t1 values (4);
insert into t1 values (5);
insert into t1 values (6);

insert into t2 values (2);
insert into t2 values (4);
insert into t2 values (5);
insert into t2 values (8);
commit;

create view v (t1, t2) as
  select t1.rdb$db_key, t2.rdb$db_key
    from t1
    full join t2
      on t2.n = t1.n;
"""

db_1 = db_factory(page_size=4096, sql_dialect=3, init=init_script_1)

test_script_1 = """select v.rdb$db_key, v.*
  from v;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
DB_KEY                           T1               T2
================================ ================ ================
81000000010000008000000002000000 8000000002000000 8100000001000000
81000000020000008000000004000000 8000000004000000 8100000002000000
81000000030000008000000005000000 8000000005000000 8100000003000000
81000000040000000000000000000000 <null>           8100000004000000
00000000000000008000000001000000 8000000001000000 <null>
00000000000000008000000003000000 8000000003000000 <null>
00000000000000008000000006000000 8000000006000000 <null>

"""

@pytest.mark.version('>=2.5.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

