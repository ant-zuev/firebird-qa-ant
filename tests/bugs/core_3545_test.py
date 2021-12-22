#coding:utf-8
#
# id:           bugs.core_3545
# title:        Inconsistent domain's constraint validation in PSQL
# decription:   
# tracker_id:   CORE-3545
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = [('-At block line: [\\d]+, col: [\\d]+', '-At block line')]

init_script_1 = """"""

db_1 = db_factory(page_size=4096, sql_dialect=3, init=init_script_1)

test_script_1 = """
    set term ^;
    execute block as
    begin
      begin execute statement 'drop table test'; when any do begin end end
      begin execute statement 'drop domain dm_text'; when any do begin end end
      begin execute statement 'drop domain dm_nums'; when any do begin end end
      begin execute statement 'drop collation co_nums'; when any do begin end end
    end
    ^ set term ;^
    commit;

    create domain dm_text varchar(2) check (value < '5');
    create collation co_nums for utf8 from unicode 'NUMERIC-SORT=1';
    create domain dm_nums varchar(3) character set utf8 check (value < '50') collate co_nums;
    create table test(id int, n dm_nums);
    commit;

    -- This should NOT produce error: domain 'dm_text' check text values without
    -- taking in account their numeric-sort aspect, so '40' will be LESS than '5' 
    -- because of *alphabetical* comparison of these strings:
    set term ^;
    execute block as
      declare v1 dm_text = '40';
    begin
    end
    ^
    
    -- This also should NOT produce error: variable 'v1' will be implicitly casted
    -- to varchar(2), i.e. '40' and then alphabetical comparison will be in action:
    execute block as
      declare v1 dm_text = 40;
    begin
    end
    ^
    set term ;^
    ----------------------------------------------------------------------------------------------------------
    -- Block has been added 24.08.2015 due to message in http://sourceforge.net/p/firebird/code/62113
    -- ("Fixed (again) CORE-3545 - Inconsistent domain's constraint validation in PSQL. Related to CORE-3947")
    -- See tracker message of 28/May/15 02:11 PM about trouble with accepting incorrect values.
    ----------------------------------------------------------------------------------------------------------

    set list on;

    insert into test(id, n) values(1, 4);
    insert into test(id, n) values(2, 399);
    insert into test(id, n) values(2, 50);

    insert into test(id, n) values(3, '4');
    insert into test(id, n) values(3,'399');
    insert into test(id, n) values(4, '50');


    select * from test;
    commit;

    --set echo on;

    -- EB where no casting is required variables are assigned immediately to text literals.
    -- Should FAIL due to "var2_assignment_without_cast = '50';" - it violates constraint of domain dm_nums
    set term ^;
    execute block returns(var1_assignment_without_cast dm_nums, var2_assignment_without_cast dm_nums) as
    begin
      var1_assignment_without_cast = '4';
      var2_assignment_without_cast = '50';
      suspend;
    end
    ^

    -- EB where no casting is required variables are assigned immediately to text literals:
    -- Should FAIL due to "var2_assignment_without_cast = '399';" - it violates constraint of domain dm_nums
    execute block returns(var1_assignment_without_cast dm_nums, var2_assignment_without_cast dm_nums) as
    begin
      var1_assignment_without_cast = '4';
      var2_assignment_without_cast = '399';
      suspend;
    end
    ^

    -- EB where casting to domain type (varchar) is required due to integer values in right parts.
    -- Should FAIL due to "var2_cast_int_to_domain = 50;" - it violates constraint of domain dm_nums
    execute block returns(var1_cast_int_to_domain dm_nums, var2_cast_int_to_domain dm_nums) as
    begin
      var1_cast_int_to_domain = 4;
      var2_cast_int_to_domain = 50;
      suspend;
    end
    ^

    -- EB where casting to domain type (varchar) is required due to integer values in right parts.
    -- Should FAIL due to "var2_cast_int_to_domain = 399;" - it violates constraint of domain dm_nums
    execute block returns(var1_cast_int_to_domain dm_nums, var2_cast_int_to_domain dm_nums) as
    begin
      var1_cast_int_to_domain = 4;
      var2_cast_int_to_domain = 399;
      suspend;
    end
    ^
    set term ;^ 
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    ID                              1
    N                               4

    ID                              3
    N                               4
"""
expected_stderr_1 = """
    Statement failed, SQLSTATE = 23000
    validation error for column "TEST"."N", value "399"

    Statement failed, SQLSTATE = 23000
    validation error for column "TEST"."N", value "50"

    Statement failed, SQLSTATE = 23000
    validation error for column "TEST"."N", value "399"

    Statement failed, SQLSTATE = 23000
    validation error for column "TEST"."N", value "50"

    Statement failed, SQLSTATE = 42000
    validation error for variable VAR2_ASSIGNMENT_WITHOUT_CAST, value "50"
    -At block line: 4, col: 7

    Statement failed, SQLSTATE = 42000
    validation error for variable VAR2_ASSIGNMENT_WITHOUT_CAST, value "399"
    -At block line: 4, col: 7

    Statement failed, SQLSTATE = 42000
    validation error for variable VAR2_CAST_INT_TO_DOMAIN, value "50"
    -At block line: 4, col: 7

    Statement failed, SQLSTATE = 42000
    validation error for variable VAR2_CAST_INT_TO_DOMAIN, value "399"
    -At block line: 4, col: 7
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr
    assert act_1.clean_stdout == act_1.clean_expected_stdout

