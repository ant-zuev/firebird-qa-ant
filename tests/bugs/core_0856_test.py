#coding:utf-8
#
# id:           bugs.core_0856
# title:        Unable to set FName, MName, LName fields in security to blank
# decription:   
# tracker_id:   CORE-856
# min_versions: []
# versions:     3.0
# qmid:         bugs.core_856

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    create or alter user tmp$c0856 password '123'
      firstname  '....:....1....:....2....:....3..'
      middlename '....:....1....:....2....:....3..'
      lastname   '....:....1....:....2....:....3..'
    ;
    commit;
    set list on;

    select sec$user_name, sec$first_name, sec$middle_name, sec$last_name
    from sec$users where upper(sec$user_name)=upper('tmp$c0856');

    alter user tmp$c0856
    firstname ''
    middlename _ascii x'09'
    lastname _ascii x'0A'
    ;

    commit;
    select 
        sec$user_name, 
        octet_length(sec$first_name), 
        octet_length(sec$middle_name), 
        octet_length(sec$last_name), 
        ascii_val(left(sec$first_name,1)), 
        ascii_val(left(sec$middle_name,1)), 
        ascii_val(left(sec$last_name,1))
    from sec$users where upper(sec$user_name)=upper('tmp$c0856');
    commit;
    
    drop user tmp$c0856;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    SEC$USER_NAME                   TMP$C0856
    SEC$FIRST_NAME                  ....:....1....:....2....:....3..
    SEC$MIDDLE_NAME                 ....:....1....:....2....:....3..
    SEC$LAST_NAME                   ....:....1....:....2....:....3..

    SEC$USER_NAME                   TMP$C0856
    OCTET_LENGTH                    <null>
    OCTET_LENGTH                    1
    OCTET_LENGTH                    1
    ASCII_VAL                       <null>
    ASCII_VAL                       9
    ASCII_VAL                       10
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

