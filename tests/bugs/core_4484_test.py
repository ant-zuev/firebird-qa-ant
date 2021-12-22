#coding:utf-8
#
# id:           bugs.core_4484
# title:        Description (COMMENT ON) for package procedures and functions, and its parameters
# decription:   Test verifies ability to store comments and also to encode them in UTF8
# tracker_id:   CORE-4484
# min_versions: ['3.0']
# versions:     3.0
# qmid:         

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = [('TEXT_BLOB.*', '')]

init_script_1 = """"""

db_1 = db_factory(charset='UTF8', sql_dialect=3, init=init_script_1)

test_script_1 = """
	set term ^;
	create or alter package pg_test
	as
	begin
	  procedure sp_test(i_x int) returns (o_z int);
	  function fn_test(i_x int) returns int;
	end
	^

	recreate package body pg_test
	as
	begin
	  procedure sp_test(i_x int) returns (o_z int) as
	  begin
		o_z = i_x * 2;
	  end
	  function fn_test(i_x int) returns int as
	  begin
		return i_x * 2;
	  end
	end
	^
	set term ;^
	commit;

	comment on package pg_test is 'MITÄ TÄMÄN';
	comment on procedure pg_test.sp_test is 'ÁÉÍÓÚÝ';
	comment on function pg_test.fn_test is 'ÂÊÎÔÛ';
	comment on procedure parameter pg_test.sp_test.i_x is 'ÃÑÕ ÄËÏÖÜŸ';
	comment on procedure parameter pg_test.sp_test.o_z is 'ÇŠ ΔΘΛΞΣΨΩ';
	comment on function parameter pg_test.fn_test.i_x is 'ĄĘŁŹŻ ЙЁ ЊЋЏ ĂŞŢ';
	commit;

	set list on;
	set blob all;

	select 'package itself' descr_for_what,rp.rdb$package_name obj_name, rp.rdb$description text_blob
	from rdb$packages rp
	where rp.rdb$package_name=upper('pg_test')

	union all

	select *
	from (
		select 'package proc' descr_for_what, pp.rdb$procedure_name, pp.rdb$description
		from rdb$procedures pp
		where pp.rdb$package_name=upper('pg_test')
		order by pp.rdb$procedure_name
	)

	union all

	select *
	from (
		select 'package func' descr_for_what, pf.rdb$function_name, pf.rdb$description
		from rdb$functions pf
		where pf.rdb$package_name = upper('pg_test')
		order by pf.rdb$function_name
	)

	union all

	select 'package proc pars' descr_for_what, p_name, p_memo
	from (
		select p2.rdb$parameter_name p_name, p2.rdb$description p_memo
		from rdb$procedure_parameters p2
		where p2.rdb$package_name = upper('pg_test')
		order by p2.rdb$parameter_name
	)


	union all

	select 'package func args', a_name, f_memo
	from (
		select f2.rdb$argument_name a_name,  f2.rdb$description f_memo
		from rdb$function_arguments f2
		where f2.rdb$package_name = upper('pg_test') and f2.rdb$argument_name is not null
		order by f2.rdb$argument_name
	)
	;  
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
	DESCR_FOR_WHAT                  package itself                                                      
	OBJ_NAME                        PG_TEST                                                                                                                     
	TEXT_BLOB                       0:3
	MITÄ TÄMÄN

	DESCR_FOR_WHAT                  package proc                                                        
	OBJ_NAME                        SP_TEST                                                                                                                     
	TEXT_BLOB                       0:6
	ÁÉÍÓÚÝ

	DESCR_FOR_WHAT                  package func                                                        
	OBJ_NAME                        FN_TEST                                                                                                                     
	TEXT_BLOB                       0:9
	ÂÊÎÔÛ

	DESCR_FOR_WHAT                  package proc pars                                                   
	OBJ_NAME                        I_X                                                                                                                         
	TEXT_BLOB                       0:c
	ÃÑÕ ÄËÏÖÜŸ

	DESCR_FOR_WHAT                  package proc pars                                                   
	OBJ_NAME                        O_Z                                                                                                                         
	TEXT_BLOB                       0:f
	ÇŠ ΔΘΛΞΣΨΩ

	DESCR_FOR_WHAT                  package func args                                                   
	OBJ_NAME                        I_X                                                                                                                         
	TEXT_BLOB                       0:12
	ĄĘŁŹŻ ЙЁ ЊЋЏ ĂŞŢ
"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

