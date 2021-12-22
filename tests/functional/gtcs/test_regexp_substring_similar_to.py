#coding:utf-8
#
# id:           functional.gtcs.regexp_substring_similar_to
# title:        GTCS/tests/FB_SQL_REGEX_1 SUBSTRING ; Miscelaneous tests of <str> SIMILAR TO <pattern>.
# decription:   
#                   Test creates table and fills it with unicode data to be checked (field 'str'), pattern and 
#               	performs output of SUBSTRING( <str> SIMILAR <pattern> ).
#               	Also, some additional examples presents for other checks.
#               	Checked on: 4.0.0.1789
#               
#               	Original test see in:
#                   https://github.com/FirebirdSQL/fbtcs/blob/master/GTCS/tests/FB_SQL_REGEX_1.script
#                
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
	create sequence g;

    set heading off;

	insert into tests(id, str, pattern, expected) values ( gen_id(g,1), '(12) 3456-7890', '\\(__\\) \\"%\\-%\\"', '3456-7890');
	insert into tests(id, str, pattern, expected) values ( gen_id(g,1), '(12) 3456-7890', '\\(__\\) \\"%x%\\"', null);
	insert into tests(id, str, pattern, expected) values ( gen_id(g,1), 'abc123abc456', '\\"%\\"abc%6', 'abc123');
	insert into tests(id, str, pattern, expected) values ( gen_id(g,1), 'abc123abc456', '\\"%\\"abc%7', null);
	commit;
	select id, substring(str similar pattern escape '\\'), expected from tests;
	
	select gen_id(g,1), substring('(12) 3456-7890' similar '\\(__\\) \\"%\\-%\\"' escape '\\') from rdb$database; -- 3.0.6: invalid pattern
	select gen_id(g,1), substring('abc123abc456' similar '\\"%\\"abc%6' escape '\\') from rdb$database;
	select gen_id(g,1), substring('abc123abc456' similar '\\"%\\"abc%7' escape '\\') from rdb$database;

	select gen_id(g,1), substring('asds 12.34 asd' similar '% \\"[\\+\\-]?[0-9]*([0-9].|.[0-9])?[0-9]*\\" %' escape '\\') from rdb$database;
	select gen_id(g,1), substring('asd 5 s 1234 a 12 sd' similar '% \\"[\\+\\-]?[0-9]*\\" %' escape '\\') from rdb$database;
	select gen_id(g,1), substring('a 1 b' similar '%#"[0-9]*#" %' escape '#') from rdb$database;

	select gen_id(g,1), substring('çaaaЫxЫЫcccç' similar '%aaa#"%#"ccc%' escape '#') from rdb$database;
	select gen_id(g,1), substring(cast('aaaЫxЫЫccc' as varchar(15) character set win1251) similar '%aaa#"%#"ccc%' escape '#') from rdb$database;
	select gen_id(g,1), cast(substring(cast(_utf8 'aaaЫxЫЫccc' as varchar(10) character set win1251) similar '%aaa#"%#"ccc%' escape '#') as varchar(10) character set utf8) from rdb$database;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
	 1 3456-7890            3456-7890            
	 2 <null>               <null>               
	 3 abc123               abc123               
	 4 <null>               <null>               
	
	 5 3456-7890      
	 6 abc123       
	 7 <null>       
	
	 8 12.34          
	 9 5                    
	10 		  
	11 ЫxЫЫ           
	12 ЫxЫЫ         
	13 ЫxЫЫ     
	
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

