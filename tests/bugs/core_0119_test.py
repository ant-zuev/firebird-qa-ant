#coding:utf-8
#
# id:           bugs.core_0119
# title:        numeric div in dialect 3 mangles data
# decription:
#
#                   New URL: https://github.com/FirebirdSQL/firebird/issues/441
#
#                   NOTE. Results for FB 4.0 become differ from old one. Discussed with Alex, 30.10.2019.
#                   Precise value of 70000 / 1.95583 is: 35790.431683735296 (checked on https://www.wolframalpha.com )
#                   Section 'expected-stdout' was adjusted to be match for results that are issued in recent FB.
#                   Discuss with Alex see in e-mail, letters 30.10.2019.
#                   Checked on:
#                       4.0.0.1635 SS: 0.909s.
#                       3.0.5.33182 SS: 0.740s.
#                       2.5.9.27146 SC: 0.212s.
#
#                   21.06.2020, 4.0.0.2068 (see also: CORE-6337):
#                   changed subtype from 0 to 1 for cast (-70000 as numeric (18,5)) / cast (1.95583 as numeric (18,5))
#                   (after discuss with dimitr, letter 21.06.2020 08:43).
#
#                   25.06.2020, 4.0.0.2076: changed types in SQLDA from numeric to int128 // after discuss with Alex about CORE-6342.
#
#                   27.07.2021: adjusted expected* sections to results in current snapshots FB 4.x and 5.x: this is needed since fix #6874
#                   ("Literal 65536 (interpreted as int) can not be multiplied by itself w/o cast if result more than 2^63-1") because
#                   division -4611686018427387904/-0.5 does not issue error since this fix.
#                   Checked on 5.0.0.113, 4.0.1.2539.
#
# tracker_id:   CORE-0119
# min_versions: ['2.5.0']
# versions:     2.5, 4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.5
# resources: None

substitutions_1 = [('[ \t]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    -- Stdout and stderr are OK in WI-V1.5.6.5026 and all above.
    -- Number of digits in mantiss is the same both on WI- and LI-.
    set list on;
    select cast (-70000 as numeric (18,5)) / cast (1.95583 as numeric (18,5)) as result from rdb$database;
    select (-4611686018427387904)/-0.5 from rdb$database;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    RESULT                          -35790.4316837350
"""

expected_stderr_1 = """
    Statement failed, SQLSTATE = 22003
    arithmetic exception, numeric overflow, or string truncation
    -numeric value is out of range
"""

@pytest.mark.version('>=2.5,<4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr
    assert act_1.clean_stdout == act_1.clean_expected_stdout

# version: 4.0
# resources: None

substitutions_2 = [('^((?!(sqltype|DIV_RESULT)).)*$', ''), ('[ \t]+', ' '), ('.*alias.*', '')]

init_script_2 = """"""

db_2 = db_factory(sql_dialect=3, init=init_script_2)

test_script_2 = """
    set list on;
    set sqlda_display on;
    select cast (-70000 as numeric (18,5)) / cast (1.95583 as numeric (18,5)) as div_result_1 from rdb$database;

    -- doc\\sql.extensions\\README.data_types:
    --	- QUANTIZE - has two DECFLOAT arguments. The returned value is first argument scaled using
    --		second value as a pattern. For example QUANTIZE(1234, 9.999) returns 1234.000.

    select QUANTIZE(cast(-70000 as decfloat(34)) / cast (1.95583 as decfloat(34)), 9.9999999999) as div_result_2 from rdb$database;
    select (-4611686018427387904)/-0.5 div_result_3 from rdb$database;
"""

act_2 = isql_act('db_2', test_script_2, substitutions=substitutions_2)

expected_stdout_2 = """
    01: sqltype: 32752 INT128 scale: -10 subtype: 1 len: 16
    DIV_RESULT_1 -35790.4316837352

    01: sqltype: 32762 DECFLOAT(34) scale: 0 subtype: 0 len: 16
    DIV_RESULT_2 -35790.4316837353

    01: sqltype: 32752 INT128 scale: -1 subtype: 0 len: 16
    DIV_RESULT_3 9223372036854775808.0
"""

@pytest.mark.version('>=4.0')
def test_2(act_2: Action):
    act_2.expected_stdout = expected_stdout_2
    act_2.execute()
    assert act_2.clean_stdout == act_2.clean_expected_stdout
