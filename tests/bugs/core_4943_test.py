#coding:utf-8
#
# id:           bugs.core_4943
# title:        Dialect 1 casting date to string breaks when in the presence a domain with a check constraint
# decription:   
# tracker_id:   CORE-4943
# min_versions: ['2.5.5']
# versions:     2.5.5
# qmid:         

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5.5
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=1, init=init_script_1)

test_script_1 = """
    -- Confirmed fail on build 2.5.5.26916.
    -- Works fine on: 2.5.5.26933, 3.0.0.32052

    set wng off;
    set term ^;
    create domain dm_without_chk as varchar(5);
    ^
    
    create or alter procedure sp_test1
    returns (
        retDate varchar(25)
        ,out_without_chk dm_without_chk
    ) as
    
    begin
    
      out_without_chk = 'qwe';
    
      retDate = cast('today' as date);
    
      suspend;
    end
    ^
    
    create domain dm_with_check as varchar(5)
           check (value is null or value in ('qwe', 'rty'))
    ^
    
    create or alter procedure sp_test2
    returns (
        retDate varchar(25)
        ,out_with_check dm_with_check
    ) as
    begin
      out_with_check = 'rty';
    
      retDate = cast('today' as date);
    
      suspend;
    end
    ^
    set term ;^
    commit;
    
    set list on;
    
    select iif(char_length(retDate)<=11, 1, 0) as sp_test1_format_ok
    from sp_test1;
    
    select iif(char_length(retDate)<=11, 1, 0) as sp_test2_format_ok
    from sp_test2;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """

    SP_TEST1_FORMAT_OK              1
    SP_TEST2_FORMAT_OK              1
"""

@pytest.mark.version('>=2.5.5')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

