#coding:utf-8
#
# id:           bugs.core_1318
# title:        Error "Identifier ... is too long using multiple (nested) derived tables
# decription:   
# tracker_id:   CORE-1318
# min_versions: ['2.0.7']
# versions:     2.0.7
# qmid:         bugs.core_1318

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.0.7
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;
    select 0*count(*) cnt
    from (
    select A1.ID 
    from(
            select A2.ID from(
                select A3.ID from(
                    select A4.ID from(
                        select A5.ID from(
                            select A6.ID from(
                                select A7.ID from(
                                    select A8.ID from(
                                        select A9.ID from(
                                            select A10.ID from(
                                                select rdb$relations.rdb$relation_id as id from rdb$relations where  rdb$relations.rdb$relation_id = 1
                                                ) as A10 
                                                union 
                                                select rdb$relations.rdb$relation_id as id from rdb$relations where  rdb$relations.rdb$relation_id = 2
                                            ) as A9 
                                            union
                                            select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 3
                                    ) as A8
                                    union
                                    select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 4
                                ) as A7
                                union
                                select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 5
                            ) as A6
                            union
                            select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 6
                        ) as A5
                        union
                        select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 7
                    ) as A4
                    union
                    select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 8
                ) as A3
                union
                select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 9
            ) as A2
            union
            select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 10
        ) as A1
        union
        select rdb$relations.rdb$relation_id as id from rdb$relations where rdb$relations.rdb$relation_id = 11
    )
    ;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    CNT                             0
"""

@pytest.mark.version('>=2.0.7')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

