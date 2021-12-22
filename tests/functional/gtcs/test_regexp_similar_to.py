#coding:utf-8
#
# id:           functional.gtcs.regexp_similar_to
# title:        GTCS/tests/FB_SQL_REGEX_1, statements with SIMILAR TO. Miscelaneous tests.
# decription:   
#                   Test creates table and fills it with unicode data to be checked (field 'str'), 
#                   pattern for right part of SIMILAR TO expression and expected result.
#               
#                   Then data will be verified against pattern twise:
#                       * without casting them to UTF8 charset;
#                       * with such casting.
#               	Checked on: 4.0.0.1789
#               	
#                   ::: NOTE :::
#               	Test parameter 'database_character_set' must be SKIPPED here!
#               	Comparison of non-ascii diacritical character can bring surprising result if we skip preliminary
#               	casting of characters to UTF8. 
#               	For example consider character 'á' (small A with Acute, https://www.compart.com/en/unicode/U+00E1).
#               	1) If we do not specify charset:
#               	   select 'á' similar to '_' from rdb$database -- then this expression returns FALSE;
#               	   (this is because here SIMILAR_TO works using BYTE-basis, and 'á' has 2 bytes and this don't match '_').
#               	2) but if we do this:
#               	   select _utf8 'á' similar to '_' as  test_1 from rdb$database -- then result will be TRUE.
#               	3) all tests here do NOT check results of substring(<str> similar to <pattern>, 
#               	   see separate test for this: regexp-substring-similar_to.fbt 
#               
#               	Original test see in:
#                   https://github.com/FirebirdSQL/fbtcs/blob/master/GTCS/tests/FB_SQL_REGEX_1.output
#                
# tracker_id:   
# min_versions: ['4.0.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('[ \t]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    recreate table tests (
        id integer generated by default as identity,
        str varchar(20),
        pattern varchar(20),
        expected varchar(20)
    );

    insert into tests (str, pattern, expected) values ('aa', '(aa){1}', null);
    insert into tests (str, pattern, expected) values ('aa', '(a){1}', null);
    insert into tests (str, pattern, expected) values ('a', '(a){1}', null);
    insert into tests (str, pattern, expected) values ('A', '(a){1}', null);
    insert into tests (str, pattern, expected) values ('á', '(a){1}', null);
    insert into tests (str, pattern, expected) values ('Á', '(ã){1}', null);
    insert into tests (str, pattern, expected) values ('aa', 'a{1}', null);
    insert into tests (str, pattern, expected) values ('', '(1|2){0,}', null);
    insert into tests (str, pattern, expected) values ('', '(1|2){1,}', null);
    insert into tests (str, pattern, expected) values ('1', '(1|2){0,}', null);
    insert into tests (str, pattern, expected) values ('1', '(1|2){0,1}', null);
    insert into tests (str, pattern, expected) values ('1', '(1|2){1}', null);
    insert into tests (str, pattern, expected) values ('12', '(1|1[2]){1}', null);
    insert into tests (str, pattern, expected) values ('1212', '(1|1[2]){3,5}', null);
    insert into tests (str, pattern, expected) values ('121212', '(1|1[2]){3,5}', null);
    insert into tests (str, pattern, expected) values ('12121212', '(1|1[2]){3,5}', null);
    insert into tests (str, pattern, expected) values ('1212121212', '(1|1[2]){3,5}', null);
    insert into tests (str, pattern, expected) values ('121212121212', '(1|1[2]){3,5}', null);
    insert into tests (str, pattern, expected) values ('á', '_', null); -- <<<<<<<<<<<<<<<<<<<<<<< NB <<<<<

    insert into tests (str, pattern, expected) values ('1', '[1-53-7]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-7]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-7]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-7]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-7]', null);

    insert into tests (str, pattern, expected) values ('1', '[1-53-78-0]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-78-0]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-78-0]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-78-0]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-78-0]', null);

    insert into tests (str, pattern, expected) values ('0', '[8-0]', null);
    insert into tests (str, pattern, expected) values ('1', '[8-0]', null);
    insert into tests (str, pattern, expected) values ('8', '[8-0]', null);
    insert into tests (str, pattern, expected) values ('9', '[8-0]', null);

    insert into tests (str, pattern, expected) values ('0', '[8-09-0]', null);
    insert into tests (str, pattern, expected) values ('1', '[8-09-0]', null);
    insert into tests (str, pattern, expected) values ('8', '[8-09-0]', null);
    insert into tests (str, pattern, expected) values ('9', '[8-09-0]', null);

    insert into tests (str, pattern, expected) values ('1', '[1-53-7^4]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-7^4]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-7^4]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-7^4]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-7^4]', null);

    insert into tests (str, pattern, expected) values ('1', '[1-53-7^2-5]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-7^2-5]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-7^2-5]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-7^2-5]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-7^2-5]', null);

    insert into tests (str, pattern, expected) values ('1', '[1-53-7^2-53-6]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-7^2-53-6]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-7^2-53-6]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-7^2-53-6]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-7^2-53-6]', null);

    insert into tests (str, pattern, expected) values ('1', '[1-53-7^5-2]', null);
    insert into tests (str, pattern, expected) values ('2', '[1-53-7^5-2]', null);
    insert into tests (str, pattern, expected) values ('4', '[1-53-7^5-2]', null);
    insert into tests (str, pattern, expected) values ('6', '[1-53-7^5-2]', null);
    insert into tests (str, pattern, expected) values ('8', '[1-53-7^5-2]', null);

    set heading off;
    select 'without_cast' as msg, str, pattern, iif(str similar to pattern escape '\\', 1, 0) from tests order by id;
    
    select 'with_utf8_cast' as msg, str, pattern, iif(cast(str as varchar(20) character set utf8) similar to cast(pattern as varchar(20) character set utf8) escape '\\', 1, 0) from tests order by id;
 
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
without_cast    aa                   (aa){1}                         1 
without_cast    aa                   (a){1}                          0 
without_cast    a                    (a){1}                          1 
without_cast    A                    (a){1}                          0 
without_cast    á                    (a){1}                          0 
without_cast    Á                    (ã){1}                          0 
without_cast    aa                   a{1}                            0 
without_cast                         (1|2){0,}                       1 
without_cast                         (1|2){1,}                       0 
without_cast    1                    (1|2){0,}                       1 
without_cast    1                    (1|2){0,1}                      1 
without_cast    1                    (1|2){1}                        1 
without_cast    12                   (1|1[2]){1}                     1 
without_cast    1212                 (1|1[2]){3,5}                   0 
without_cast    121212               (1|1[2]){3,5}                   1 
without_cast    12121212             (1|1[2]){3,5}                   1 
without_cast    1212121212           (1|1[2]){3,5}                   1 
without_cast    121212121212         (1|1[2]){3,5}                   0 
without_cast    á                    _                               0 
without_cast    1                    [1-53-7]                        1 

without_cast    2                    [1-53-7]                        1 
without_cast    4                    [1-53-7]                        1 
without_cast    6                    [1-53-7]                        1 
without_cast    8                    [1-53-7]                        0 
without_cast    1                    [1-53-78-0]                     1 
without_cast    2                    [1-53-78-0]                     1 
without_cast    4                    [1-53-78-0]                     1 
without_cast    6                    [1-53-78-0]                     1 
without_cast    8                    [1-53-78-0]                     0 
without_cast    0                    [8-0]                           0 
without_cast    1                    [8-0]                           0 
without_cast    8                    [8-0]                           0 
without_cast    9                    [8-0]                           0 
without_cast    0                    [8-09-0]                        0 
without_cast    1                    [8-09-0]                        0 
without_cast    8                    [8-09-0]                        0 
without_cast    9                    [8-09-0]                        0 
without_cast    1                    [1-53-7^4]                      1 
without_cast    2                    [1-53-7^4]                      1 
without_cast    4                    [1-53-7^4]                      0 

without_cast    6                    [1-53-7^4]                      1 
without_cast    8                    [1-53-7^4]                      0 
without_cast    1                    [1-53-7^2-5]                    1 
without_cast    2                    [1-53-7^2-5]                    0 
without_cast    4                    [1-53-7^2-5]                    0 
without_cast    6                    [1-53-7^2-5]                    1 
without_cast    8                    [1-53-7^2-5]                    0 
without_cast    1                    [1-53-7^2-53-6]                 1 
without_cast    2                    [1-53-7^2-53-6]                 0 
without_cast    4                    [1-53-7^2-53-6]                 0 
without_cast    6                    [1-53-7^2-53-6]                 0 
without_cast    8                    [1-53-7^2-53-6]                 0 
without_cast    1                    [1-53-7^5-2]                    1 
without_cast    2                    [1-53-7^5-2]                    1 
without_cast    4                    [1-53-7^5-2]                    1 
without_cast    6                    [1-53-7^5-2]                    1 
without_cast    8                    [1-53-7^5-2]                    0 


with_utf8_cast    aa                   (aa){1}                         1 
with_utf8_cast    aa                   (a){1}                          0 
with_utf8_cast    a                    (a){1}                          1 
with_utf8_cast    A                    (a){1}                          0 
with_utf8_cast    á                    (a){1}                          0 
with_utf8_cast    Á                    (ã){1}                          0 
with_utf8_cast    aa                   a{1}                            0 
with_utf8_cast                         (1|2){0,}                       1 
with_utf8_cast                         (1|2){1,}                       0 
with_utf8_cast    1                    (1|2){0,}                       1 
with_utf8_cast    1                    (1|2){0,1}                      1 
with_utf8_cast    1                    (1|2){1}                        1 
with_utf8_cast    12                   (1|1[2]){1}                     1 
with_utf8_cast    1212                 (1|1[2]){3,5}                   0 
with_utf8_cast    121212               (1|1[2]){3,5}                   1 
with_utf8_cast    12121212             (1|1[2]){3,5}                   1 
with_utf8_cast    1212121212           (1|1[2]){3,5}                   1 
with_utf8_cast    121212121212         (1|1[2]){3,5}                   0 
with_utf8_cast    á                    _                               1 
with_utf8_cast    1                    [1-53-7]                        1 

with_utf8_cast    2                    [1-53-7]                        1 
with_utf8_cast    4                    [1-53-7]                        1 
with_utf8_cast    6                    [1-53-7]                        1 
with_utf8_cast    8                    [1-53-7]                        0 
with_utf8_cast    1                    [1-53-78-0]                     1 
with_utf8_cast    2                    [1-53-78-0]                     1 
with_utf8_cast    4                    [1-53-78-0]                     1 
with_utf8_cast    6                    [1-53-78-0]                     1 
with_utf8_cast    8                    [1-53-78-0]                     0 
with_utf8_cast    0                    [8-0]                           0 
with_utf8_cast    1                    [8-0]                           0 
with_utf8_cast    8                    [8-0]                           0 
with_utf8_cast    9                    [8-0]                           0 
with_utf8_cast    0                    [8-09-0]                        0 
with_utf8_cast    1                    [8-09-0]                        0 
with_utf8_cast    8                    [8-09-0]                        0 
with_utf8_cast    9                    [8-09-0]                        0 
with_utf8_cast    1                    [1-53-7^4]                      1 
with_utf8_cast    2                    [1-53-7^4]                      1 
with_utf8_cast    4                    [1-53-7^4]                      0 

with_utf8_cast    6                    [1-53-7^4]                      1 
with_utf8_cast    8                    [1-53-7^4]                      0 
with_utf8_cast    1                    [1-53-7^2-5]                    1 
with_utf8_cast    2                    [1-53-7^2-5]                    0 
with_utf8_cast    4                    [1-53-7^2-5]                    0 
with_utf8_cast    6                    [1-53-7^2-5]                    1 
with_utf8_cast    8                    [1-53-7^2-5]                    0 
with_utf8_cast    1                    [1-53-7^2-53-6]                 1 
with_utf8_cast    2                    [1-53-7^2-53-6]                 0 
with_utf8_cast    4                    [1-53-7^2-53-6]                 0 
with_utf8_cast    6                    [1-53-7^2-53-6]                 0 
with_utf8_cast    8                    [1-53-7^2-53-6]                 0 
with_utf8_cast    1                    [1-53-7^5-2]                    1 
with_utf8_cast    2                    [1-53-7^5-2]                    1 
with_utf8_cast    4                    [1-53-7^5-2]                    1 
with_utf8_cast    6                    [1-53-7^5-2]                    1 
with_utf8_cast    8                    [1-53-7^5-2]                    0 
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

