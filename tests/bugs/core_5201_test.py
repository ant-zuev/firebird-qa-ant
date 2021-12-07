#coding:utf-8
#
# id:           bugs.core_5201
# title:        Return nonzero result code when restore fails on activating and creating deferred user index
# decription:
#                   ### NB ###
#                   According to Alex responce on letter 25-apr-2016 19:15, zero retcode returned ONLY when restore
#                   was done WITH '-verbose' switch, and this was fixed. When restoring wasdone without additional
#                   switches, retcode was NON zero and its value was 1.
#
#                   Test description.
#                   We create table with UNIQUE computed-by index which expression refers to other table (Firebird allows this!).
#                   Because other table (test_2) initially is empty, index _can_ be created. But after this we insert record into
#                   this table and do commit. Since that moment backup of this database will have table test_1 but its index will
#                   NOT be able to restore (unless '-i' switch specified).
#                   We will use this inability of restore index by checking 'gbak -rep -v ...' return code: it should be NON zero.
#                   If code will skip exception then this will mean FAIL of test.
#
#                   Confirmed on: 3.0.0.32484, 4.0.0.142 - retcode was ZERO (and this was wrong); since 4.0.0.145 - all fine, retcode=2.
#
# tracker_id:   CORE-5201
# min_versions: ['2.5.6']
# versions:     2.5.6
# qmid:         None

import pytest
from pathlib import Path
from firebird.qa import db_factory, python_act, Action, temp_file

# version: 2.5.6
# resources: None

substitutions_1 = []

init_script_1 = """
    create table test_1(x int);
    create table test_2(x int);
    insert into test_1 values(1);
    insert into test_1 values(2);
    insert into test_1 values(3);
    commit;
    create unique index test_1_unq on test_1 computed by( iif( exists(select * from test_2), 1, x ) );
    commit;
    insert into test_2 values(1000);
    commit;
"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# import os
#  import time
#  import subprocess
#
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#
#  thisdb = db_conn.database_name
#  tmpbkp = os.path.splitext(thisdb)[0] + '.fbk'
#  tmpres = os.path.splitext(thisdb)[0] + '.tmp'
#
#  db_conn.close()
#
#  #--------------------------------------------
#
#  def flush_and_close(file_handle):
#      # https://docs.python.org/2/library/os.html#os.fsync
#      # If you're starting with a Python file object f,
#      # first do f.flush(), and
#      # then do os.fsync(f.fileno()), to ensure that all internal buffers associated with f are written to disk.
#      global os
#
#      file_handle.flush()
#      if file_handle.mode not in ('r', 'rb') and file_handle.name != os.devnull:
#          # otherwise: "OSError: [Errno 9] Bad file descriptor"!
#          os.fsync(file_handle.fileno())
#      file_handle.close()
#
#  #--------------------------------------------
#
#  def cleanup( f_names_list ):
#      global os
#      for i in range(len( f_names_list )):
#         if type(f_names_list[i]) == file:
#            del_name = f_names_list[i].name
#         elif type(f_names_list[i]) == str:
#            del_name = f_names_list[i]
#         else:
#            print('Unrecognized type of element:', f_names_list[i], ' - can not be treated as file.')
#            del_name = None
#
#         if del_name and os.path.isfile( del_name ):
#             os.remove( del_name )
#
#  #--------------------------------------------
#
#  f_backup=open( os.path.join(context['temp_directory'],'tmp_backup_5201.log'), 'w')
#  subprocess.check_call([context['fbsvcmgr_path'],
#                         "localhost:service_mgr",
#                         "action_backup",
#                         "dbname", thisdb,
#                         "bkp_file", tmpbkp
#                        ],
#                        stdout=f_backup, stderr=subprocess.STDOUT)
#  flush_and_close( f_backup )
#
#  f_restore=open( os.path.join(context['temp_directory'],'tmp_restore_5201.log'), 'w')
#  try:
#      # This is key point: before 4.0.0.145 restoring with '-v' key did assign retcode to zero
#      # even in case when index could not be created because of errors.
#      # Since 4.0.0.145 this call should assign retcode = 2:
#      restore_out=subprocess.check_call([ context['gbak_path'],
#                         "-rep",
#                         "-v",
#                         tmpbkp,
#                         tmpres
#                        ],
#                        stdout=f_restore, stderr=subprocess.STDOUT)
#
#  except subprocess.CalledProcessError as cpexc:
#      # Final output of this test MUST have following line (confirmed on 3.0.0.32484: did not has this).
#      print ('Restore finished with error code: '+str(cpexc.returncode))
#
#  flush_and_close( f_restore )
#
#
#  # Output STDOUT+STDERR of backup: they both should be EMPTY because we did not specify '-v' key:
#  with open( f_backup.name,'r') as f:
#      for line in f:
#          print( "BACKUP LOG: "+line )
#
#  # Output STDOUT+STDERR of restoring with filtering text related to ERRORs:
#  with open( f_restore.name,'r') as f:
#      for line in f:
#          if ' ERROR:' in line:
#              print( "RESTORE LOG: "+line )
#
#
#  # Cleanup:
#  ##########
#  time.sleep(1)
#  cleanup( (f_backup, f_restore, tmpbkp, tmpres) )
#
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    gbak: ERROR:attempt to store duplicate value (visible to active transactions) in unique index "TEST_1_UNQ"
    gbak: ERROR:    Problematic key value is (<expression> = 1)
"""

fbk_file = temp_file('core_5201.fbk')
tmp_db_file = temp_file('tmp_core_5201.fdb')

@pytest.mark.version('>=3.0')
def test_1(act_1: Action, fbk_file: Path, tmp_db_file: Path):
    with act_1.connect_server() as srv:
        srv.database.backup(database=act_1.db.db_path, backup=fbk_file)
        assert srv.readlines() == []
    #
    act_1.expected_stderr = 'We expect error'
    act_1.expected_stdout = expected_stdout_1
    act_1.gbak(switches=['-rep', '-v', str(fbk_file), str(tmp_db_file)])
    # filter stdout
    act_1.stdout = '\n'.join([line for line in act_1.stdout.splitlines() if ' ERROR:' in line])
    assert act_1.return_code == 2
    assert act_1.clean_stdout == act_1.clean_expected_stdout
