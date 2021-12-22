#coding:utf-8
#
# id:           bugs.core_6460
# title:        Incorrect query result when using named window
# decription:   
#                   Confirmed bug on 4.0.0.2265. Discussed with Vlad 21.12.2020 (subj: "fresh fails on 4.0.0.2298").
#                   Checked on 4.0.0.2307 -- all OK.
#                   More examples will be implemented later.
#                
# tracker_id:   CORE-6460
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('=', ''), ('[ \t]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    recreate table test (
     emp_no smallint,
     dept_no char(3),
     salary numeric(10,2)
    );
    commit;

    insert into test (emp_no, dept_no, salary) values ( 85, 'd01', 99999);
    insert into test (emp_no, dept_no, salary) values (127, 'd01', 11111);
    commit;

    select e.emp_no, e.dept_no, e.salary,
           last_value(e.salary) over (order by e.salary, e.emp_no) as last_2,
           last_value(e.salary) over w2 as last_w2,
           last_value(e.salary) over (order by e.salary, e.emp_no RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as last_3,
           last_value(e.salary) over w3 as last_w3,
           last_value(e.salary) over w4 as last_w4
      from test e
      window
          w1 as (),
          w2 as (w1 order by e.salary, e.emp_no),
          w3 as (w1 order by e.salary, e.emp_no RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),
          w4 as (w2 RANGE BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
    order by e.emp_no 
    ;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
 EMP_NO DEPT_NO                SALARY                LAST_2               LAST_W2                LAST_3               LAST_W3               LAST_W4 
     85 d01                  99999.00              99999.00              99999.00              99999.00              99999.00              99999.00 
    127 d01                  11111.00              11111.00              11111.00              99999.00              99999.00              99999.00 
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

