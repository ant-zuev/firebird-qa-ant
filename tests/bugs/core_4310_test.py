#coding:utf-8
#
# id:           bugs.core_4310
# title:        DateAdd(): change input <amount> argument from INT to BIGINT
# decription:   
#                    See also test for CORE-6241.
#                
# tracker_id:   CORE-4310
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = [('^((?!sqltype|DTS1|DTS2|SQLSTATE|exceed|range|valid).)*$', ''), ('[ ]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set sqlda_display on;
    set planonly;
    select dateadd( ? millisecond to ?) from rdb$database;
    set planonly;
    set plan off;
    set sqlda_display off;
    set list on;
    
    select 
         dateadd(  315537897599998 millisecond to timestamp '01.01.0001 00:00:00.001' ) dts1
        ,dateadd( -315537897599998 millisecond to timestamp '31.12.9999 23:59:59.999' ) dts2
    from rdb$database;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    01: sqltype: 580 INT64 scale: -1 subtype: 0 len: 8
    02: sqltype: 510 TIMESTAMP scale: 0 subtype: 0 len: 8
    01: sqltype: 510 TIMESTAMP scale: 0 subtype: 0 len: 8
    DTS1                            9999-12-31 23:59:59.9990
    DTS2                            0001-01-01 00:00:00.0010
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

