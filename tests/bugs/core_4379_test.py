#coding:utf-8
#
# id:           bugs.core_4379
# title:        Poor performance of explicit cursors containing correlated subqueries in the select list
# decription:
# tracker_id:   CORE-4379
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """
    recreate sequence g;
    commit;
    recreate table t(id int primary key using index t_pk_idx, f01 int);
    commit;
    delete from t;
    insert into t select gen_id(g,1), gen_id(g,0)*10 from rdb$types,rdb$types
    rows 20000;
    commit;
  """

db_1 = db_factory(from_backup='mon-stat-gathering-3_0.fbk', init=init_script_1)

test_script_1 = """
    set list on;

    execute procedure sp_truncate_stat;
    commit;
    execute procedure sp_gather_stat;
    commit;

    set plan on;
    update t a set f01 = (select f01 from t x where x.id>a.id order by id rows 1);
    set plan off;
    rollback;

    execute procedure sp_gather_stat;
    commit;

    select natural_reads, indexed_reads from v_agg_stat_tabs where table_name = upper('T');

    --------------------------

    execute procedure sp_truncate_stat;
    commit;
    execute procedure sp_gather_stat;
    commit;

    set plan on;
    set term ^;
    execute block as
      declare c_cur cursor for (select (select f01 from t x where x.id>a.id order by id rows 1) as next_f01 from t a);
      declare v_next_f01 int;
    begin
      open c_cur;
      while (1=1) do
      begin
        fetch c_cur into v_next_f01;
        if (row_count = 0) then leave;
        update t set f01 = :v_next_f01 where current of c_cur;
      end
      close c_cur;
    end
    ^
    set term ;^
    set plan off;
    rollback;

    execute procedure sp_gather_stat;
    commit;

    -- On LI-T3.0.0.30981 (29-mar02014) it was 200029999  indexed reads here:
    select natural_reads, indexed_reads from v_agg_stat_tabs where table_name = upper('T');

    -----------------------------

    execute procedure sp_truncate_stat;
    commit;
    execute procedure sp_gather_stat;
    commit;

    set plan on;
    set term ^;
    execute block as
      declare v_key char(8);
      declare c_cur cursor for (select a.rdb$db_key as r_key, (select f01 from t x where x.id>a.id order by id rows 1) as next_f01 from t a);
      declare v_next_f01 int;
    begin
      open c_cur;
      while (1=1) do
      begin
        fetch c_cur into v_key, v_next_f01;
        if (row_count = 0) then leave;
        update t set f01 = :v_next_f01 where rdb$db_key = :v_key;
      end
      close c_cur;
    end
    ^
    set term ;^
    set plan off;
    rollback;

    execute procedure sp_gather_stat;
    commit;

    -- On LI-T3.0.0.30981 (29-mar02014) it was 200049999 indexed reads here:
    select natural_reads, indexed_reads from v_agg_stat_tabs where table_name = upper('T');
  """

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    PLAN (X ORDER T_PK_IDX)
    PLAN (A NATURAL)
    NATURAL_READS                   20000
    INDEXED_READS                   39999

    PLAN (C_CUR X ORDER T_PK_IDX)
    PLAN (C_CUR A NATURAL)
    PLAN (C_CUR X ORDER T_PK_IDX)
    NATURAL_READS                   20000
    INDEXED_READS                   39999

    PLAN (C_CUR X ORDER T_PK_IDX)
    PLAN (C_CUR A NATURAL)
    PLAN (C_CUR X ORDER T_PK_IDX)
    PLAN (T INDEX ())
    NATURAL_READS                   20000
    INDEXED_READS                   59999
  """

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.charset = 'NONE'
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_expected_stdout == act_1.clean_stdout

