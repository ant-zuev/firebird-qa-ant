#coding:utf-8
#
# id:           bugs.core_5921
# title:        Provide information about Global Commit Number, Commit Number of currently used database snapshot (if any) and Commit Numbers assigned to the committed transactions
# decription:   
#                   From doc\\sql.extensions\\README.builtin_functions.txt about rdb$get_transaction_cn() function:
#                   ===
#                     ... numbers returned by RDB$GET_TRANSACTION_CN could have values below:
#               	-2 - transaction is dead (rolled back)
#               	-1 - transaction is in limbo
#               	 0 - transaction is active,
#               	 1 - transaction committed before database started or less than OIT
#               	>1 - transaction committed after database started
#               	NULL - given transaction number is NULL or greater than database Next Transaction
#                   ===
#                   Checked on: 4.0.0.1218, 2.578 s.
#                   ::: NB :::
#                   This ISQL-based test does NOT verify cases when tx is dead or in limbo.
#                   Perhaps, Python-based implementation is required and will be created later.
#               
#                   05.03.2019: renamed RDB$GET_CONTEXT('SYSTEM', 'SNAPSHOT_CN') to RDB$GET_CONTEXT('SYSTEM', 'SNAPSHOT_NUMBER') -- see CORE-6016. Checked on 4.0.0.1455
#               
#                   09.11.2019: added section with substitutions because GET_OIT_CN can differ in SS vs CS: 9 and 10.
#                   Checked on:
#                       4.0.0.1646 SS: 1.249s.
#                       4.0.0.1637 SC: 1.532s.
#                       4.0.0.1633 CS: 1.576s.
#                
# tracker_id:   CORE-5921
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('[ \t]+', ' '), ('GET_OIT_CN[ \t]+[\\d]+', 'GET_OIT_CN <digit>')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;
    set term ^;
    create or alter procedure sp_set_tx_ctx( a_ctx_var_name varchar(80) ) as
    begin
        rdb$set_context('USER_SESSION', :a_ctx_var_name, current_transaction);
    end
    ^
    set term ;^
    commit;

    set list on;
    execute procedure sp_set_tx_ctx('tx_a');

    select 
         iif( tx_a < tx_oit, 'For TX < OIT', iif( tx_a = tx_oit, 'For OIT', 'For TX > OIT') ) as msg_a
        ,rdb$get_transaction_cn( tx_a ) as get_tx_a_cn
    from (
        select 
             d.mon$oldest_transaction as tx_oit
            ,cast( rdb$get_context('USER_SESSION','tx_a') as int ) as tx_a
        from mon$database d
    )
    ;
    rollback;

    execute procedure sp_set_tx_ctx('tx_b');
    commit;

    select 
         iif( tx_b < tx_oit, 'For TX < OIT', iif( tx_b = tx_oit, 'For OIT', 'For TX > OIT') ) as msg_b
        ,rdb$get_transaction_cn( tx_b ) as get_tx_b_cn
    from (
        select 
             d.mon$oldest_transaction as tx_oit
            ,cast( rdb$get_context('USER_SESSION','tx_b') as int ) as tx_b
        from mon$database d
    )
    ;

    select
         rdb$get_transaction_cn( d.mon$oldest_transaction ) as get_oit_cn
        ,rdb$get_transaction_cn( current_transaction ) as get_tx_c_cn
        ,rdb$get_transaction_cn( null ) as get_tx_nul_cn
        ,rdb$get_transaction_cn( mon$next_transaction + 1 ) as get_tx_nxx_cn
        -- added 25.09.2018, after commit 
        -- https://github.com/FirebirdSQL/firebird/commit/7610a76ff3f263177d0a9f7b02cdc1784a0f3402
        -- all of these columns must contain NULL:
        ,rdb$get_transaction_cn( mon$next_transaction + (9223372036854775807-mon$next_transaction) ) as get_tx_001_cn
        ,rdb$get_transaction_cn( 9223372036854775807 ) as get_tx_002_cn
        ,rdb$get_transaction_cn(-9223372036854775808) as get_tx_003_cn
    from mon$database d;
    
    set term ^;
    execute block returns( global_cn_sign smallint, snapshot_cn smallint ) as
    begin
       global_cn_sign = sign( rdb$get_context('SYSTEM', 'GLOBAL_CN') );
       snapshot_cn = sign( rdb$get_context('SYSTEM', 'SNAPSHOT_NUMBER') );
       suspend;
    end
    ^
    set term ;^
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    MSG_A                           For TX > OIT
    GET_TX_A_CN                     0

    MSG_B                           For TX < OIT
    GET_TX_B_CN                     1

    GET_OIT_CN                      9
    GET_TX_C_CN                     0

    GET_TX_NUL_CN                   <null>
    GET_TX_NXX_CN                   <null>
    GET_TX_001_CN                   <null>
    GET_TX_002_CN                   <null>
    GET_TX_003_CN                   <null>

    GLOBAL_CN_SIGN                  1
    SNAPSHOT_CN                     1
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

