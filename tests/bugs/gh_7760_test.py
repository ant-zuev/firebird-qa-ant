#coding:utf-8

"""
ID:          issue-7760
ISSUE:       https://github.com/FirebirdSQL/firebird/issues/7760
TITLE:       Parameters inside the IN list may cause a string truncation error
DESCRIPTION:
NOTES:
    [28.09.2023] pzotov
    Confirmed bug on 5.0.0.1225, 6.0.0.49:
        gdscodes: (335544321, 335544914, 335545033)
        exc test: arithmetic ... or string truncation / ... / -expected length 0, actual 1
    Checked on 6.0.0.57, 5.0.0.1233, 4.0.4.2995, 3.0.12.33713.
    Thanks to dimitr for reproducible example.
"""

import pytest
from firebird.qa import *
from firebird.driver import tpb, Isolation, TraAccessMode, DatabaseError

init_sql = """
    create domain dm_test char(1) default 'M' not null check (value in ('S', 'V', 'M')); -- collate PXW_HUNDC;
    create table test (
         id int generated by default as identity constraint test_pk primary key
        ,sv dm_test
        ,sw dm_test
    );
    insert into test(sv, sw) values('S', 'S');
    insert into test(sv, sw) values('V', 'V');
    insert into test(sv, sw) values('M', 'M');
    commit;
    set term ^;
    create procedure sp_test(a_sv type of column test.sv) returns (id int, sw type of column test.sv) as
    begin
        for 
            -- execute statement  (q'{ select id, sw from test where sv = 'M' or sv  = ? }' ) -- WORKS fine.
            execute statement (q'{ select id, sw from test where sv in ('M', ?) }' ) (:a_sv) -- FAILED before fix.
            into id, sw
        do
            suspend; -- FAILS.
    end
    ^
    set term ;^
    commit;
"""
db = db_factory(init = init_sql, charset = 'win1250')
act = python_act('db')
#act = isql_act('db', test_script)

@pytest.mark.version('>=3.0')
def test_1(act: Action, capsys):

    with act.db.connect(charset = 'utf8') as con:
        cur = con.cursor()
        try:
            cur.execute("select id, sw from sp_test('S') order by id")
            for r in cur:
                print(r[0],r[1])
        except DatabaseError as exc:
            print('UNEXPECTED ERROR. Could not run cursor:')
            print(exc.gds_codes)
            print(exc.__str__())

    expected_stdout = """
        1 S
        3 M
    """
    act.expected_stdout = expected_stdout
    act.stdout = capsys.readouterr().out
    assert act.clean_stdout == act.clean_expected_stdout
