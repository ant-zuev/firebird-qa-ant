#coding:utf-8
#
# id:           functional.tabloid.dbp_1940_20110426_1906
# title:        Common SQL. Check correctness of the results
# decription:   
# tracker_id:   
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(from_backup='tabloid-dbp-1940.fbk', init=init_script_1)

test_script_1 = """
    set list on;
    with recursive
    n as (
      select 0 n from rdb$database union all select r.n+1 from n as r where r.n<29
    )
    ,t as (
          select min(d) dd
          from
            (
                select b.vi v, b.tm d, sum(b1.bv) as vol 
                from   bbb b left join bbb b1 on b1.vi=b.vi 
                and b1.tm <= b.tm
                group by b.vi, b.tm
            ) cc
          where vol = 255
    )
    ,b as (
        select b.vi v, b.tm d, sum(b1.bv) as vol 
        from bbb b
        left join bbb b1 on b1.vi=b.vi and b1.tm <= b.tm
        group by b.vi, b.tm
    )
    ,t1 as (
        select dateadd(n second to dd) d
        from t, n
    )
    ,tx as
    (
        select t1.d as f01, count(distinct t2.v) f02
        from t1
        left join
        (
         select v, d, vol
          from b
          where vol between 85 and 170
        ) t2 
        on t2.d<=t1.d
        where 170 > all (select vol from b where b.v=t2.v and b.d<=t1.d)
        group by t1.d
    )
    select * from tx
    order by 1,2
    ;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    F01                             2003-01-01 01:11:00.0000
    F02                             1
    F01                             2003-01-01 01:11:01.0000
    F02                             3
    F01                             2003-01-01 01:11:02.0000
    F02                             4
    F01                             2003-01-01 01:11:03.0000
    F02                             4
    F01                             2003-01-01 01:11:04.0000
    F02                             3
    F01                             2003-01-01 01:11:05.0000
    F02                             3
    F01                             2003-01-01 01:11:06.0000
    F02                             3
    F01                             2003-01-01 01:11:07.0000
    F02                             3
    F01                             2003-01-01 01:11:08.0000
    F02                             3
    F01                             2003-01-01 01:11:09.0000
    F02                             3
    F01                             2003-01-01 01:11:10.0000
    F02                             4
    F01                             2003-01-01 01:11:11.0000
    F02                             5
    F01                             2003-01-01 01:11:12.0000
    F02                             4
    F01                             2003-01-01 01:11:13.0000
    F02                             4
    F01                             2003-01-01 01:11:14.0000
    F02                             3
    F01                             2003-01-01 01:11:15.0000
    F02                             3
    F01                             2003-01-01 01:11:16.0000
    F02                             3
    F01                             2003-01-01 01:11:17.0000
    F02                             4
    F01                             2003-01-01 01:11:18.0000
    F02                             4
    F01                             2003-01-01 01:11:19.0000
    F02                             4
    F01                             2003-01-01 01:11:20.0000
    F02                             4
    F01                             2003-01-01 01:11:21.0000
    F02                             4
    F01                             2003-01-01 01:11:22.0000
    F02                             4
    F01                             2003-01-01 01:11:23.0000
    F02                             4
    F01                             2003-01-01 01:11:24.0000
    F02                             4
    F01                             2003-01-01 01:11:25.0000
    F02                             4
    F01                             2003-01-01 01:11:26.0000
    F02                             4
    F01                             2003-01-01 01:11:27.0000
    F02                             4
    F01                             2003-01-01 01:11:28.0000
    F02                             4
    F01                             2003-01-01 01:11:29.0000
    F02                             4
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

