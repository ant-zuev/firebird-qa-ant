#coding:utf-8
#
# id:           functional.arno.optimizer.opt_inner_join_merge_05
# title:        INNER JOIN join merge and VIEWs
# decription:   X JOIN Y ON (X.Field = Y.Field)
#               When no index can be used on a INNER JOIN and there's a relation setup between X and Y then a MERGE should be performed. Of course also when a VIEW is used.
# tracker_id:   
# min_versions: []
# versions:     3.0
# qmid:         functional.arno.optimizer.opt_inner_join_merge_05

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 3.0
# resources: None

substitutions_1 = []

init_script_1 = """CREATE TABLE Table_10 (
  ID INTEGER NOT NULL
);

CREATE TABLE Table_100 (
  ID INTEGER NOT NULL
);

CREATE TABLE Table_1000 (
  ID INTEGER NOT NULL
);

SET TERM ^^ ;
CREATE PROCEDURE PR_FillTable_10
AS
DECLARE VARIABLE FillID INTEGER;
BEGIN
  FillID = 1;
  WHILE (FillID <= 10) DO
  BEGIN
    INSERT INTO Table_10 (ID) VALUES (:FillID);
    FillID = FillID + 1;
  END
END
^^

CREATE PROCEDURE PR_FillTable_100
AS
DECLARE VARIABLE FillID INTEGER;
BEGIN
  FillID = 1;
  WHILE (FillID <= 100) DO
  BEGIN
    INSERT INTO Table_100 (ID) VALUES (:FillID);
    FillID = FillID + 1;
  END
END
^^

CREATE PROCEDURE PR_FillTable_1000
AS
DECLARE VARIABLE FillID INTEGER;
BEGIN
  FillID = 1;
  WHILE (FillID <= 1000) DO
  BEGIN
    INSERT INTO Table_1000 (ID) VALUES (:FillID);
    FillID = FillID + 1;
  END
END
^^
SET TERM ; ^^

CREATE VIEW View_A (
  ID10,
  ID100
)
AS
SELECT
  t10.ID,
  t100.ID
FROM
  Table_100 t100
  JOIN Table_10 t10 ON (t10.ID = t100.ID);

COMMIT;

EXECUTE PROCEDURE PR_FillTable_10;
EXECUTE PROCEDURE PR_FillTable_100;
EXECUTE PROCEDURE PR_FillTable_1000;

COMMIT;
"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """SET PLAN ON;
SELECT
  Count(*)
FROM
  Table_1000 t1000
  JOIN View_A va ON (va.ID100 = t1000.ID);
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """PLAN HASH (T1000 NATURAL, VA T100 NATURAL, VA T10 NATURAL)

                COUNT
=====================
                   10

"""

@pytest.mark.version('>=3.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_expected_stdout == act_1.clean_stdout
