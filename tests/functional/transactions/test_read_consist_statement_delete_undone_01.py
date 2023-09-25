#coding:utf-8

"""
ID:          transactions.read-consist-statement-delete-undone-01
TITLE:       READ CONSISTENCY. Changes produced by DELETE statement must be UNDONE when cursor resultset becomes empty after this statement start. Test-01
DESCRIPTION:
  Initial article for reading:
          https://asktom.oracle.com/pls/asktom/f?p=100:11:::::P11_QUESTION_ID:11504247549852
          Note on terms which are used there: "BLOCKER", "LONG" and "FIRSTLAST" - their names are slightly changed here
          to: LOCKER-1, WORKER and LOCKER-2 respectively.
      See also: doc/README.read_consistency.md

      **********************************************

      ::: NB :::
      This test uses script %FBT_REPO%/files/read-consist-sttm-restart-DDL.sql which contains common DDL for all other such tests.
      Particularly, it contains two TRIGGERS (TLOG_WANT and TLOG_DONE) which are used for logging of planned actions and actual
      results against table TEST. These triggers launched AUTONOMOUS transactions in order to have ability to see results in any
      outcome of test.

      ###############
      Following scenario if executed here:
      * five rows are inserted into the table TEST, with IDs: 1...5.

      * session 'locker-1' ("BLOCKER" in Tom Kyte's article ):
              update test set id = id where id=1;

      * session 'worker' ("LONG" in TK article) has mission:
              delete from test where not exists(select * from test where id >= 10) order by id desc;  // using TIL = read committed read consistency

          // Execution will have PLAN ORDER <DESCENDING_INDEX>.
          // It will delete rows starting with ID = 5 and down to ID = 2, but hang on row with ID = 1 because of locker-1;

      * session 'locker-2' ("FIRSTLAST" in TK article):
              (1) insert into test(id) values(6);
              (2) commit;
              (3) update test set id=id where id = 6;

          // session-'worker' remains waiting at this point because row with ID = 5 is still occupied by by locker-1
          // but worker must further see record with (new) id = 6 because its TIL was changed to RC NO RECORD_VERSION.

      * session 'locker-1': commit (and allows lead session-worker to delete row with ID = 1).
              (1) commit;
              (2) insert into test(id) values(7);
              (3) commit;
              (4) update test set id=id where id = 7;

          // This: '(1) commit' - will release record with ID = 1. Worker sees this record and put write-lock on it.
          // [DOC]: "b) engine put write lock on conflicted record"
          // Because of TIL = RC NRV session-'worker' must see all committed records regardless on its own snapshot.
          // Worker resumes search for any rows which with taking in account required order of its DML (i.e. 'ORDER BY ID DESC').
          // [DOC]: "c) engine continue to evaluate remaining records of update/delete cursor and put write locks on it too"
          // Worker starts to search records which must be involved in its DML and *found* first sucn row: it has ID = 7.
          // Then it goes on and stops on ID=6 because id is occupied by locker-2.
          // BECAUSE OF FACT THAT AT LEAST ONE ROW *WAS FOUND* - STATEMENT-LEVEL RESTART *NOT* YET OCCURS HERE.
          // [DOC]: "d) when there is *no more* records to fetch, engine start to undo all actions performed since
          //            top-level statement execution starts and preserve already taken write locks
          //         e) then engine restores transaction isolation mode as READ COMMITTED *READ CONSISTENCY*,
          //            creates new statement-level snapshot and restart execution of top-level statement."


      * session 'locker-2':
              (1) commit;
              (2) insert into test(id) values(8);
              (3) commit;
              (4) update test set id=id where id = 8;

          // This: '(1) commit' - will release record with ID = 6. Worker sees this record and put write-lock on it.
          // [DOC]: "b) engine put write lock on conflicted record"
          // Because of TIL = RC NRV session-'worker' must see all committed records regardless on its own snapshot.
          // Worker resumes search for any rows which with taking in account required order of its DML (i.e. 'ORDER BY ID DESC')
          // [DOC]: "c) engine continue to evaluate remaining records of update/delete cursor and put write locks on it too"
          // Worker starts to search records which must be involved in its DML and *found* first sucn row: it has ID = 8.
          // Then it goes on stops on ID=7 because id is occupied by locker-1.
          // BECAUSE OF FACT THAT AT LEAST ONE ROW *WAS FOUND* - STATEMENT-LEVEL RESTART *NOT* YET OCCURS HERE.
          // [DOC]: "d) when there is *no more* records to fetch, engine start to undo all actions performed since
          //            top-level statement execution starts and preserve already taken write locks
          //         e) then engine restores transaction isolation mode as READ COMMITTED *READ CONSISTENCY*,
          //            creates new statement-level snapshot and restart execution of top-level statement."

      * session 'locker-1': commit (this allows session-worker to delete row with ID = 7).
              (1) commit;
              (2) insert into test(id) values(9);
              (3) commit;
              (4) update test set id=id where id = 9;

         // Comments here are similar to previous one: STATEMENT-LEVEL RESTART *NOT* YET OCCURS HERE.

      * session 'locker-2': commit (this allows session-worker to delete row with ID = 6).
              (1) commit;
              (2) insert into test(id) values(10);
              (3) commit;
              (4) update test set id=id where id = 10;

         // This will made this row visible to session-worker when it will resume its DML.
         // NOTE: this record will cause session-worker immediately UNDO all changes that it was performed before - see "WHERE NOT EXISTS(...)" in its DML expression.


      Expected result:
      * session-'worker' must be cancelled. No rows must be deleted, PLUS new rows must remain (with ID = 6 ... 10).
      * we must NOT see statement-level restart because no rows actually were affected by session-worker statement.
        Column TLOG_DONE.SNAP_NO must contain only one unique value that relates to start of DELETE statement.

      Additional comments for this case - see letter from Vlad, 05-aug-2020 00:51.

FBTEST:      functional.transactions.read_consist_statement_delete_undone_01
NOTES:
    [27.02.2023] pzotov
        Added check for presense of STATEMENT RESTART in the trace (see https://github.com/FirebirdSQL/firebird/issues/6730 )
        Trace must contain several groups, each with similar lines:
            <timestamp> (<trace_memory_address>) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted <N> time(s)

        Checked on 5.0.0.561 (date of build: 29-jun-2022) - all OK.

    [23.09.2023] pzotov
        Replaced verification method of worker attachment presense (which tries DML and waits for resource).
        Many thanks to Vlad for suggestions.
    [25.09.2023] pzotov
        1. Added trace launch and its parsing in order to get number of times when WORKER statement did restart.
        2. To prevent raises between concurrent transactions, it is necessary to ensure that code:
               * does not allow LOCKER-2 to start its work until WORKER session will establish connection and - moreover - will actually locks first record 
                 from the scope that is seen by the query that we want to be executed by worker.
               * does not allow LOCKER-1 to do something after LOCKER-2 issued commit (and thus released record): we first have to ensure that this record
                 now is locked by WORKER. The same when record was occupied by LOCKER-2 and then is released: LOCKER-1 must not do smth until WORKER will
                 encounter this record and 'catch' it.
           This is done by calls to function 'wait_for_record_become_locked()' which are performed by separate 'monitoring' connection with starting Tx
           with NO_WAIT mode and catching exception with further parsing. In case when record has been already occupied (by WORKER) this exception will
           have form "deadlock / -update conflicts ... / -concurrent transaction number is <N>". We can then obtain number of this transaction and query
           mon$statements for get MON$SQL_TEXT that is runnig by this Tx. If it contains contains 'special tag' (see variable SQL_TAG_THAT_WE_WAITING_FOR)
           then we can be sure that WORKER really did establish connection and successfully locked row with required ID.

           Table 'TLOG_WANT' (which is fulfilled by trigger TEST_BIUD using in autonomous tx) can NOT be used for detection of moments when WORKER
           actually locks records which he was waiting for: this trigger fires BEFORE actual updating occurs, i.e. when record become seeon by WORKER
           but is still occupied by some LOCKER ("[DOC]: c) engine continue to evaluate remaining records ... and put write locks on it too")

           NB! Worker transaction must running in WAIT mode - in contrary to Tx that we start in our monitoring loop.

        Checked on WI-T6.0.0.48, WI-T5.0.0.1211, WI-V4.0.4.2988.
"""

import subprocess
import re
from pathlib import Path
import time
import datetime as py_dt
import locale

import pytest
from firebird.qa import *
from firebird.driver import tpb, Isolation, TraAccessMode, DatabaseError

db = db_factory()

fn_worker_sql = temp_file('tmp_worker.sql')
fn_worker_log = temp_file('tmp_worker.log')
fn_worker_err = temp_file('tmp_worker.err')

MAX_WAIT_FOR_WORKER_START_MS = 10000;
SQL_TAG_THAT_WE_WAITING_FOR = 'SQL_TAG_THAT_WE_WAITING_FOR'

#act = python_act('db', substitutions=[('=', ''), ('[ \t]+', ' '), ('.* EXECUTE_STATEMENT_RESTART', 'EXECUTE_STATEMENT_RESTART')])
act = python_act('db', substitutions=[ ('.* EXECUTE_STATEMENT_RESTART', 'EXECUTE_STATEMENT_RESTART')])


#-----------------------------------------------------------------------------------------------------------------------------------------------------

def wait_for_record_become_locked(tx_monitoring, cur_monitoring, sql_to_lock_record, SQL_TAG_THAT_WE_WAITING_FOR):

    # sql_to_lock_record: f'update {target_obj} set id=id where id=1'
    # ::: NB :::
    # tx_monitoring must work in NOWAIT mode!

    t1=py_dt.datetime.now()
    required_concurrent_found = None
    concurrent_tx_pattern = re.compile('concurrent transaction number is \\d+', re.IGNORECASE)
    while True:
        concurrent_tx_number = None
        concurrent_runsql = ''
        tx_monitoring.begin()
        try:
            cur_monitoring.execute(sql_to_lock_record)
        except DatabaseError as exc:
            # Failed: SQL execution failed with: deadlock
            # -update conflicts with concurrent update
            # -concurrent transaction number is 40
            m = concurrent_tx_pattern.search( str(exc) )
            if m:
                concurrent_tx_number = m.group().split()[-1] # 'concurrent transaction number is 40' ==> '40'
                cur_monitoring.execute( 'select mon$sql_text from mon$statements where mon$transaction_id = ?', (int(concurrent_tx_number),) )
                for r in cur_monitoring:
                    concurrent_runsql = r[0]
                    if SQL_TAG_THAT_WE_WAITING_FOR in concurrent_runsql:
                        required_concurrent_found = 1

            # pytest.fail(f"Can not upd, concurrent TX = {concurrent_tx_number}, sql: {concurrent_runsql}")
        finally:
            tx_monitoring.rollback()
        
        if not required_concurrent_found:
            t2=py_dt.datetime.now()
            d1=t2-t1
            if d1.seconds*1000 + d1.microseconds//1000 >= MAX_WAIT_FOR_WORKER_START_MS:
                break
            else:
                time.sleep(0.2)
        else:
            break

    assert required_concurrent_found, f"Could not find attach that running SQL with tag '{SQL_TAG_THAT_WE_WAITING_FOR}' and locks record for {MAX_WAIT_FOR_WORKER_START_MS} ms. ABEND."
    return

#-----------------------------------------------------------------------------------------------------------------------------------------------------

@pytest.mark.version('>=4.0')
def test_1(act: Action, fn_worker_sql: Path, fn_worker_log: Path, fn_worker_err: Path, capsys):
    sql_init = (act.files_dir / 'read-consist-sttm-restart-DDL.sql').read_text()

    for checked_mode in('table', 'view'):
        target_obj = 'test' if checked_mode == 'table' else 'v_test'

        SQL_TO_BE_RESTARTED = f'delete /* {SQL_TAG_THAT_WE_WAITING_FOR} */ from {target_obj} where not exists(select * from {target_obj} where id >= 10) order by id desc'

        # add rows with ID = 1,2,3,4,5:
        sql_addi='''
            set term ^;
            execute block as
            begin
                rdb$set_context('USER_SESSION', 'WHO', 'INIT_DATA');
            end
            ^
            set term ;^
            insert into test(id, x)
            select row_number()over(),row_number()over()
            from rdb$types rows 5;
            commit;
        '''
        act.isql(switches=['-q'], input = ''.join( (sql_init, sql_addi) ) )
        # ::: NOTE ::: We have to immediately quit if any error raised in prepare phase.
        # See also letter from dimitr, 01-feb-2022 14:46
        assert act.stderr == ''
        act.reset()

        trace_cfg_items = [
            'time_threshold = 0',
            'log_errors = true',
            'log_statement_start = true',
            'log_statement_finish = true',
        ]

        with act.trace(db_events = trace_cfg_items, encoding=locale.getpreferredencoding()):

            with act.db.connect() as con_lock_1, act.db.connect() as con_lock_2, act.db.connect() as con_monitoring:
            
                tpb_monitoring = tpb(isolation=Isolation.READ_COMMITTED_RECORD_VERSION, lock_timeout=0)
                tx_monitoring = con_monitoring.transaction_manager(tpb_monitoring)
                cur_monitoring = tx_monitoring.cursor()

                for i,c in enumerate((con_lock_1,con_lock_2)):
                    sttm = f"execute block as begin rdb$set_context('USER_SESSION', 'WHO', 'LOCKER #{i+1}'); end"
                    c.execute_immediate(sttm)

                #########################
                ###  L O C K E R - 1  ###
                #########################
                con_lock_1.execute_immediate( 'update test set id=id where id = 1' )

                worker_sql = f'''
                    set list on;
                    set autoddl off;
                    set term ^;
                    execute block returns (whoami varchar(30)) as
                    begin
                        whoami = 'WORKER'; -- , ATT#' || current_connection;
                        rdb$set_context('USER_SESSION','WHO', whoami);
                        -- suspend;
                    end
                    ^
                    set term ;^
                    commit;
                    SET KEEP_TRAN_PARAMS ON;
                    set transaction read committed read consistency;
                    set list off;
                    set wng off;
                    set count on;

                    -- this must hang because of locker-1:
                    {SQL_TO_BE_RESTARTED};

                    -- check results:
                    -- ###############
                    select id from test order by id; -- this will produce output only after all lockers do their commit/rollback

                    select v.old_id, v.op, v.snap_no_rank
                    from v_worker_log v
                    where v.op = 'del';

                    set width who 10;
                    -- DO NOT check this! Values can differ here from one run to another!
                    --select id, trn, who, old_id, new_id, op, rec_vers, global_cn, snap_no from tlog_done order by id;

                    rollback;
                '''
                fn_worker_sql.write_text(worker_sql)

                with fn_worker_log.open(mode='w') as hang_out, fn_worker_err.open(mode='w') as hang_err:

                    ############################################################################
                    ###  L A U N C H     W O R K E R    U S I N G     I S Q L,   A S Y N C.  ###
                    ############################################################################
                    p_worker = subprocess.Popen([act.vars['isql'], '-i', str(fn_worker_sql),
                                                   '-user', act.db.user,
                                                   '-password', act.db.password,
                                                   act.db.dsn
                                                ],
                                                  stdout = hang_out,
                                                  stderr = hang_err
                                               )

                    # NB: when ISQL will establish attach, first record that it must lock is ID = 5 -- see above SQL_TO_BE_RESTARTED
                    # We must to ensure that this (worker) attachment has been really created and LOCKS this record:
                    #
                    wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id=5', SQL_TAG_THAT_WE_WAITING_FOR)


                    #########################
                    ###  L O C K E R - 2  ###
                    #########################
                    # Add record so that it **will* be included in the set of rows that must be affected by session-worker:
                    con_lock_2.execute_immediate( 'insert into test(id, x) values(6, 6);' )
                    con_lock_2.commit()
                    con_lock_2.execute_immediate( 'update test set id = id where id = 6;' )

                    #########################
                    ###  L O C K E R - 1  ###
                    #########################
                    con_lock_1.commit() # releases record with ID=1 ==> now it can be locked by worker.

                    # We have to WAIT HERE until worker will actually 'catch' just released record with ID = 1.
                    #
                    wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id=1', SQL_TAG_THAT_WE_WAITING_FOR)

                    # If we come here then it means that record with ID = 1 for sure is locked by WORKER.

                    # Add record so that it **will* be included in the set of rows that must be affected by session-worker:
                    con_lock_1.execute_immediate( 'insert into test(id, x) values(7, 7);' )
                    con_lock_1.commit()
                    con_lock_1.execute_immediate( 'update test set id = id where id = 7;' )

                    #########################
                    ###  L O C K E R - 2  ###
                    #########################
                    con_lock_2.commit() # releases record with ID = 6, but session-worker is waiting for record with ID = 7 (that was added by locker-1).

                    # We have to WAIT HERE until worker will actually 'catch' just released record with ID = 6:
                    #
                    wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id = 6', SQL_TAG_THAT_WE_WAITING_FOR)

                    # If we come here then it means that record with ID = 6 for sure is locked by WORKER.


                    con_lock_2.execute_immediate( 'insert into test(id, x) values(8, 8);' )
                    con_lock_2.commit()
                    con_lock_2.execute_immediate( 'update test set id = id where id = 8;' )


                    #########################
                    ###  L O C K E R - 1  ###
                    #########################
                    con_lock_1.commit() # releases record with ID = 7, but session-worker is waiting for record with ID = 8 (that was added by locker-2).

                    # We have to WAIT HERE until worker will actually 'catch' just released record with ID = 7:
                    #
                    wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id = 7', SQL_TAG_THAT_WE_WAITING_FOR)

                    # If we come here then it means that record with ID = 7 for sure is locked by WORKER.

                    con_lock_1.execute_immediate( 'insert into test(id, x) values(9, 9);' )
                    con_lock_1.commit()
                    con_lock_1.execute_immediate( 'update test set id = id where id = 9;' )


                    #########################
                    ###  L O C K E R - 2  ###
                    #########################
                    con_lock_2.commit() # releases record with ID = 8, but session-worker is waiting for record with ID = 9 (that was added by locker-1).

                    # We have to WAIT HERE until worker will actually 'catch' just released record with ID = 8:
                    #
                    wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id = 8', SQL_TAG_THAT_WE_WAITING_FOR)

                    # If we come here then it means that record with ID = 8 for sure is locked by WORKER.

                    con_lock_2.execute_immediate( 'insert into test(id, x) values(10, 10);' )
                    con_lock_2.commit()
                    con_lock_2.execute_immediate( 'update test set id = id where id = 10;' )


                    #########################
                    ###  L O C K E R - 1  ###
                    #########################
                    con_lock_1.commit() # <<< THIS MUST CANCEL ALL PERFORMED DELETIONS OF SESSION-WORKER: record with ID = 10 become visible to it and its "NOT EXISTS()" query predicate return FAILSE on that.

                    # We have to WAIT HERE until worker will actually 'catch' just released record with ID = 9:
                    #
                    #wait_for_record_become_locked(tx_monitoring, cur_monitoring, f'update {target_obj} set id=id where id = 9', SQL_TAG_THAT_WE_WAITING_FOR)
                    # If we come here then it means that record with ID = 9 for sure is locked by WORKER.

                    con_lock_2.commit()

                    # Here we wait until ISQL complete its mission:
                    p_worker.wait()

            #< with act.db.connect()

            for g in (fn_worker_log, fn_worker_err):
                with g.open() as f:
                    for line in f:
                        if line.split():
                            if g == fn_worker_log:
                                print(f'checked_mode: {checked_mode}, STDLOG: {line}')
                            else:
                                print(f'UNEXPECTED STDERR {line}')


            #for g in (fn_worker_log, fn_worker_err):
            #    with g.open() as f:
            #        print( f.read() )

            expected_stdout_worker = f"""
                checked_mode: {checked_mode}, STDLOG: Records affected: 0

                checked_mode: {checked_mode}, STDLOG:      ID
                checked_mode: {checked_mode}, STDLOG: =======
                checked_mode: {checked_mode}, STDLOG:       1
                checked_mode: {checked_mode}, STDLOG:       2
                checked_mode: {checked_mode}, STDLOG:       3
                checked_mode: {checked_mode}, STDLOG:       4
                checked_mode: {checked_mode}, STDLOG:       5
                checked_mode: {checked_mode}, STDLOG:       6
                checked_mode: {checked_mode}, STDLOG:       7
                checked_mode: {checked_mode}, STDLOG:       8
                checked_mode: {checked_mode}, STDLOG:       9
                checked_mode: {checked_mode}, STDLOG:      10
                checked_mode: {checked_mode}, STDLOG: Records affected: 10

                checked_mode: {checked_mode}, STDLOG:  OLD_ID OP              SNAP_NO_RANK
                checked_mode: {checked_mode}, STDLOG: ======= ====== =====================
                checked_mode: {checked_mode}, STDLOG:       5 DEL                        1
                checked_mode: {checked_mode}, STDLOG:       4 DEL                        1
                checked_mode: {checked_mode}, STDLOG:       3 DEL                        1
                checked_mode: {checked_mode}, STDLOG:       2 DEL                        1

                checked_mode: {checked_mode}, STDLOG: Records affected: 4
            """
            act.expected_stdout = expected_stdout_worker
            act.stdout = capsys.readouterr().out
            assert act.clean_stdout == act.clean_expected_stdout
            act.reset()

        #< act.trace()

        allowed_patterns = \
        (
             '\\)\\s+EXECUTE_STATEMENT_RESTART$'
            ,re.escape(SQL_TO_BE_RESTARTED)
            ,'^Restarted \\d+ time\\(s\\)'
        )
        allowed_patterns = [ re.compile(p, re.IGNORECASE) for p in allowed_patterns ]

        for line in act.trace_log:
            if line.strip():
                if act.match_any(line.strip(), allowed_patterns):
                    print(line.strip())

        expected_stdout_trace = f"""
            {SQL_TO_BE_RESTARTED}

            2023-02-27T18:03:19.1100 (26564:0000000005A01940) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted 1 time(s)

            2023-02-27T18:03:19.1100 (26564:0000000005A01940) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted 2 time(s)

            2023-02-27T18:03:19.1100 (26564:0000000005A01940) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted 3 time(s)

            2023-02-27T18:03:19.1100 (26564:0000000005A01940) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted 4 time(s)

            2023-02-27T18:03:19.1100 (26564:0000000005A01940) EXECUTE_STATEMENT_RESTART
            {SQL_TO_BE_RESTARTED}
            Restarted 5 time(s)

            {SQL_TO_BE_RESTARTED}

        """

        act.expected_stdout = expected_stdout_trace
        act.stdout = capsys.readouterr().out
        assert act.clean_stdout == act.clean_expected_stdout

    # < for checked_mode in('table', 'view')
