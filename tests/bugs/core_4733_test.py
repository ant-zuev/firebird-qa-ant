#coding:utf-8

"""
ID:          issue-5039
ISSUE:       5039
TITLE:       Command "Alter table <T> alter TYPE <C> <DOMAIN_WITH_NOT_NULL" does not verifies data in column <C> and makes incorrect assignments in <C> to ZERO / JULIAN_DATE / ASCII(0) for types INT, TIMESTAMP and VARCHAR
DESCRIPTION:
JIRA:        CORE-4733
"""

import pytest
from firebird.qa import *

db = db_factory()

test_script = """
    -- Tests that manipulates with NULL fields/domains and check results:
    -- CORE-1518 Adding a non-null restricted column to a populated table renders the table inconsistent
    -- CORE-4453 (Regression: NOT NULL constraint, declared in domain, does not work)
    -- CORE-4725 (Inconsistencies with ALTER DOMAIN and ALTER TABLE with DROP NOT NULL and PRIMARY KEYs)
    -- CORE-4733 (Command "Alter table <T> alter TYPE <C> <DOMAIN_WITH_NOT_NULL" does not verifies data in column <C> and makes incorrect assignments in <C> to ZERO / JULIAN_DATE / ASCII(0) for types INT, TIMESTAMP and VARCHAR)

    create domain dm_nn_int int NOT null;
    create domain dm_nn_dts timestamp NOT null;
    create domain dm_nn_utf varchar(10) character set utf8 NOT null;
    create domain dm_nn_boo boolean NOT null;

    set list on;

    create table test(num int, dts timestamp, str varchar(10) character set utf8, boo boolean);
    commit;

    insert into test values(null, null, null, null);
    commit;

    alter table test
        alter num type dm_nn_int
        ,alter dts type dm_nn_dts
        ,alter str type dm_nn_utf
        ,alter boo type dm_nn_boo
    ;
    commit;

    show table test;

    delete from test returning num, dts, str, boo;
    commit;

    alter table test
        alter num type dm_nn_int
        ,alter dts type dm_nn_dts
        ,alter str type dm_nn_utf
        ,alter boo type dm_nn_boo
    ;

    commit;
    insert into test values(null, null, null, null);
    commit;
    show table test;
"""

act = isql_act('db', test_script)

expected_stdout = """
    NUM                             INTEGER Nullable
    DTS                             TIMESTAMP Nullable
    STR                             VARCHAR(10) CHARACTER SET UTF8 Nullable
    BOO                             BOOLEAN Nullable

    NUM                             <null>
    DTS                             <null>
    STR                             <null>
    BOO                             <null>


    NUM                             (DM_NN_INT) INTEGER Not Null
    DTS                             (DM_NN_DTS) TIMESTAMP Not Null
    STR                             (DM_NN_UTF) VARCHAR(10) CHARACTER SET UTF8 Not Null
    BOO                             (DM_NN_BOO) BOOLEAN Not Null
"""

expected_stderr = """
    Statement failed, SQLSTATE = 22006
    unsuccessful metadata update
    -Cannot make field NUM of table TEST NOT NULL because there are NULLs present
    -Cannot make field DTS of table TEST NOT NULL because there are NULLs present
    -Cannot make field STR of table TEST NOT NULL because there are NULLs present
    -Cannot make field BOO of table TEST NOT NULL because there are NULLs present
    Statement failed, SQLSTATE = 23000
    validation error for column "TEST"."NUM", value "*** null ***"
"""

@pytest.mark.version('>=3.0')
def test_1(act: Action):
    act.expected_stdout = expected_stdout
    act.expected_stderr = expected_stderr
    act.execute()
    assert (act.clean_stderr == act.clean_expected_stderr and
            act.clean_stdout == act.clean_expected_stdout)

