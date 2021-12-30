#coding:utf-8
#
# id:           functional.replication.updating_blob_with_empty_string_stops_replication
# title:        Replication gets stuck due to "Blob xxx.xx is not found for table xxx" error
# decription:   
#                   https://github.com/FirebirdSQL/firebird/issues/6795
#               
#                   Test creates table with blob column and performs trivial scenario:
#                       insert into test(id, b) values(1, null);
#                       update test set b = '' where id = 1;
#                   After this we do connect and query ID of last generated segment by querying REPLICATION_SEQUENCE variable
#                   from SYSTEM context namespace.
#                   
#                   Then we wait until replica becomes actual to master, and this delay will last no more then threshold
#                   that is defined by MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG variable (measured in seconds).
#                   During this delay, we check every second for replication log and search there line with number of last generated
#                   segment (which was replicated and deleting finally).
#                   We can assume that replication finished OK only when such line is found see ('POINT-1').
#                   
#                   Then we invoke ISQL with executing auxiliary script for drop all DB objects on master (with '-nod' command switch).
#                   After all objects will be dropped, we have to wait again until  replica becomes actual with master (see 'POINT-2').
#               
#                   Finally, we extract metadata for master and replica and compare them (see 'f_meta_diff').
#                   The only difference in metadata must be 'CREATE DATABASE' statement with different DB names - we suppress it,
#                   thus metadata difference must not be issued.
#               
#                   ################
#                   ### N O T E  ###
#                   ################
#                   Test assumes that master and replica DB have been created beforehand.
#                   Also, it assumes that %FB_HOME%
#               eplication.conf has been prepared with apropriate parameters for replication.
#                   Particularly, name of directories and databases must have info about checked FB major version and ServerMode.
#                       * verbose = true // in order to find out line with message that required segment was replicated
#                       * section for master database with specified parameters:
#                           journal_directory = "!fbt_repo!	mp
#               b-replication.!fb_major!.!server_mode!.journal"
#                           journal_archive_directory = "!fbt_repo!	mp
#               b-replication.!fb_major!.!server_mode!.archive"
#                           journal_archive_command = "copy $(pathname) $(archivepathname)"
#                           journal_archive_timeout = 10
#                       * section for replica database with specified parameter:
#                            journal_source_directory =  "!fbt_repo!	mp
#               b-replication.!fb_major!.!server_mode!.archive"
#               
#                   Master and replica databases must be created in "%FBT_REPO%	mp" directory and have names like these:
#                       'fbt-main.fb40.SS.fdb'; 'fbt-repl.fb40.SS.fdb'; - for FB 4.x ('SS' = Super; 'CS' = Classic)
#                       'fbt-main.fb50.SS.fdb'; 'fbt-repl.fb50.SS.fdb'; - for FB 5.x ('SS' = Super; 'CS' = Classic)
#                       NB: fixed numeric value ('40' or '50') must be used for any minor FB version (4.0; 4.0.1; 4.1; 5.0; 5.1 etc)
#               
#                   These two databases must NOT be dropped in any of tests related to replication!
#                   They are created and dropped in the batch scenario which prepares FB instance to be checked for each ServerMode
#                   and make cleanup after it, i.e. when all tests will be completed.
#               
#                   NB. Currently this task presents only in Windows batch, thus test has attribute platform = 'Windows'.
#               
#                   Temporary comment. For debug purpoces:
#                       1) find out SUFFIX of the name of FB service which is to be tested (e.g. 'DefaultInstance', '40SS' etc);
#                       2) copy file %fbt-repo%	ests
#               unctional	abloidatches\\setup-fb-for-replication.bat.txt
#                          to some place and rename it "*.bat";
#                       3) open this .bat in editor and asjust value of 'fbt_repo' variable;
#                       4) run: setup-fb-for-replication.bat [SUFFIX_OF_FB_SERVICE]
#                          where SUFFIX_OF_FB_SERVICE is ending part of FB service which you want to check:
#                          DefaultInstance ; 40ss ; 40cs ; 50ss ; 50cs etc
#                       5) batch 'setup-fb-for-replication.bat' will:
#                          * stop selected FB instance
#                          * create test databases (in !fbt_repo!	mp\\);
#                          * prepare journal/archive sub-folders for replication (also in !fbt_repo!	mp\\);
#                          * replace %fb_home%
#               eplication.conf with apropriate
#                          * start selected FB instance
#                       6) run this test (FB instance will be already launched by setup-fb-for-replication.bat):
#                           %fpt_repo%
#               bt-run2.bat dblevel-triggers-must-not-fire-on-replica.fbt 50ss, etc
#               
#                   Confirmed bug on 4.0.0.2465, got in replication.log:
#                       * Added 1 segment(s) to the processing queue 
#                       * Segment 1 replication failure at offset 150 
#                       * Blob 128.480 is not found for table TEST
#                       After this replication of segment 1 unable to continue and issues repeating messages about added segments.
#               
#                   Checked on:
#                       4.0.0.2479 SS; 4.0.1.2519 CS; 5.0.0.82 SS/CS.
#                
# tracker_id:   
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, python_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('Start removing objects in:.*', 'Start removing objects'), ('Finish. Total objects removed:  [1-9]\\d*', 'Finish. Total objects removed'), ('.* CREATE DATABASE .*', '')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# 
#  import os
#  import subprocess
#  import re
#  import difflib
#  import shutil
#  import time
#  
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#  
#  #####################################
#  MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 65
#  #####################################
#  
#  svc = fdb.services.connect(host='localhost', user=user_name, password=user_password)
#  FB_HOME = svc.get_home_directory()
#  svc.close()
#  
#  engine = db_conn.engine_version         # 4.0; 4.1; 5.0 etc -- type float
#  fb_major = 'fb' + str(engine)[:1] + '0' # 'fb40'; 'fb50'
#  
#  cur = db_conn.cursor()
#  cur.execute("select rdb$config_value from rdb$config where upper(rdb$config_name) = upper('ServerMode')")
#  server_mode = 'XX'
#  for r in cur:
#      if r[0] == 'Super':
#          server_mode = 'SS'
#      elif r[0] == 'SuperClassic':
#          server_mode = 'SC'
#      elif r[0] == 'Classic':
#          server_mode = 'CS'
#  cur.close()
#  
#  # 'fbt-main.fb50.ss.fdb' etc:
#  db_main = os.path.join( context['temp_directory'], 'fbt-main.' + fb_major + '.' + server_mode + '.fdb' )
#  db_repl = db_main.replace( 'fbt-main.', 'fbt-repl.')
#  
#  # Folders for journalling and archieving segments.
#  repl_journal_dir = os.path.join( context['temp_directory'], 'fb-replication.' + fb_major + '.' + server_mode + '.journal' )
#  repl_archive_dir = os.path.join( context['temp_directory'], 'fb-replication.' + fb_major + '.' + server_mode +  '.archive' )
#  
#  db_conn.close()
#  
#  #--------------------------------------------
#  
#  def flush_and_close( file_handle ):
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
#  def wait_for_data_in_replica( fb_home, max_allowed_time_for_wait, db_main, prefix_msg = '' ):
#  
#      global re
#      global difflib
#      global time
#  
#      replold_lines = []
#      with open( os.path.join(fb_home,'replication.log'), 'r') as f:
#          replold_lines = f.readlines()
#  
#      con = fdb.connect( dsn = 'localhost:' + db_main, no_db_triggers = 1)
#      cur = con.cursor()
#      cur.execute("select rdb$get_context('SYSTEM','REPLICATION_SEQUENCE') from rdb$database")
#      for r in cur:
#          last_generated_repl_segment = r[0]
#      cur.close()
#      con.close()
#  
#      #print('last_generated_repl_segment:', last_generated_repl_segment)
#  
#      # VERBOSE: Segment 1 (2582 bytes) is replicated in 1 second(s), deleting the file
#      p=re.compile( '\\+\\s+verbose:\\s+segment\\s+%(last_generated_repl_segment)s\\s+\\(\\d+\\s+bytes\\)\\s+is\\s+replicated.*deleting' % locals(), re.IGNORECASE)
#  
#      found_required_message = False
#      for i in range(0,max_allowed_time_for_wait):
#          time.sleep(1)
#       
#          # Get content of fb_home replication.log _after_ isql finish:
#          f_repllog_new = open( os.path.join(fb_home,'replication.log'), 'r')
#          diff_data = difflib.unified_diff(
#              replold_lines, 
#              f_repllog_new.readlines()
#            )
#          f_repllog_new.close()
#  
#          for k,d in enumerate(diff_data):
#              if p.search(d):
#                  print( (prefix_msg + ' ' if prefix_msg else '') + 'FOUND message about replicated segment.' )
#                  found_required_message = True
#                  break
#  
#          if found_required_message:
#              break
#  
#      if not found_required_message:
#          print('UNEXPECTED RESULT: no message about replicated segment for %d seconds.' % max_allowed_time_for_wait)
#  
#  #--------------------------------------------
#  
#  sql_ddl = '''    set bail on;
#      set list on;
#  
#      recreate table test(id int primary key, b blob);
#      insert into test(id, b) values(1, null);
#      update test set b = '' where id = 1;
#      commit;
#      
#      select rdb$get_context('SYSTEM','REPLICATION_SEQUENCE') as last_generated_repl_segment from rdb$database;
#      quit;
#  ''' % locals()
#  
#  
#  f_sql_chk = open( os.path.join(context['temp_directory'],'tmp_gh_6795_test.sql'), 'w')
#  f_sql_chk.write(sql_ddl)
#  flush_and_close( f_sql_chk )
#  
#  f_sql_log = open( ''.join( (os.path.splitext(f_sql_chk.name)[0], '.log' ) ), 'w')
#  f_sql_err = open( ''.join( (os.path.splitext(f_sql_chk.name)[0], '.err' ) ), 'w')
#  subprocess.call( [ context['isql_path'], 'localhost:' + db_main, '-i', f_sql_chk.name ], stdout = f_sql_log, stderr = f_sql_err)
#  flush_and_close( f_sql_log )
#  flush_and_close( f_sql_err )
#  
#  last_generated_repl_segment = 0
#  
#  with open(f_sql_err.name,'r') as f:
#      for line in f:
#          print('UNEXPECTED STDERR in initial SQL: ' + line)
#          MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 0
#  
#  if MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG: # ==> initial SQL script finished w/o errors
#  
#      ##############################################################################
#      ###  W A I T   U N T I L    R E P L I C A    B E C O M E S   A C T U A L   ###
#      ##############################################################################
#      wait_for_data_in_replica( FB_HOME, MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG, db_main, 'POINT-1' )
#      
#      runProgram('isql', ['localhost:' + db_repl, '-nod'], "set list on; select count(*) as empty_string_blob_on_replica from test where b = '' and id = 1;")
#  
#      # return initial state of master DB:
#      # remove all DB objects (tables, views, ...):
#      # --------------------------------------------
#      sql_clean_ddl = os.path.join(context['files_location'],'drop-all-db-objects.sql')
#  
#      f_clean_log=open( os.path.join(context['temp_directory'],'tmp_gh_6795_drop-all-db-objects.log'), 'w')
#      f_clean_err=open( ''.join( ( os.path.splitext(f_clean_log.name)[0], '.err') ), 'w')
#      subprocess.call( [context['isql_path'], 'localhost:' + db_main, '-q', '-nod', '-i', sql_clean_ddl], stdout=f_clean_log, stderr=f_clean_err )
#      flush_and_close(f_clean_log)
#      flush_and_close(f_clean_err)
#  
#      with open(f_clean_err.name,'r') as f:
#          for line in f:
#              print('UNEXPECTED STDERR in cleanup SQL: ' + line)
#              MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 0
#  
#      with open(f_clean_log.name,'r') as f:
#          for line in f:
#              # show number of dropped objects
#              print(line)
#  
#      if MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG: # ==> initial SQL script finished w/o errors
#  
#          ##############################################################################
#          ###  W A I T   U N T I L    R E P L I C A    B E C O M E S   A C T U A L   ###
#          ##############################################################################
#          wait_for_data_in_replica( FB_HOME, MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG, db_main, 'POINT-2' )
#  
#          f_main_meta_sql=open( os.path.join(context['temp_directory'],'tmp_gh_6795_db_main_meta.sql'), 'w')
#          subprocess.call( [context['isql_path'], 'localhost:' + db_main, '-q', '-nod', '-ch', 'utf8', '-x'], stdout=f_main_meta_sql, stderr=subprocess.STDOUT )
#          flush_and_close( f_main_meta_sql )
#  
#          f_repl_meta_sql=open( os.path.join(context['temp_directory'],'tmp_gh_6795_db_repl_meta.sql'), 'w')
#          subprocess.call( [context['isql_path'], 'localhost:' + db_repl, '-q', '-nod', '-ch', 'utf8', '-x'], stdout=f_repl_meta_sql, stderr=subprocess.STDOUT )
#          flush_and_close( f_repl_meta_sql )
#  
#          db_main_meta=open(f_main_meta_sql.name, 'r')
#          db_repl_meta=open(f_repl_meta_sql.name, 'r')
#  
#          diffmeta = ''.join(difflib.unified_diff(
#              db_main_meta.readlines(), 
#              db_repl_meta.readlines()
#            ))
#          db_main_meta.close()
#          db_repl_meta.close()
#  
#          f_meta_diff=open( os.path.join(context['temp_directory'],'tmp_gh_6795_db_meta_diff.txt'), 'w', buffering = 0)
#          f_meta_diff.write(diffmeta)
#          flush_and_close( f_meta_diff )
#  
#          # Following must issue only TWO rows:
#          #     UNEXPECTED METADATA DIFF.: -/* CREATE DATABASE 'localhost:[db_main]' ... */
#          #     UNEXPECTED METADATA DIFF.: -/* CREATE DATABASE 'localhost:[db_repl]' ... */
#          # Only thes lines will be suppressed further (see subst. section):
#          with open(f_meta_diff.name, 'r') as f:
#              for line in f:
#                 if line[:1] in ('-', '+') and line[:3] not in ('---','+++'):
#                     print('UNEXPECTED METADATA DIFF.: ' + line)
#  
#  ######################
#  ### A C H T U N G  ###
#  ######################
#  # MANDATORY, OTHERWISE REPLICATION GETS STUCK ON SECOND RUN OF THIS TEST
#  # WITH 'ERROR: Record format with length NN is not found for table TEST':
#  runProgram('gfix', ['-sweep', 'localhost:' + db_repl])
#  runProgram('gfix', ['-sweep', 'localhost:' + db_main])
#  #######################
#  
#  
#  # cleanup:
#  ##########
#  cleanup( (f_sql_chk, f_sql_log, f_sql_err,f_clean_log,f_clean_err,f_main_meta_sql,f_repl_meta_sql,f_meta_diff) )
#    
#---
act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    POINT-1 FOUND message about replicated segment.
    EMPTY_STRING_BLOB_ON_REPLICA    1
    Start removing objects
    Finish. Total objects removed
    POINT-2 FOUND message about replicated segment.
"""

@pytest.mark.version('>=4.0')
@pytest.mark.platform('Windows')
@pytest.mark.xfail
def test_1(act_1: Action):
    pytest.fail("Test not IMPLEMENTED")


