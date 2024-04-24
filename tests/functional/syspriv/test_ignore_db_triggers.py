#coding:utf-8

"""
ID:          syspriv.ignore-db-triggers
TITLE:       Check ability of non-sysdba and non-owner to ignore DB triggers
DESCRIPTION:
    Test creates two users (tmp_senior, tmp_junior) and role with IGNORE_DB_TRIGGERS system privilege.
    This role is granted as default to tmp_senior (and only to him).
    Also, all types of DB-level triggers are created and each of them appends ros into 'tlog' table.
    Then we run ISQL with requirement to skip execution of DB triggers ('-nod' switch).
    ISQL first make attempt to connect as tmp_junior and this must fail with SQLSTATE = 28000.
    Then ISQL makes connection as tmp_junior and does commit, implicit start of TX, select, rollback and
    implicit disconnect followed by connection by SYSDBA.
    All these operations (performed by tmp_senior) must ignore DB-level triggers and this is checked 
    by query to the table TLOG: it must remain empty.
    Finally, we REVOKE role from tmp_senior and try to make connection again, using '-nod' switch.
    This must fail with SQLSTATE = 28000 ("Unable to perform ... / ... IGNORE_DB_TRIGGERS is missing")
NOTES:
    [24.04.2024] pzotov
    This system privilege also is used in following tests:
        test_change_header_settings.py ; test_change_shutdown_mode.py ; test_use_gstat_utility.py
    Checked on: 6.0.0.325, 5.0.1.1383, 4.0.5.3086.
"""

import locale
import pytest
from firebird.qa import *

init_script = """
    set wng off;
    set bail on;

    recreate table tlog (
         id int generated by default as identity
        ,event_name varchar(50)
        ,conn_user varchar(32) default current_user
        ,conn_role varchar(32) default current_role
    );

    create or alter view v_check as
    select
         current_user as who_ami
        ,r.rdb$role_name
        ,rdb$role_in_use(r.rdb$role_name) as RDB_ROLE_IN_USE
        ,r.rdb$system_privileges
    from rdb$roles r
    where r.rdb$system_flag is distinct from 1
    ;
    commit;
    grant select on v_check to public;

    set term ^;
    execute block as
    begin
        rdb$set_context('USER_SESSION', 'INIT_SQL', 1);
    end
    ^
    create or alter trigger trg_attach active on connect as
    begin
        if ( rdb$get_context('USER_SESSION', 'INIT_SQL') is null ) then
            insert into tlog(event_name) values ('attach');
    end
    ^
    create or alter trigger trg_detach active on disconnect as
    begin
        if ( rdb$get_context('USER_SESSION', 'INIT_SQL') is null ) then
            insert into tlog(event_name) values ('detach');
    end
    ^
    create or alter trigger trg_tx_start active on transaction start as
    begin
        if ( rdb$get_context('USER_SESSION', 'INIT_SQL') is null ) then
            insert into tlog(event_name) values ('tx_start');
    end
    ^
    create or alter trigger trg_tx_commit active on transaction commit as
    begin
        if ( rdb$get_context('USER_SESSION', 'INIT_SQL') is null ) then
            insert into tlog(event_name) values ('tx_commit');
    end
    ^
    create or alter trigger trg_tx_rollback active on transaction rollback as
    begin
        if ( rdb$get_context('USER_SESSION', 'INIT_SQL') is null ) then
            insert into tlog(event_name) values ('tx_rolback');
    end
    ^
    set term ;^
    commit;
"""

db = db_factory(init = init_script)
act = python_act('db', substitutions=[('[ \t]+', ' ')])

tmp_junior = user_factory('db', name='tmp$junior', password='123', plugin = 'Srp')
tmp_senior = user_factory('db', name='tmp$senior', password='456', plugin = 'Srp')
tmp_role = role_factory('db', name='tmp$role_ignore_dbtrg')

@pytest.mark.version('>=4.0')
def test_1(act: Action, tmp_junior: User, tmp_senior: User, tmp_role: Role):

    test_script = f"""
        set wng off;
        set list on;
        set count on;
        set bail on;

        set term ^;
        execute block as
        begin
            rdb$set_context('USER_SESSION', 'INIT_SQL', 1);
        end
        ^
        set term ;^
        alter role {tmp_role.name}
            set system privileges to
                IGNORE_DB_TRIGGERS
        ;
        revoke all on all from {tmp_senior.name};
        grant default {tmp_role.name} to user {tmp_senior.name};
        commit;
        set bail off;
        ----------------------------------------------------------------------
        connect '{act.db.dsn}' user {tmp_junior.name} password '{tmp_junior.password}';
        rollback;
        connect '{act.db.dsn}' user {tmp_senior.name} password '{tmp_senior.password}';
        commit;
        select 'check-1a' as msg, v.* from v_check v;
        rollback;
        ----------------------------------------------------------------------
        connect '{act.db.dsn}' user {act.db.user} password '{act.db.password}';
        select 'check-1b' as msg, g.* from rdb$database left join tlog g on upper(g.conn_user) is distinct from upper('{act.db.user}');
    """

    act.expected_stdout = f"""
        Statement failed, SQLSTATE = 28000
        Unable to perform operation
        -System privilege IGNORE_DB_TRIGGERS is missing

        MSG check-1a
        WHO_AMI TMP$SENIOR
        RDB$ROLE_NAME TMP$ROLE_IGNORE_DBTRG
        RDB_ROLE_IN_USE <true>
        RDB$SYSTEM_PRIVILEGES 0040000000000000
        Records affected: 1

        MSG check-1b
        ID <null>
        EVENT_NAME <null>
        CONN_USER <null>
        CONN_ROLE <null>
        Records affected: 1
    """
    act.isql(switches=['-n', '-q', '-nod'], input = test_script, combine_output = True, io_enc = locale.getpreferredencoding())
    assert act.clean_stdout == act.clean_expected_stdout
    act.reset()

    ###################################################

    test_script = f"""
        set list on;
        set count on;
        set bail on;

        set term ^;
        execute block as
        begin
            rdb$set_context('USER_SESSION', 'INIT_SQL', 1);
        end
        ^
        set term ;^
        alter role {tmp_role.name}
            set system privileges to
                IGNORE_DB_TRIGGERS
        ;
        revoke default {tmp_role.name} from user {tmp_senior.name};
        commit;
        set bail off;
        ----------------------------------------------------------------------
        connect '{act.db.dsn}' user {tmp_senior.name} password '{tmp_senior.password}';
        commit;
        select 'check-2a' as msg, v.* from v_check v;
        rollback;
        ----------------------------------------------------------------------
        connect '{act.db.dsn}' user {act.db.user} password '{act.db.password}';
        select 'check-2b' as msg, g.* from rdb$database left join tlog g on upper(g.conn_user) is distinct from upper('{act.db.user}');
    """

    act.expected_stdout = f"""
        Statement failed, SQLSTATE = 28000
        Unable to perform operation
        -System privilege IGNORE_DB_TRIGGERS is missing

        MSG check-2b
        ID <null>
        EVENT_NAME <null>
        CONN_USER <null>
        CONN_ROLE <null>
        Records affected: 1
    """
    act.isql(switches=['-n', '-q', '-nod'], input = test_script, combine_output = True, io_enc = locale.getpreferredencoding())
    assert act.clean_stdout == act.clean_expected_stdout
    act.reset()

