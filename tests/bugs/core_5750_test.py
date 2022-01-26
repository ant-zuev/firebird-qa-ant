#coding:utf-8

"""
ID:          issue-6013
ISSUE:       6013
TITLE:       Date-time parsing is very weak
DESCRIPTION:
  Parser changed after following fixes:
    - CORE-6427 - Whitespace as date separator causes conversion error.
    - CORE-6429 - Timezone offset in timestamp/time literal and CAST should follow SQL standard syntax only.
  See: https://github.com/FirebirdSQL/firebird/commit/ff37d445ce844f991242b1e2c1f96b80a5d1636d
  Adjusted expected stdout/stderr after discuss with Adriano.
JIRA:        CORE-5750
"""

import pytest
from firebird.qa import *

db = db_factory()

test_script = """
    set heading off;
    --set echo on;

    -- All these must fail:
    select timestamp '2018-01-01 10 20 30' from rdb$database;
    select timestamp '2018-01-01 10,20,30 40' from rdb$database;
    select timestamp '31.05.2017 1:2:3.4567' from rdb$database;
    select timestamp '31/05/2017 2:3:4.5678' from rdb$database;
    ------------------------------------------------------------

    -- Date components separator may be a single one (first and second occurence): dash, slash or dot.
    select date '2018-01-31' from rdb$database;
    select date '2018/01/31' from rdb$database;
    select date '2018.01.31' from rdb$database;
    select date '2018' from rdb$database;
    select date '2018,01,31' from rdb$database;
    select date '2018/01.31' from rdb$database;
    select date '2018 01 31' from rdb$database;

    -- Time components (hours to minutes to seconds) separator may be colon.
    select time '10:29:39' from rdb$database;
    select time '10/29/39' from rdb$database;
    select time '10.29.39' from rdb$database;
    select time '10-29-39' from rdb$database;
    select time '10 29 39' from rdb$database;

    -- Seconds to fractions separator may be dot.
    select time '7:3:1.' from rdb$database;
    select time '7:3:2.1238' from rdb$database;
    select time '7:3:3,1238' from rdb$database;

    -- There could *NOT* be any separator (other than spaces) between date and time.
    select timestamp '2018-01-01T01:02:03.4567' from rdb$database;
    select timestamp '31.05.2017       11:22:33.4455' from rdb$database;
    select timestamp '31.05.2017
    22:33:44.5577' from rdb$database;
"""

act = isql_act('db', test_script)

expected_stdout = """
    2017-05-31 01:02:03.4567
    2018-01-31
    2018-01-31
    2018-01-31
    2018-01-31
    10:29:39.0000
    07:03:01.0000
    07:03:02.1238
    2017-05-31 11:22:33.4455
"""

expected_stderr = """
    Statement failed, SQLSTATE = 22009
    Invalid time zone region: 20 30

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: ,20,30 40

    Statement failed, SQLSTATE = 22018
    conversion error from string "31/05/2017 2:3:4.5678"

    Statement failed, SQLSTATE = 22018
    conversion error from string "2018"

    Statement failed, SQLSTATE = 22018
    conversion error from string "2018,01,31"

    Statement failed, SQLSTATE = 22018
    conversion error from string "2018/01.31"

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: /29/39

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: .39

    Statement failed, SQLSTATE = 22009
    Invalid time zone offset: -29-39 - must use format +/-hours:minutes and be between -14:00 and +14:00

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: 29 39

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: ,1238

    Statement failed, SQLSTATE = 22009
    Invalid time zone region: T01:02:03.4567

    Statement failed, SQLSTATE = 22009
    Invalid time zone region:
        22:33:44.5577
"""

@pytest.mark.version('>=4.0')
def test_1(act: Action):
    act.expected_stdout = expected_stdout
    act.expected_stderr = expected_stderr
    act.execute()
    assert (act.clean_stderr == act.clean_expected_stderr and
            act.clean_stdout == act.clean_expected_stdout)
