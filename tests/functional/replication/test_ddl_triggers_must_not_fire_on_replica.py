#coding:utf-8
#
# id:           tests.functional.replication.ddl_triggers_must_not_fire_on_replica
# title:        DDL-triggers must fire only on master DB.
# decription:   
#                   Test creates all kinds of DDL triggers in the master DB.
#                   Each of them registers apropriate event in the table with name 'log_ddl_triggers_activity'.
#                   After this we create all kinds of DB objects (tables, procedure, function, etc) in master DB to fire these triggers.
#               
#                   Then we wait until replica becomes actual to master, and this delay will last no more then threshold
#                   that is defined by MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG variable (measured in seconds).
#                   During this delay, we check every second for replication log and search there line with number of last generated
#                   segment (which was replicated and deleting finally).
#                   We can assume that replication finished OK only when such line is found see ('POINT-1').
#                   
#                   After this, we do following:
#                   1) compare metadata of master and replica DB, they must be equal (except file names);
#                   2) obtain data from 'log_ddl_triggers_activity' table:
#                     2.1) on master it must have record about every DDL-trigger that fired;
#                     2.2) on replica this table must be EMPTY (bacause DDL triggers must not fire on replica).
#                    
#                   Then we invoke ISQL with executing auxiliary script for drop all DB objects on master (with '-nod' command switch).
#                   After all objects will be dropped, we have to wait again until replica becomes actual with master (see 'POINT-2').
#               
#                   Finally, we extract metadata for master and replica after this cleanup and compare them.
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
#                   Master and replica databases must be created in "!fbt_repo!	mp" directory and have names like these:
#                       'fbt-main.fb40.SS.fdb'; 'fbt-repl.fb40.SS.fdb'; - for FB 4.x ('SS' = Super; 'CS' = Classic)
#                       'fbt-main.fb50.SS.fdb'; 'fbt-repl.fb50.SS.fdb'; - for FB 5.x ('SS' = Super; 'CS' = Classic)
#                       NB: fixed numeric value ('40' or '50') must be used for any minor FB version (4.0; 4.0.1; 4.1; 5.0; 5.1 etc)
#               
#                   These two databases must NOT be dropped in any of tests related to replication!
#                   They are created and dropped in the batch scenario which prepares FB instance to be checked for each ServerMode
#                   and make cleanup after it, i.e. when all tests will be completed.
#               
#                   NB. Currently this task was implemented only in Windows batch, thus test has attribute platform = 'Windows'.
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
#               bt-run2.bat ddl-triggers-must-not-fire-on-replica.fbt 50ss, etc
#               
#                   Checked on:
#                       4.0.1.2547 (SS/CS), 5.0.0.120 (SS/CS).
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

db_1 = db_factory(charset='UTF8', sql_dialect=3, init=init_script_1)

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
#  MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 75
#  KEEP_LOGS_FOR_DEBUG = 0
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
#  def compare_metadata(db_main, db_repl, nm_suffix = '', keep4dbg = 0):
#  
#      global subprocess, difflib, flush_and_close, cleanup
#  
#      f_main_meta_sql=open( os.path.join(context['temp_directory'],'db_main_meta'+nm_suffix+'.sql'), 'w')
#      subprocess.call( [context['isql_path'], 'localhost:' + db_main, '-q', '-nod', '-ch', 'utf8', '-x'], stdout=f_main_meta_sql, stderr=subprocess.STDOUT )
#      flush_and_close( f_main_meta_sql )
#  
#      f_repl_meta_sql=open( os.path.join(context['temp_directory'],'db_repl_meta'+nm_suffix+'.sql'), 'w')
#      subprocess.call( [context['isql_path'], 'localhost:' + db_repl, '-q', '-nod', '-ch', 'utf8', '-x'], stdout=f_repl_meta_sql, stderr=subprocess.STDOUT )
#      flush_and_close( f_repl_meta_sql )
#  
#      db_main_meta=open(f_main_meta_sql.name, 'r')
#      db_repl_meta=open(f_repl_meta_sql.name, 'r')
#  
#      diffmeta = ''.join(difflib.unified_diff(
#          db_main_meta.readlines(), 
#          db_repl_meta.readlines()
#        ))
#      db_main_meta.close()
#      db_repl_meta.close()
#  
#      f_meta_diff=open( os.path.join(context['temp_directory'],'db_meta_diff'+nm_suffix+'.txt'), 'w')
#      f_meta_diff.write(diffmeta)
#      flush_and_close( f_meta_diff )
#  
#      # Following must issue only TWO rows:
#      #     UNEXPECTED METADATA DIFF.: -/* CREATE DATABASE 'localhost:[db_main]' ... */
#      #     UNEXPECTED METADATA DIFF.: -/* CREATE DATABASE 'localhost:[db_repl]' ... */
#      # Only thes lines will be suppressed further (see subst. section):
#      with open(f_meta_diff.name, 'r') as f:
#          for line in f:
#             if line[:1] in ('-', '+') and line[:3] not in ('---','+++'):
#                 print('UNEXPECTED METADATA DIFF.: ' + line)
#  
#      if not keep4dbg:
#          cleanup( (f_main_meta_sql,f_repl_meta_sql,f_meta_diff ) )
#  
#  #--------------------------------------------
#  
#  sql_ddl = '''    set bail on;
#      set list on;
#      
#      select mon$database_name from mon$database;
#  
#      recreate table log_ddl_triggers_activity (
#          id int generated by default as identity constraint pk_log_ddl_triggers_activity primary key
#          ,ddl_trigger_name varchar(64)
#          ,event_type varchar(25) not null
#          ,object_type varchar(25) not null
#          ,ddl_event varchar(25) not null
#          ,object_name varchar(64) not null
#      );
#  
#  
#      set term ^;
#      execute block as
#          declare v_lf char(1) = x'0A';
#      begin
#          rdb$set_context('USER_SESSION', 'SKIP_DDL_TRIGGER', '1');
#  
#          for
#              with
#              a as (
#                  select 'ANY DDL STATEMENT' x from rdb$database union all
#                  select 'CREATE TABLE' from rdb$database union all
#                  select 'ALTER TABLE' from rdb$database union all
#                  select 'DROP TABLE' from rdb$database union all
#                  select 'CREATE PROCEDURE' from rdb$database union all
#                  select 'ALTER PROCEDURE' from rdb$database union all
#                  select 'DROP PROCEDURE' from rdb$database union all
#                  select 'CREATE FUNCTION' from rdb$database union all
#                  select 'ALTER FUNCTION' from rdb$database union all
#                  select 'DROP FUNCTION' from rdb$database union all
#                  select 'CREATE TRIGGER' from rdb$database union all
#                  select 'ALTER TRIGGER' from rdb$database union all
#                  select 'DROP TRIGGER' from rdb$database union all
#                  select 'CREATE EXCEPTION' from rdb$database union all
#                  select 'ALTER EXCEPTION' from rdb$database union all
#                  select 'DROP EXCEPTION' from rdb$database union all
#                  select 'CREATE VIEW' from rdb$database union all
#                  select 'ALTER VIEW' from rdb$database union all
#                  select 'DROP VIEW' from rdb$database union all
#                  select 'CREATE DOMAIN' from rdb$database union all
#                  select 'ALTER DOMAIN' from rdb$database union all
#                  select 'DROP DOMAIN' from rdb$database union all
#                  select 'CREATE ROLE' from rdb$database union all
#                  select 'ALTER ROLE' from rdb$database union all
#                  select 'DROP ROLE' from rdb$database union all
#                  select 'CREATE SEQUENCE' from rdb$database union all
#                  select 'ALTER SEQUENCE' from rdb$database union all
#                  select 'DROP SEQUENCE' from rdb$database union all
#                  select 'CREATE USER' from rdb$database union all
#                  select 'ALTER USER' from rdb$database union all
#                  select 'DROP USER' from rdb$database union all
#                  select 'CREATE INDEX' from rdb$database union all
#                  select 'ALTER INDEX' from rdb$database union all
#                  select 'DROP INDEX' from rdb$database union all
#                  select 'CREATE COLLATION' from rdb$database union all
#                  select 'DROP COLLATION' from rdb$database union all
#                  select 'ALTER CHARACTER SET' from rdb$database union all
#                  select 'CREATE PACKAGE' from rdb$database union all
#                  select 'ALTER PACKAGE' from rdb$database union all
#                  select 'DROP PACKAGE' from rdb$database union all
#                  select 'CREATE PACKAGE BODY' from rdb$database union all
#                  select 'DROP PACKAGE BODY' from rdb$database
#              )
#              ,e as (
#                  select 'before' w from rdb$database union all select 'after' from rdb$database
#              )
#              ,t as (
#                  select upper(trim(replace(trim(a.x),' ','_')) || iif(e.w='before', '_before', '_after')) as trg_name, a.x, e.w
#                  from e, a
#              )
#  
#              select
#                     'create or alter trigger trg_' || t.trg_name
#                  || ' active ' || t.w || ' ' || trim(t.x) || ' as '
#                  || :v_lf
#                  || 'begin'
#                  || :v_lf
#                  || q'{    if (rdb$get_context('USER_SESSION', 'SKIP_DDL_TRIGGER') is null) then}'
#                  || :v_lf
#                  || '        insert into log_ddl_triggers_activity(ddl_trigger_name, event_type, object_type, ddl_event, object_name) values('
#                  || :v_lf
#                  || q'{'}' || trim(t.trg_name) || q'{'}'
#                  || :v_lf
#                  || q'{, rdb$get_context('DDL_TRIGGER', 'EVENT_TYPE')}'
#                  || :v_lf
#                  || q'{, rdb$get_context('DDL_TRIGGER', 'OBJECT_TYPE')}'
#                  || :v_lf
#                  || q'{, rdb$get_context('DDL_TRIGGER', 'DDL_EVENT')}'
#                  || :v_lf
#                  || q'{, rdb$get_context('DDL_TRIGGER', 'OBJECT_NAME')}'
#                  || :v_lf
#                  || ');'
#                  || :v_lf
#                  || ' end'
#                  as sttm
#              from t
#              as cursor c
#           do begin
#               execute statement(c.sttm) with autonomous transaction;
#           end
#  
#          rdb$set_context('USER_SESSION', 'SKIP_DDL_TRIGGER', null);
#      end
#      ^
#      set term ;^
#      commit;
#  
#      /*
#      select rt.rdb$trigger_name,rt.rdb$relation_name,rt.rdb$trigger_type,rt.rdb$trigger_source
#      from rdb$triggers rt
#      where
#          rt.rdb$system_flag is distinct from 1
#          and rt.rdb$trigger_inactive is distinct from 1;
#  
#      select * from log_ddl_triggers_activity;
#      */
#  
#      -- set count on;
#      -- set echo on;
#  
#      set term ^;
#  
#      create table test(id int not null, name varchar(10))
#      ^
#      alter table test add constraint test_pk primary key(id)
#      ^
#      ----------
#      create procedure sp_test as begin end
#      ^
#      alter procedure sp_test as declare x int; begin x=1; end
#      ^
#      ----------
#      create function fn_test(a_id int) returns bigint as
#      begin
#          return a_id * a_id;
#      end
#      ^
#      alter function fn_test(a_id int) returns int128 as
#      begin
#          return a_id * a_id * a_id;
#      end
#      ^
#      ----------
#      create trigger trg_connect_test on connect as
#      begin
#      end
#      ^
#      alter trigger trg_connect_test as
#          declare x int;
#      begin
#          x = 1;
#      end
#      ^
#      ----------
#      create exception exc_test 'Invalud value: @1'
#      ^
#      alter exception exc_test 'Bad values: @1 and @2'
#      ^
#      ----------
#      create view v_test as select 1 x from rdb$database
#      ^
#      alter view v_test as select 1 x, 2 y from rdb$database
#      ^
#      ----------
#      create domain dm_test int
#      ^
#      alter domain dm_test set not null
#      ^
#      ----------
#      create role r_test
#      ^
#      alter role r_test set system privileges to use_gstat_utility, ignore_db_triggers
#      ^
#      ----------
#      create sequence g_test
#      ^
#      alter sequence g_test restart with 123
#      ^
#      ----------
#      /*
#      create or alter user u_test password '123' using plugin Srp
#      ^
#      alter user u_test password '456'
#      ^
#      */
#      ----------
#      create index test_name on test(name)
#      ^
#      alter index test_name inactive
#      ^
#      ----------
#      create collation name_coll for utf8 from unicode case insensitive
#      ^
#      ----------
#      alter character set iso8859_1 set default collation pt_br
#      ^
#      ----------
#      create or alter package pg_test as
#      begin
#         function pg_fn1 returns int;
#      end
#      ^
#      alter package pg_test as
#      begin
#         function pg_fn1(a_x int) returns int128;
#      end
#      ^
#  
#      create package body pg_test as
#      begin
#         function pg_fn1(a_x int) returns int128 as
#         begin
#             return a_x * a_x * a_x;
#         end
#      end
#      ^
#      set term ;^
#      commit;
#  
#  
#      select rdb$get_context('SYSTEM','REPLICATION_SEQUENCE') as last_generated_repl_segment from rdb$database;
#      quit;
#  ''' % locals()
#  
#  
#  f_sql_chk = open( os.path.join(context['temp_directory'],'tmp_repltest_skip_ddl_trg.sql'), 'w')
#  f_sql_chk.write(sql_ddl)
#  flush_and_close( f_sql_chk )
#  
#  f_sql_log = open( ''.join( (os.path.splitext(f_sql_chk.name)[0], '.log' ) ), 'w')
#  f_sql_err = open( ''.join( (os.path.splitext(f_sql_chk.name)[0], '.err' ) ), 'w')
#  subprocess.call( [ context['isql_path'], 'localhost:' + db_main, '-i', f_sql_chk.name ], stdout = f_sql_log, stderr = f_sql_err)
#  flush_and_close( f_sql_log )
#  flush_and_close( f_sql_err )
#  
#  with open(f_sql_err.name,'r') as f:
#      for line in f:
#          print('UNEXPECTED STDERR in initial SQL: ' + line)
#          MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 0
#  
#  
#  if MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG: # ==> initial SQL script finished w/o errors
#  
#      ##############################################################################
#      ###  W A I T   U N T I L    R E P L I C A    B E C O M E S   A C T U A L   ###
#      ##############################################################################
#      wait_for_data_in_replica( FB_HOME, MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG, db_main, 'POINT-1' )
#  
#      compare_metadata(db_main, db_repl, '.1', KEEP_LOGS_FOR_DEBUG)
#  
#      sql_get_result =    '''
#          set list on;
#          set count on;
#          select
#              iif(coalesce(rdb$get_context('SYSTEM','REPLICA_MODE'),'') = '', 'MASTER', 'REPLICA') as replication_mode
#              ,a.id
#              ,a.ddl_trigger_name
#              ,a.event_type
#              ,a.object_type
#              ,a.ddl_event
#              ,a.object_name
#          from rdb$database r
#          left join log_ddl_triggers_activity a on 1=1
#          order by a.id;
#      '''
#  
#      runProgram('isql', ['localhost:' + db_main, '-nod'], sql_get_result)
#      runProgram('isql', ['localhost:' + db_repl, '-nod'], sql_get_result)
#  
#  
#  # return initial state of master DB:
#  # remove all DB objects (tables, views, ...):
#  # --------------------------------------------
#  sql_clean_ddl = os.path.join(context['files_location'],'drop-all-db-objects.sql')
#  
#  f_clean_log=open( os.path.join(context['temp_directory'],'drop-all-db-objects.log'), 'w')
#  f_clean_err=open( ''.join( ( os.path.splitext(f_clean_log.name)[0], '.err') ), 'w')
#  subprocess.call( [context['isql_path'], 'localhost:' + db_main, '-q', '-nod', '-i', sql_clean_ddl], stdout=f_clean_log, stderr=f_clean_err )
#  flush_and_close(f_clean_log)
#  flush_and_close(f_clean_err)
#  
#  with open(f_clean_err.name,'r') as f:
#      for line in f:
#          print('UNEXPECTED STDERR in cleanup SQL: ' + line)
#          MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG = 0
#  
#  with open(f_clean_log.name,'r') as f:
#      for line in f:
#          # show number of dropped objects
#          print(line)
#  
#  if MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG: # ==> initial SQL script finished w/o errors
#  
#      ##############################################################################
#      ###  W A I T   U N T I L    R E P L I C A    B E C O M E S   A C T U A L   ###
#      ##############################################################################
#      wait_for_data_in_replica( FB_HOME, MAX_TIME_FOR_WAIT_SEGMENT_IN_LOG, db_main, 'POINT-2' )
#  
#      compare_metadata(db_main, db_repl, '.2', KEEP_LOGS_FOR_DEBUG)
#  
#  # cleanup:
#  ##########
#  if not KEEP_LOGS_FOR_DEBUG:
#      cleanup( (f_sql_chk, f_sql_log, f_sql_err, f_clean_log, f_clean_err) )
#    
#---
act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    POINT-1 FOUND message about replicated segment.

    REPLICATION_MODE                MASTER
    ID                              1
    DDL_TRIGGER_NAME                CREATE_TABLE_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       CREATE TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              2
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       CREATE TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              3
    DDL_TRIGGER_NAME                CREATE_TABLE_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       CREATE TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              4
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       CREATE TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              5
    DDL_TRIGGER_NAME                ALTER_TABLE_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       ALTER TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              6
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       ALTER TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              7
    DDL_TRIGGER_NAME                ALTER_TABLE_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       ALTER TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              8
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TABLE
    DDL_EVENT                       ALTER TABLE
    OBJECT_NAME                     TEST
    REPLICATION_MODE                MASTER
    ID                              9
    DDL_TRIGGER_NAME                CREATE_PROCEDURE_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       CREATE PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              10
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       CREATE PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              11
    DDL_TRIGGER_NAME                CREATE_PROCEDURE_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       CREATE PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              12
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       CREATE PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              13
    DDL_TRIGGER_NAME                ALTER_PROCEDURE_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       ALTER PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              14
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       ALTER PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              15
    DDL_TRIGGER_NAME                ALTER_PROCEDURE_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       ALTER PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              16
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PROCEDURE
    DDL_EVENT                       ALTER PROCEDURE
    OBJECT_NAME                     SP_TEST
    REPLICATION_MODE                MASTER
    ID                              17
    DDL_TRIGGER_NAME                CREATE_FUNCTION_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       CREATE FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              18
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       CREATE FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              19
    DDL_TRIGGER_NAME                CREATE_FUNCTION_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       CREATE FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              20
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       CREATE FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              21
    DDL_TRIGGER_NAME                ALTER_FUNCTION_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       ALTER FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              22
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       ALTER FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              23
    DDL_TRIGGER_NAME                ALTER_FUNCTION_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       ALTER FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              24
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     FUNCTION
    DDL_EVENT                       ALTER FUNCTION
    OBJECT_NAME                     FN_TEST
    REPLICATION_MODE                MASTER
    ID                              25
    DDL_TRIGGER_NAME                CREATE_TRIGGER_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       CREATE TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              26
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       CREATE TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              27
    DDL_TRIGGER_NAME                CREATE_TRIGGER_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       CREATE TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              28
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       CREATE TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              29
    DDL_TRIGGER_NAME                ALTER_TRIGGER_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       ALTER TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              30
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       ALTER TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              31
    DDL_TRIGGER_NAME                ALTER_TRIGGER_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       ALTER TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              32
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     TRIGGER
    DDL_EVENT                       ALTER TRIGGER
    OBJECT_NAME                     TRG_CONNECT_TEST
    REPLICATION_MODE                MASTER
    ID                              33
    DDL_TRIGGER_NAME                CREATE_EXCEPTION_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       CREATE EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              34
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       CREATE EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              35
    DDL_TRIGGER_NAME                CREATE_EXCEPTION_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       CREATE EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              36
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       CREATE EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              37
    DDL_TRIGGER_NAME                ALTER_EXCEPTION_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       ALTER EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              38
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       ALTER EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              39
    DDL_TRIGGER_NAME                ALTER_EXCEPTION_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       ALTER EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              40
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     EXCEPTION
    DDL_EVENT                       ALTER EXCEPTION
    OBJECT_NAME                     EXC_TEST
    REPLICATION_MODE                MASTER
    ID                              41
    DDL_TRIGGER_NAME                CREATE_VIEW_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       CREATE VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              42
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       CREATE VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              43
    DDL_TRIGGER_NAME                CREATE_VIEW_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       CREATE VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              44
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       CREATE VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              45
    DDL_TRIGGER_NAME                ALTER_VIEW_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       ALTER VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              46
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       ALTER VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              47
    DDL_TRIGGER_NAME                ALTER_VIEW_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       ALTER VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              48
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     VIEW
    DDL_EVENT                       ALTER VIEW
    OBJECT_NAME                     V_TEST
    REPLICATION_MODE                MASTER
    ID                              49
    DDL_TRIGGER_NAME                CREATE_DOMAIN_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       CREATE DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              50
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       CREATE DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              51
    DDL_TRIGGER_NAME                CREATE_DOMAIN_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       CREATE DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              52
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       CREATE DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              53
    DDL_TRIGGER_NAME                ALTER_DOMAIN_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       ALTER DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              54
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       ALTER DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              55
    DDL_TRIGGER_NAME                ALTER_DOMAIN_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       ALTER DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              56
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     DOMAIN
    DDL_EVENT                       ALTER DOMAIN
    OBJECT_NAME                     DM_TEST
    REPLICATION_MODE                MASTER
    ID                              57
    DDL_TRIGGER_NAME                CREATE_ROLE_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       CREATE ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              58
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       CREATE ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              59
    DDL_TRIGGER_NAME                CREATE_ROLE_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       CREATE ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              60
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       CREATE ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              61
    DDL_TRIGGER_NAME                ALTER_ROLE_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       ALTER ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              62
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       ALTER ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              63
    DDL_TRIGGER_NAME                ALTER_ROLE_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       ALTER ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              64
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     ROLE
    DDL_EVENT                       ALTER ROLE
    OBJECT_NAME                     R_TEST
    REPLICATION_MODE                MASTER
    ID                              65
    DDL_TRIGGER_NAME                CREATE_SEQUENCE_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       CREATE SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              66
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       CREATE SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              67
    DDL_TRIGGER_NAME                CREATE_SEQUENCE_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       CREATE SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              68
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       CREATE SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              69
    DDL_TRIGGER_NAME                ALTER_SEQUENCE_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       ALTER SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              70
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       ALTER SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              71
    DDL_TRIGGER_NAME                ALTER_SEQUENCE_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       ALTER SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              72
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     SEQUENCE
    DDL_EVENT                       ALTER SEQUENCE
    OBJECT_NAME                     G_TEST
    REPLICATION_MODE                MASTER
    ID                              73
    DDL_TRIGGER_NAME                CREATE_INDEX_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       CREATE INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              74
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       CREATE INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              75
    DDL_TRIGGER_NAME                CREATE_INDEX_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       CREATE INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              76
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       CREATE INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              77
    DDL_TRIGGER_NAME                ALTER_INDEX_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       ALTER INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              78
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       ALTER INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              79
    DDL_TRIGGER_NAME                ALTER_INDEX_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       ALTER INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              80
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     INDEX
    DDL_EVENT                       ALTER INDEX
    OBJECT_NAME                     TEST_NAME
    REPLICATION_MODE                MASTER
    ID                              81
    DDL_TRIGGER_NAME                CREATE_COLLATION_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     COLLATION
    DDL_EVENT                       CREATE COLLATION
    OBJECT_NAME                     NAME_COLL
    REPLICATION_MODE                MASTER
    ID                              82
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     COLLATION
    DDL_EVENT                       CREATE COLLATION
    OBJECT_NAME                     NAME_COLL
    REPLICATION_MODE                MASTER
    ID                              83
    DDL_TRIGGER_NAME                CREATE_COLLATION_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     COLLATION
    DDL_EVENT                       CREATE COLLATION
    OBJECT_NAME                     NAME_COLL
    REPLICATION_MODE                MASTER
    ID                              84
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     COLLATION
    DDL_EVENT                       CREATE COLLATION
    OBJECT_NAME                     NAME_COLL
    REPLICATION_MODE                MASTER
    ID                              85
    DDL_TRIGGER_NAME                ALTER_CHARACTER_SET_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     CHARACTER SET
    DDL_EVENT                       ALTER CHARACTER SET
    OBJECT_NAME                     ISO8859_1
    REPLICATION_MODE                MASTER
    ID                              86
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     CHARACTER SET
    DDL_EVENT                       ALTER CHARACTER SET
    OBJECT_NAME                     ISO8859_1
    REPLICATION_MODE                MASTER
    ID                              87
    DDL_TRIGGER_NAME                ALTER_CHARACTER_SET_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     CHARACTER SET
    DDL_EVENT                       ALTER CHARACTER SET
    OBJECT_NAME                     ISO8859_1
    REPLICATION_MODE                MASTER
    ID                              88
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     CHARACTER SET
    DDL_EVENT                       ALTER CHARACTER SET
    OBJECT_NAME                     ISO8859_1
    REPLICATION_MODE                MASTER
    ID                              89
    DDL_TRIGGER_NAME                CREATE_PACKAGE_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       CREATE PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              90
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       CREATE PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              91
    DDL_TRIGGER_NAME                CREATE_PACKAGE_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       CREATE PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              92
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       CREATE PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              93
    DDL_TRIGGER_NAME                ALTER_PACKAGE_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       ALTER PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              94
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       ALTER PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              95
    DDL_TRIGGER_NAME                ALTER_PACKAGE_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       ALTER PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              96
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      ALTER
    OBJECT_TYPE                     PACKAGE
    DDL_EVENT                       ALTER PACKAGE
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              97
    DDL_TRIGGER_NAME                CREATE_PACKAGE_BODY_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE BODY
    DDL_EVENT                       CREATE PACKAGE BODY
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              98
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_BEFORE
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE BODY
    DDL_EVENT                       CREATE PACKAGE BODY
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              99
    DDL_TRIGGER_NAME                CREATE_PACKAGE_BODY_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE BODY
    DDL_EVENT                       CREATE PACKAGE BODY
    OBJECT_NAME                     PG_TEST
    REPLICATION_MODE                MASTER
    ID                              100
    DDL_TRIGGER_NAME                ANY_DDL_STATEMENT_AFTER
    EVENT_TYPE                      CREATE
    OBJECT_TYPE                     PACKAGE BODY
    DDL_EVENT                       CREATE PACKAGE BODY
    OBJECT_NAME                     PG_TEST
    Records affected: 100

    
    REPLICATION_MODE                REPLICA
    ID                              <null>
    DDL_TRIGGER_NAME                <null>
    EVENT_TYPE                      <null>
    OBJECT_TYPE                     <null>
    DDL_EVENT                       <null>
    OBJECT_NAME                     <null>
    Records affected: 1

    Start removing objects
    Finish. Total objects removed

    POINT-2 FOUND message about replicated segment.

"""

@pytest.mark.version('>=4.0')
@pytest.mark.platform('Windows')
@pytest.mark.xfail
def test_1(act_1: Action):
    pytest.fail("Test not IMPLEMENTED")

