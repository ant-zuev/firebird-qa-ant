#coding:utf-8
#
# id:           bugs.core_4464
# title:        Duplicate tags for CREATE/ALTER USER not handled correctly
# decription:   
#                  Refactored 16-may-2018 for usage plugin Srp.
#                  Checked on:
#                    30Cs, build 3.0.4.32972: OK, 1.734s.
#                    30SS, build 3.0.4.32972: OK, 1.156s.
#                    40CS, build 4.0.0.955: OK, 2.516s.
#                    40SS, build 4.0.0.977: OK, 1.656s.
#                
# tracker_id:   CORE-4464
# min_versions: ['3.0']
# versions:     3.0
# qmid:         

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = [('=\\+', '')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set term ^;
    execute block as
    begin
        begin
        execute statement 'drop user tmp$c4464_1 using plugin Srp' with autonomous transaction;
            when any do begin end
        end
     
        begin
        execute statement 'drop user tmp$c4464_2 using plugin Srp' with autonomous transaction;
            when any do begin end
        end

        begin
        execute statement 'drop user tmp$c4464_3 using plugin Srp' with autonomous transaction;
            when any do begin end
        end
    end^
    set term ;^
    commit;

    --set echo on;
    --show users;

    -- Should fail with:
    --    Statement failed, SQLSTATE = 42702
    --    Duplicated user attribute INITNAME
    -- - because of duplicate specification of added attr. 'initname':
    create user tmp$c4464_1 password '123'
        using plugin Srp
        tags (initname='Ozzy', surname='Osbourne', groupname='Black Sabbath', initname='John')
    ;
    rollback; -- !! --

    -- Should work OK:
    create user tmp$c4464_1 password '123' 
        using plugin Srp
        tags (initname='John', surname='Osbourne', groupname='Black Sabbath', aka='Ozzy');
    ;

    -- Should work OK:
    create user tmp$c4464_2 password '456' 
        using plugin Srp
        tags (initname='Ian', surname='Gillan', groupname='Deep Purple')
    ;

    create user tmp$c4464_3 password '789'
        using plugin Srp
    ;
    commit;


    -- Should fail with:
    --    Statement failed, SQLSTATE = 42702
    --    Duplicated user attribute INITNAME
    -- - because of duplicate specification of deleted attr. 'initname':
    alter user tmp$c4464_2 
        using plugin Srp 
        tags (drop initname, drop surname, drop groupname, drop initname);
    commit;

    -- Should fail with:
    --    Statement failed, SQLSTATE = 42702
    --    Duplicated user attribute INITNAME
    -- - because of duplicate tag to be added: initname
    alter user tmp$c4464_3 
        using plugin Srp 
        tags (initname='Ozzy', surname='Osbourne', groupname='Black Sabbath', initname='Foo');
    commit;

 
    -- Should fail with:
    --    Statement failed, SQLSTATE = 42702
    --    Duplicated user attribute INITNAME
    -- - because of duplicate specification of removed and than added attr. 'initname':
    alter user tmp$c4464_3 
        using plugin Srp 
        tags (drop initname, surname='Gillan', groupname='Deep Purple', initname='Ian');
    commit;

    set width usrname 12;
    set width tag_key 20;
    set width tag_val 25;
    set width sec_plg 7;
    select
         u.sec$user_name as usrname
        ,a.sec$key tag_key
        ,a.sec$value as tag_val
        ,sec$plugin sec_plg
    from sec$users u
    left join sec$user_attributes a using( sec$user_name, sec$plugin )
    where u.sec$user_name in ( upper('tmp$c4464_1'), upper('tmp$c4464_2'), upper('tmp$c4464_3') )
    order by 1,2,3;
    commit;

    drop user tmp$c4464_1 using plugin Srp;
    drop user tmp$c4464_2 using plugin Srp;
    drop user tmp$c4464_3 using plugin Srp;
    commit;

"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    USRNAME      TAG_KEY              TAG_VAL                   SEC_PLG 
    ============ ==================== ========================= ======= 
    TMP$C4464_1  AKA                  Ozzy                      Srp     
    TMP$C4464_1  GROUPNAME            Black Sabbath             Srp     
    TMP$C4464_1  INITNAME             John                      Srp     
    TMP$C4464_1  SURNAME              Osbourne                  Srp     
    TMP$C4464_2  GROUPNAME            Deep Purple               Srp     
    TMP$C4464_2  INITNAME             Ian                       Srp     
    TMP$C4464_2  SURNAME              Gillan                    Srp     
    TMP$C4464_3  <null>               <null>                    Srp     
"""
expected_stderr_1 = """
    Statement failed, SQLSTATE = 42702
    Duplicated user attribute INITNAME

    Statement failed, SQLSTATE = 42702
    Duplicated user attribute INITNAME

    Statement failed, SQLSTATE = 42702
    Duplicated user attribute INITNAME

    Statement failed, SQLSTATE = 42702
    Duplicated user attribute INITNAME
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr
    assert act_1.clean_stdout == act_1.clean_expected_stdout

