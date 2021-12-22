#coding:utf-8
#
# id:           bugs.core_4027
# title:        Creating table with computed fields containing "SELECT FIRST" produces corrupted result
# decription:   Broken output in ISQL command SHOW TABLE <T> for computed-by field(s).
# tracker_id:   CORE-4027
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(page_size=4096, sql_dialect=3, init=init_script_1)

test_script_1 = """
    -- NB: fixed only in 3.0 (checked 30.03.2015)
    recreate table test (id int);
    commit;
    
    recreate table contragents (
        agent_id   int not null
        ,agent_name varchar(25) not null
    );
    commit;
    
    recreate table turnovers(
        po_number  char(8) not null
        ,agent_id   int not null
        ,order_date timestamp default 'now' not null
    );
    commit;
    
    recreate table test (
        agent_id integer not null,
        first_po_number computed by (
            (
                select first 1 t.po_number
                from turnovers t
                where t.agent_id=test.agent_id
                order by t.order_date
            )
        ),
        agent_name computed by (
            (
                select agent_name
                from contragents a
                where a.agent_id = test.agent_id
            )
        )
    );
    commit;
    show table test;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    AGENT_ID                        INTEGER Not Null
    FIRST_PO_NUMBER                 Computed by: (
                (
                    select first 1 t.po_number
                    from turnovers t
                    where t.agent_id=test.agent_id
                    order by t.order_date
                )
            )
    AGENT_NAME                      Computed by: (
                (
                    select agent_name
                    from contragents a
                    where a.agent_id = test.agent_id
                )
            )
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

