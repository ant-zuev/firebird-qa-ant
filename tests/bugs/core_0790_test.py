#coding:utf-8
#
# id:           bugs.core_0790
# title:        Alter view
# decription:
# tracker_id:   CORE-790
# min_versions: ['2.5.0']
# versions:     2.5.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5.0
# resources: None

substitutions_1 = []

init_script_1 = """create table users (
    id integer,
    name varchar(20),
    passwd varchar(20)
);

create view v_users as
    select name from users;
commit;"""

db_1 = db_factory(page_size=4096, sql_dialect=3, init=init_script_1)

test_script_1 = """alter view v_users (id, name, passwd ) as
    select id, name, passwd  from users;
commit;
show view v_users;
create view v_users_name as
    select name from v_users;
commit;
alter view v_users (id, name ) as
    select id, name from users;
commit;
show view v_users;
show view v_users_name;


"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """Database:  localhost:C:/fbtest2/tmp/bugs.core_0790.fdb, User: SYSDBA
SQL> CON> SQL> SQL> ID                              INTEGER Nullable
NAME                            VARCHAR(20) Nullable
PASSWD                          VARCHAR(20) Nullable
View Source:
==== ======

    select id, name, passwd  from users
SQL> CON> SQL> SQL> CON> SQL> SQL> ID                              INTEGER Nullable
NAME                            VARCHAR(20) Nullable
View Source:
==== ======

    select id, name from users
SQL> NAME                            VARCHAR(20) Nullable
View Source:
==== ======

    select name from v_users
SQL> SQL> SQL> SQL>
"""

@pytest.mark.version('>=2.5.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

