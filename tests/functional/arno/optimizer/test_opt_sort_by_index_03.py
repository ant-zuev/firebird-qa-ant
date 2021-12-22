#coding:utf-8
#
# id:           functional.arno.optimizer.opt_sort_by_index_03
# title:        ORDER BY ASC using index (non-unique)
# decription:   ORDER BY X
#               When a index can be used for sorting, use it.
# tracker_id:   
# min_versions: []
# versions:     2.0
# qmid:         functional.arno.optimizer.opt_sort_by_index_03

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.0
# resources: None

substitutions_1 = []

init_script_1 = """CREATE TABLE Table_66 (
  ID INTEGER
);

SET TERM ^^ ;
CREATE PROCEDURE PR_FillTable_66
AS
DECLARE VARIABLE FillID INTEGER;
BEGIN
  FillID = 2147483647;
  WHILE (FillID > 0) DO
  BEGIN
    INSERT INTO Table_66 (ID) VALUES (:FillID);
    FillID = FillID / 2;
  END
  INSERT INTO Table_66 (ID) VALUES (NULL);
  INSERT INTO Table_66 (ID) VALUES (0);
  INSERT INTO Table_66 (ID) VALUES (NULL);
  FillID = -2147483648;
  WHILE (FillID < 0) DO
  BEGIN
    INSERT INTO Table_66 (ID) VALUES (:FillID);
    FillID = FillID / 2;
  END
END
^^
SET TERM ; ^^

COMMIT;

EXECUTE PROCEDURE PR_FillTable_66;

COMMIT;

CREATE ASC INDEX I_Table_66_ASC ON Table_66 (ID);
CREATE DESC INDEX I_Table_66_DESC ON Table_66 (ID);

COMMIT;
"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """SET PLAN ON;
SELECT
  ID
FROM
  Table_66 t66
ORDER BY
t66.ID ASC;"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """PLAN (T66 ORDER I_TABLE_66_ASC)

          ID
============
      <null>
      <null>
 -2147483648
 -1073741824
  -536870912
  -268435456
  -134217728
   -67108864
   -33554432
   -16777216
    -8388608
    -4194304
    -2097152
    -1048576
     -524288
     -262144
     -131072
      -65536
      -32768
      -16384

          ID
============
       -8192
       -4096
       -2048
       -1024
        -512
        -256
        -128
         -64
         -32
         -16
          -8
          -4
          -2
          -1
           0
           1
           3
           7
          15
          31

          ID
============
          63
         127
         255
         511
        1023
        2047
        4095
        8191
       16383
       32767
       65535
      131071
      262143
      524287
     1048575
     2097151
     4194303
     8388607
    16777215
    33554431

          ID
============
    67108863
   134217727
   268435455
   536870911
  1073741823
2147483647"""

@pytest.mark.version('>=2.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

