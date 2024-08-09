#coding:utf-8

"""
ID:          issue-8015
ISSUE:       https://github.com/FirebirdSQL/firebird/issues/8015
TITLE:       Add multi-character TRIM function
DESCRIPTION:
NOTES:
    [26.03.2024] pzotov
    Test verifies only basic feature of BTRIM() function:
        * proper work when source text is specified in different character sets (utf8 and several single-byte charsets are checked);
        * proper work when text contains diacrits and/or accents and <trim character>  are specified in different case and/or accents;
        * proper work for both varchar and blob datatypes.
    Other features (and also functions LTRIM, RTRIM) will be verified in other tests.
    Checked on 6.0.0.301 (Windows).
"""

import pytest
from firebird.qa import *
import locale

db = db_factory(charset='utf8')

test_script = """
    set bail on;
    create collation nm_utf8_ci_ai for utf8 from unicode no pad case insensitive accent insensitive;
    create domain dm_txt_utf8_ci_ai varchar(50) character set utf8 collate nm_utf8_ci_ai;
    create domain dm_blb_utf8_ci_ai blob character set utf8 collate nm_utf8_ci_ai;

    create table test_vchr(
        id int generated by default as identity primary key
       ,txt_utf8 varchar(50) character set utf8
       ,txt_1250 varchar(50) character set win1250 -- central europe
       ,txt_1251 varchar(50) character set win1251 -- cyrillic
       ,txt_1252 varchar(50) character set win1252 -- ~ ISO-8859-1; except for the code points 128-159 (0x80-0x9F).
       ,txt_1253 varchar(50) character set win1253 -- greek
       ,txt_1254 varchar(50) character set win1254 -- turkish
       ,txt_1257 varchar(50) character set win1257 -- baltic
       ,txt_utf8_ci_ai dm_txt_utf8_ci_ai 
       ,txt_estonian_ci_ai varchar(50) character set iso8859_1 collate ES_ES_CI_AI
       ,txt_czech_ci_ai varchar(50) character set win1250 collate WIN_CZ_CI_AI
    );
    -------------------------------------------------

    insert into test_vchr (
        txt_utf8
       ,txt_1250
       ,txt_1251
       ,txt_1252
       ,txt_1253
       ,txt_1254
       ,txt_1257
       ,txt_utf8_ci_ai
       ,txt_estonian_ci_ai
       ,txt_czech_ci_ai
    ) values (
        'შობას გილოცავთ'          -- georgian
        ,'boldog Karácsonyt'       --  hungarian
        ,'з Різдвом'               -- ukrainian
        ,'Joyeux noël'             -- french
        ,'Καλό απόγευμα'           -- greek
        ,'Teşekkür ederim'         -- turkish 
        ,'Priecīgus Ziemassvētkus' -- latvian
        ,'Täze ýyl gutly bolsun'   -- turkmenian; will be used to check ability to use characters with diff case and accents
        ,'häid jõule'              -- estonian; will be used to check ability to use characters with diff case and accents
        ,'veselé Vánoce'           -- czech; will be used to check ability to use characters with diff case and accents
    );

    set list on;
    select
        btrim(txt_utf8, 'ოშათვ') as btrim_utf8
        ,btrim(txt_1251, 'з м') as btrim_1250
        ,btrim(txt_1252, 'oëlJ') as btrim_1252
        ,btrim(txt_1253, 'αμΚ') as btrim_1253
        ,btrim(txt_1254, 'eiTmşr') as btrim_1254
        ,btrim(txt_1257, 'ktPrciīeēuvs') as btrim_1257
        ,btrim(txt_utf8_ci_ai, 'ÜYETAÑZ ') as btrim_txt_utf8_ci_ai
        ,btrim(txt_estonian_ci_ai, 'AH') as btrim_txt_estonian_ci_ai
        ,btrim(txt_czech_ci_ai, 'ELVS ') as btrim_txt_czech_ci_ai
    from test_vchr
    order by id
    ;
    commit;
    
    recreate table test_blob(
        id int generated by default as identity primary key
       ,txt_utf8 blob character set utf8
       ,txt_1250 blob character set win1250 -- central europe
       ,txt_1251 blob character set win1251 -- cyrillic
       ,txt_1252 blob character set win1252 -- ~ ISO-8859-1; except for the code points 128-159 (0x80-0x9F).
       ,txt_1253 blob character set win1253 -- greek
       ,txt_1254 blob character set win1254 -- turkish
       ,txt_1257 blob character set win1257 -- baltic
       ,txt_utf8_ci_ai dm_blb_utf8_ci_ai
       ,txt_estonian_ci_ai blob character set iso8859_1 collate ES_ES_CI_AI
       ,txt_czech_ci_ai blob character set win1250 collate WIN_CZ_CI_AI
    );
    
    -------------------------------------------------

    insert into test_blob (
        txt_utf8
       ,txt_1250
       ,txt_1251
       ,txt_1252
       ,txt_1253
       ,txt_1254
       ,txt_1257
       ,txt_utf8_ci_ai
       ,txt_estonian_ci_ai
       ,txt_czech_ci_ai
    ) values (
        'შობას გილოცავთ'
        ,'boldog Karácsonyt'
        ,'з Різдвом'
        ,'Joyeux noël'
        ,'Καλό απόγευμα'
        ,'Teşekkür ederim'
        ,'Priecīgus Ziemassvētkus'
        ,'Täze ýyl gutly bolsun'
        ,'häid jõule'
        ,'veselé Vánoce'
    );

    select
        btrim(txt_utf8, 'ოშათვ') as blob_id_btrim_utf8
        ,btrim(txt_1251, 'з м') as blob_id_btrim_1250
        ,btrim(txt_1252, 'oëlJ') as blob_id_btrim_1252
        ,btrim(txt_1253, 'αμΚ') as blob_id_btrim_1253
        ,btrim(txt_1254, 'eiTmşr') as blob_id_btrim_1254
        ,btrim(txt_1257, 'ktPrciīeēuvs') as blob_id_btrim_1257
        ,btrim(txt_utf8_ci_ai, 'ÜYETAÑZ ') as blob_id_btrim_txt_utf8_ci_ai
        ,btrim(txt_estonian_ci_ai, 'AH') as blob_id_btrim_txt_estonian_ci_ai
        ,btrim(txt_czech_ci_ai, 'ELVS ') as blob_id_btrim_txt_czech_ci_ai
    from test_blob
    order by id
    ;   
"""

act = isql_act('db', test_script, substitutions=[('[ \t]+', ' '), ('BLOB_ID_.*','')])

expected_stdout = """
    BTRIM_UTF8                      ბას გილოც
    BTRIM_1250                      Різдво
    BTRIM_1252                      yeux n
    BTRIM_1253                      λό απόγευ
    BTRIM_1254                      kkür ed
    BTRIM_1257                      gus Ziema
    BTRIM_TXT_UTF8_CI_AI            l gutly bols
    BTRIM_TXT_ESTONIAN_CI_AI        id jõule
    BTRIM_TXT_CZECH_CI_AI           ánoc
    
    ბას გილოც
    Різдво
    yeux n
    λό απόγευ
    kkür ed
    gus Ziema
    l gutly bols
    id jõule
    ánoc    
"""

@pytest.mark.version('>=6.0.0')
def test_1(act: Action):
    act.expected_stdout = expected_stdout
    # NB: io_enc must be 'utf8' because 'act.execute' essentially calls isql using PIPE
    # with sending as input text from test_script.
    # We must NOT specify here locale.getpreferredencoding() otherwise charmap error
    # will raise in case if our system has non-ascii locale ('cp1251') etc.
    act.execute(combine_output = True, charset = 'utf8', io_enc = 'utf8')
    assert act.clean_stdout == act.clean_expected_stdout
