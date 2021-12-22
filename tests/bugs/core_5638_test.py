#coding:utf-8
#
# id:           bugs.core_5638
# title:        Wrong result with index on case-insensitive collation using NUMERIC-SORT
# decription:   
#                   Changed collation to nn_NO (Norwegian) because there are two letters
#                   which did produce some problems in the past builds (in ~2015):
#                       'ø', 'Ø' -- U+C3B8 LATIN SMALL LETTER O WITH STROKE; U+C398 LATIN CAPITAL LETTER O WITH STROKE
#                       'æ', 'Æ' -- U+00E6 LATIN SMALL LETTER AE;  U+00C6 LATIN CAPITAL LETTER AE
#                   ###################
#                   See also: CORE-1945
#                   ###################
#               
#                   Checked on Win XP, builds:
#                   3.0.3.32813: OK, 2.000s.
#                   4.0.0.767: OK, 1.187s.
#                   NB: I intentionally excluded  'similar to' from "OR"-list of predicates because it changes plan of execution.
#                   This will be investigated later.
#                 
# tracker_id:   CORE-5638
# min_versions: ['3.0.3']
# versions:     3.0.3
# qmid:         bugs.core_5638

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0.3
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(charset='UTF8', sql_dialect=3, init=init_script_1)

test_script_1 = """
    create collation utf_sv_ci
          for utf8
          from unicode
          case insensitive
         --'locale=sv_SE'
         'locale=nn_NO'
    ;

    create collation utf_sv_ci_ns
          for utf8
          from unicode
          case insensitive
          --'locale=sv_SE;NUMERIC-SORT=1'
          'locale=nn_NO;NUMERIC-SORT=1'
    ;
    -- nn_NO
    -- da_DK

    set echo off;

    commit;

    create table test (
        f01_case_insens varchar(5) character set utf8 collate utf_sv_ci,
        f01_ci_numsort varchar(5) character set utf8 collate utf_sv_ci_ns);

    commit;

    insert into test(f01_case_insens, f01_ci_numsort) values('20', '20');
    insert into test(f01_case_insens, f01_ci_numsort) values('1', '1' );
    insert into test(f01_case_insens, f01_ci_numsort) values('2', '2' );
    insert into test(f01_case_insens, f01_ci_numsort) values('10', '10');
    insert into test(f01_case_insens, f01_ci_numsort) values('a', 'a' );
    insert into test(f01_case_insens, f01_ci_numsort) values('A', 'A' );
    insert into test(f01_case_insens, f01_ci_numsort) values('aa', 'aa');
    insert into test(f01_case_insens, f01_ci_numsort) values('Aa', 'Aa');
    insert into test(f01_case_insens, f01_ci_numsort) values('AA', 'AA');
    insert into test(f01_case_insens, f01_ci_numsort) values('b', 'b' );
    insert into test(f01_case_insens, f01_ci_numsort) values('B', 'B' );
    insert into test(f01_case_insens, f01_ci_numsort) values('o', 'o' );
    insert into test(f01_case_insens, f01_ci_numsort) values('O', 'O' );
    insert into test(f01_case_insens, f01_ci_numsort) values('z', 'z' );
    insert into test(f01_case_insens, f01_ci_numsort) values('Z', 'Z' );
    insert into test(f01_case_insens, f01_ci_numsort) values('å', 'å' );
    insert into test(f01_case_insens, f01_ci_numsort) values('Å', 'Å' );
    insert into test(f01_case_insens, f01_ci_numsort) values('ä', 'ä' );
    insert into test(f01_case_insens, f01_ci_numsort) values('Ä', 'Ä' );
    insert into test(f01_case_insens, f01_ci_numsort) values('ö', 'ö' );
    insert into test(f01_case_insens, f01_ci_numsort) values('Ö', 'Ö' );
    -- from Danish and Norwegian alphabet:
    insert into test(f01_case_insens, f01_ci_numsort) values('ø', 'Ø' );
    insert into test(f01_case_insens, f01_ci_numsort) values('æ', 'Æ' );
    commit;

    create index idx_ci on test(f01_case_insens);
    create index idx_ci_ns on test(f01_ci_numsort);
    commit; 

    set list on;
    --set plan on;
    set count on;
    
    select f01_case_insens
    from test 
    where 
        f01_case_insens in('b','å')
        or 
        f01_case_insens >= 'a' and f01_case_insens <= 'a'
        or 
        f01_case_insens between 'ö' and 'ö'
        or 
        f01_case_insens in ( 'ø', 'æ' )
        --or f01_case_insens similar to 'ä'
    order by f01_case_insens asc;
    
    select f01_ci_numsort 
    from test 
    where 
        f01_ci_numsort in('b','å')
        or 
        f01_ci_numsort >= 'a' and f01_ci_numsort <= 'a'
        or 
        f01_ci_numsort between 'ö' and 'ö'
        or 
        f01_ci_numsort in ( 'ø', 'æ' )
        -- !! "similar to" changes HERE plan to:  PLAN (TEST ORDER IDX_CI_NS) --
        --or f01_ci_numsort similar to 'ä'
    order by f01_ci_numsort asc
    ;  
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    F01_CASE_INSENS                 a
    F01_CASE_INSENS                 A
    F01_CASE_INSENS                 å
    F01_CASE_INSENS                 Å
    F01_CASE_INSENS                 æ
    F01_CASE_INSENS                 b
    F01_CASE_INSENS                 B
    F01_CASE_INSENS                 ö
    F01_CASE_INSENS                 Ö
    F01_CASE_INSENS                 ø
    Records affected: 10
    
    F01_CI_NUMSORT                  a
    F01_CI_NUMSORT                  A
    F01_CI_NUMSORT                  å
    F01_CI_NUMSORT                  Å
    F01_CI_NUMSORT                  Æ
    F01_CI_NUMSORT                  b
    F01_CI_NUMSORT                  B
    F01_CI_NUMSORT                  ö
    F01_CI_NUMSORT                  Ö
    F01_CI_NUMSORT                  Ø
    Records affected: 10
"""

@pytest.mark.version('>=3.0.3')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

