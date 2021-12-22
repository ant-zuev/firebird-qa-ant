#coding:utf-8
#
# id:           functional.fkey.unique.insert_03
# title:        Check correct work fix with foreign key
# decription:   Check foreign key work.
#               Master table has one primary key field and one unique field.
#               Master transaction:
#                1) modified non key field
#                2) create savepoint
#                3) modified unique field
#                4) rollback to savepoint
#               Detail transaction inserts record  in detail_table.
#               Expected: Error - unique field was changed
# tracker_id:
# min_versions: []
# versions:     2.1
# qmid:         functional.fkey.unique.ins_03

import pytest
from firebird.qa import db_factory, python_act, Action
from firebird.driver import DatabaseError, tpb, Isolation

# version: 2.1
# resources: None

substitutions_1 = []

init_script_1 = """CREATE TABLE MASTER_TABLE (
    ID     INTEGER PRIMARY KEY,
    UF     INTEGER UNIQUE,
    INT_F  INTEGER
);

CREATE TABLE DETAIL_TABLE (
    ID    INTEGER PRIMARY KEY,
    FKEY  INTEGER
);

ALTER TABLE DETAIL_TABLE ADD CONSTRAINT FK_DETAIL_TABLE FOREIGN KEY (FKEY) REFERENCES MASTER_TABLE (UF);
COMMIT;
INSERT INTO MASTER_TABLE (ID, UF, INT_F) VALUES (1, 1, 10);
commit;"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# TPB_master = (
#        chr(kdb.isc_tpb_write)
#      + chr(kdb.isc_tpb_read_committed) + chr(kdb.isc_tpb_rec_version)
#      + chr(kdb.isc_tpb_nowait)
#                    )
#  TPB_detail = (
#        chr(kdb.isc_tpb_write)
#      + chr(kdb.isc_tpb_read_committed) + chr(kdb.isc_tpb_rec_version)
#      + chr(kdb.isc_tpb_nowait)
#                    )
#
#
#  db_conn.begin(tpb=TPB_master)
#  cm_1 = db_conn.cursor()
#  cm_1.execute('UPDATE MASTER_TABLE SET INT_F=2')
#  db_conn.savepoint('A')
#  cm_1.execute('UPDATE MASTER_TABLE SET UF=2 WHERE ID=1')
#  db_conn.rollback(savepoint='A')
#
#  #Create second connection - update detail table
#  con_detail = kdb.connect(
#       dsn=dsn.encode(),
#       user=user_name.encode(),
#       password=user_password.encode()
#  )
#
#  try:
#     con_detail.begin(tpb=TPB_detail)
#     cd = con_detail.cursor()
#     cd.execute("INSERT INTO DETAIL_TABLE (ID, FKEY) VALUES (1,2)")
#     con_detail.commit()
#  except Exception, e:
#  print (e[0])
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

@pytest.mark.version('>=2.1')
def test_1(act_1: Action):
    with act_1.db.connect() as con:
        cust_tpb = tpb(isolation=Isolation.READ_COMMITTED_RECORD_VERSION, lock_timeout=0)
        con.begin(cust_tpb)
        with con.cursor() as c:
            c.execute('UPDATE MASTER_TABLE SET INT_F=2')
            con.savepoint('A')
            c.execute('UPDATE MASTER_TABLE SET UF=2 WHERE ID=1')
            con.rollback(savepoint='A')
            #Create second connection for change detail table
            with act_1.db.connect() as con_detail:
                con_detail.begin(cust_tpb)
                with con_detail.cursor() as cd:
                    with pytest.raises(DatabaseError,
                                       match='.*Foreign key reference target does not exist.*'):
                        cd.execute("INSERT INTO DETAIL_TABLE (ID, FKEY) VALUES (1,2)")
                con_detail.commit()
    # Passed.
