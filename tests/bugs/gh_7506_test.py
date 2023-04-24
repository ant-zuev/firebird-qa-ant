#coding:utf-8

"""
ID:          issue-7506
ISSUE:       7506
TITLE:       Reduce output of the SHOW GRANTS command
DESCRIPTION:
    Test checks output of SHOW GRANT command when we allow access to:
    2) user;
    1) role.
NOTES:
    Checked on 5.0.0.1030.
"""
import pytest
from firebird.qa import *

tmp_user_boss = user_factory('db', name='tmp$gh_7506_john', password='123', plugin = 'Srp')
tmp_user_mngr = user_factory('db', name='tmp$gh_7506_mike', password='456', plugin = 'Srp')

tmp_role_boss = role_factory('db', name='tmp$gh_7506_boss')
tmp_role_mngr = role_factory('db', name='tmp$gh_7506_mngr')

db = db_factory()

act = python_act('db', substitutions=[('[ \t]+', ' ')])

@pytest.mark.version('>=5.0')
def test_1(act: Action, tmp_user_boss: User, tmp_user_mngr: User, tmp_role_boss: Role, tmp_role_mngr: Role, capsys):

    test_user_sql = f"""
        recreate table test(id int primary key, f01 int, f02 int, f03 int, f04 int, f05 int, f06 int);
        recreate view v_test as select * from test;

        grant delete, insert, select, update, references on test to view v_test;

        grant select on test to user {tmp_user_boss.name} with grant option;
        grant update(f01, f03) on test to user {tmp_user_boss.name};
        grant delete on test to user {tmp_user_boss.name};
        grant update(f02) on test to user {tmp_user_boss.name};
        grant insert on test to user {tmp_user_boss.name};
        grant update(f05, f06, f04) on test to user {tmp_user_boss.name} with grant option;
        grant update(f01, f03) on test to user {tmp_user_mngr.name};
        commit;

        connect '{act.db.dsn}' user {tmp_user_boss.name} password '{tmp_user_boss.password}';
        grant select on test to user {tmp_user_mngr.name};
        grant update(f05, f06, f04) on test to user {tmp_user_mngr.name};

        show grants;
    """

    act.expected_stdout = f"""
        /* Grant permissions for this database */
        GRANT DELETE, INSERT, UPDATE (F01, F02, F03) ON TEST TO USER {tmp_user_boss.name.upper()}
        GRANT SELECT, UPDATE (F04, F05, F06) ON TEST TO USER {tmp_user_boss.name.upper()} WITH GRANT OPTION
        GRANT SELECT ON TEST TO USER {tmp_user_mngr.name.upper()} GRANTED BY {tmp_user_boss.name.upper()}
        GRANT UPDATE (F01, F03) ON TEST TO USER {tmp_user_mngr.name.upper()}
        GRANT UPDATE (F04, F05, F06) ON TEST TO USER {tmp_user_mngr.name.upper()} GRANTED BY {tmp_user_boss.name.upper()}
        GRANT ALL ON TEST TO VIEW V_TEST
    """
    act.isql(input = test_user_sql, combine_output = True)
    assert act.clean_stdout == act.clean_expected_stdout
    act.reset()

    #----------------------------------------------------

    test_role_sql = f"""
        set wng off;
        revoke all on all from {tmp_user_boss.name};
        revoke all on all from {tmp_user_mngr.name};
        drop view v_test;
        commit;
        recreate table test(id int primary key, f01 int, f02 int, f03 int, f04 int, f05 int, f06 int);

        grant select on test to role {tmp_role_boss.name} with grant option;
        grant update(f01, f03) on test to role {tmp_role_boss.name};
        grant delete on test to role {tmp_role_boss.name};
        grant update(f02) on test to role {tmp_role_boss.name};
        grant insert on test to role {tmp_role_boss.name};
        grant update(f05, f06, f04) on test to role {tmp_role_boss.name} with grant option;
        grant update(f01, f03) on test to role {tmp_role_mngr.name};
        grant {tmp_role_boss.name} to {tmp_user_boss.name};
        commit;

        connect '{act.db.dsn}' user {tmp_user_boss.name} password '{tmp_user_boss.password}' role {tmp_role_boss.name};
        grant select on test to role {tmp_role_mngr.name};
        grant update(f05, f06, f04) on test to role {tmp_role_mngr.name};

        show grants;
    """

    act.expected_stdout = f"""
        /* Grant permissions for this database */
        GRANT DELETE, INSERT, UPDATE (F01, F02, F03) ON TEST TO ROLE TMP$GH_7506_BOSS
        GRANT SELECT, UPDATE (F04, F05, F06) ON TEST TO ROLE TMP$GH_7506_BOSS WITH GRANT OPTION
        GRANT SELECT ON TEST TO ROLE TMP$GH_7506_MNGR GRANTED BY TMP$GH_7506_JOHN
        GRANT UPDATE (F01, F03) ON TEST TO ROLE TMP$GH_7506_MNGR
        GRANT UPDATE (F04, F05, F06) ON TEST TO ROLE TMP$GH_7506_MNGR GRANTED BY TMP$GH_7506_JOHN
        GRANT TMP$GH_7506_BOSS TO TMP$GH_7506_JOHN
    """
    act.isql(input = test_role_sql, combine_output = True)
    assert act.clean_stdout == act.clean_expected_stdout
    act.reset()
