#coding:utf-8
#
# id:           bugs.core_4292
# title:        Server ignores asynchronous (monitoring or cancellation) requests while preparing a query with lot of windowed functions
# decription:
#                   Preparing stage of test query will last lot of time even on power host.
#                   We launch separate (child) process with ISQL and allow him to start preparing this query during several
#                   seconds. Then we launch second child process with ISQL and try to kill first one.
#                   Before this ticket was fixed it was NOT possible neither to cancel it by using MON$ATTACHMENTS nor even
#                   query MON$ tables at all (until this 'complex query' preparing finish).
#
#                   Checked on WI-V3.0.0.32081, SS / SC / CS. Result: all fine.
#                   11.05.2017: checked on WI-T4.0.0.638 - added filtering to messages about shutdown state, see comments below.
#
# tracker_id:   CORE-4292
# min_versions: ['3.0']
# versions:     3.0
# qmid:         None

import pytest
import subprocess
import time
from pathlib import Path
from firebird.qa import db_factory, python_act, Action, temp_file

# version: 3.0
# resources: None

substitutions_1 = [('.*line.*', ''), ('.*Killed by database administrator.*', ''), ('[\t ]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# import os
#  import subprocess
#  from subprocess import Popen
#  import time
#
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#
#  db_conn.close()
#
#  #-----------------------------------
#
#  def flush_and_close(file_handle):
#      # https://docs.python.org/2/library/os.html#os.fsync
#      # If you're starting with a Python file object f,
#      # first do f.flush(), and
#      # then do os.fsync(f.fileno()), to ensure that all internal buffers associated with f are written to disk.
#      global os
#
#      file_handle.flush()
#      os.fsync(file_handle.fileno())
#
#      file_handle.close()
#
#  #--------------------------------------------
#
#  def cleanup( f_names_list ):
#      global os
#      for i in range(len( f_names_list )):
#         if os.path.isfile( f_names_list[i]):
#              os.remove( f_names_list[i] )
#              if os.path.isfile( f_names_list[i]):
#                  print('ERROR: can not remove file ' + f_names_list[i])
#
#  #--------------------------------------------
#
#  heavy_sql = '''
#      set bail on;
#      set list on;
#      set count on;
#      with a as (
#          select rf.rdb$field_id fid, rr.rdb$relation_id rid, rr.rdb$relation_name rnm
#          from rdb$relation_fields rf join rdb$relations rr on rf.rdb$relation_name=rr.rdb$relation_name
#      )
#      ,b as (
#          select fid, rnm, rid, iif(rid is null, 1, r) r
#          from (--f
#              select fid, rnm, rid,
#                      iif(lag(fid) over(partition by rid order by fid) is not null
#                          and lag(r) over(partition by rid order by fid) >= r
#                          , r + 1, r) r
#              from (--e
#                  select fid, rnm, rid,
#                          iif(lag(fid) over(partition by rid order by fid) is not null
#                              and lag(r) over(partition by rid order by fid) >= r
#                              , r + 1, r) r
#                  from (--d
#                      select fid, rnm, rid,
#                              iif(lag(fid) over(partition by rid order by fid) is not null
#                                  and lag(r) over(partition by rid order by fid) >= r
#                                  , r + 1, r) r
#                      from (--c
#                          select fid, rnm, rid,
#                                  iif(lag(fid) over(partition by rid order by fid) is not null
#                                      and lag(r) over(partition by rid order by fid) >= r
#                                 ,r + 1, r) r
#                          from (--b
#                              select fid, rnm, rid,
#                                      iif( lag(fid) over(partition by rid order by fid) is not null
#                                            and lag(r) over(partition by rid order by fid) >= r
#                                           ,r + 1, r) r
#                              from (
#                                      select a.*, 1 r
#                                      from a
#                                    ) a
#                              ) b
#                        ) c
#                    ) d
#                ) e
#            ) f
#      )
#      -- select max(r) r from b group by fid having max(r) < 6; -- ok
#
#      ,c
#      as (
#          select fid, rnm, rid, iif(rid is null, 1, r) r
#          from (--f
#              select fid, rnm, rid,
#                      iif(lag(fid) over(partition by rid order by fid) is not null
#                           and lag(r) over(partition by rid order by fid) >= r
#                          , r + 1, r) r
#              from (--e
#                  select fid, rnm, rid,
#                          iif(lag(fid) over(partition by rid order by fid) is not null
#                               and lag(r) over(partition by rid order by fid) >= r
#                              , r + 1, r) r
#                  from (--d
#                      select fid, rnm, rid,
#                              iif(lag(fid) over(partition by rid order by fid) is not null
#                                   and lag(r) over(partition by rid order by fid) >= r
#                                  , r + 1, r) r
#                      from (--c
#                          select fid, rnm, rid,
#                                  iif(lag(fid) over(partition by rid order by fid) is not null
#                                       and lag(r) over(partition by rid order by fid) >= r
#                                 ,r + 1, r) r
#                          from (--b
#                              select fid, rnm, rid,
#                                      iif( lag(fid) over(partition by rid order by fid) is not null
#                                            and lag(r) over(partition by rid order by fid) >= r
#                                           ,r + 1, r) r
#                              from (
#                                      select fid, rnm, rid, max(r) over(partition by fid) r from b
#                                    ) a
#                              ) b
#                        ) c
#                    ) d
#                ) e
#            ) f
#      )
#      -- select * from c -- ok
#
#      ,d
#      as (
#          select fid, rnm, rid, iif(rid is null, 1, r) r
#          from (--f
#              select fid, rnm, rid,
#                      iif( lag(fid) over(partition by rid order by fid) is not null
#                           and lag(r) over(partition by rid order by fid) >= r
#                          , r + 1, r) r
#              from (--e
#                  select fid, rnm, rid,
#                          iif( lag(fid) over(partition by rid order by fid) is not null
#                               and lag(r) over(partition by rid order by fid) >= r
#                              , r + 1, r) r
#                  from (--d
#                      select fid, rnm, rid,
#                              iif( lag(fid) over(partition by rid order by fid) is not null
#                                   and lag(r) over(partition by rid order by fid) >= r
#                                  , r + 1, r) r
#                      from (--c
#                          select fid, rnm, rid,
#                                  iif( lag(fid) over(partition by rid order by fid) is not null
#                                       and lag(r) over(partition by rid order by fid) >= r
#                                 ,r + 1, r) r
#                          from (--b
#                              select fid, rnm, rid,
#                                      iif( lag(fid) over(partition by rid order by fid) is not null
#                                            and lag(r) over(partition by rid order by fid) >= r
#                                           ,r + 1, r) r
#                              from (
#                                      select fid, rnm, rid, max(r) over(partition by fid) r from c
#                                    ) a
#                              ) b
#                        ) c
#                    ) d
#                ) e
#            ) f
#      )
#      select * from d rows 0;
#      set count off;
#      select 'WORKER FINISHED TOO FAST! DELAY IN TEST MUST BE REDUCED!' msg from rdb$database;
#
#  '''
#  f_worker_sql=open(os.path.join(context['temp_directory'],'tmp_worker_4292.sql'),'w')
#  f_worker_sql.write(heavy_sql)
#  flush_and_close( f_worker_sql )
#
#  f_worker_log=open( os.path.join(context['temp_directory'],'tmp_worker_4292.log'), 'w')
#
#  # Execute a child program in a new process, redirecting STDERR to the same target as of STDOUT:
#  p_worker = Popen([ context['isql_path'], dsn, "-i", f_worker_sql.name], stdout=f_worker_log, stderr=subprocess.STDOUT )
#
#  time.sleep(4)
#
#  killer_sql='''
#     set list on;
#     set count on;
#     /*
#     select a.*, s.*
#     from mon$attachments a
#     left join mon$statements s on a.mon$attachment_id = s.mon$attachment_id
#     where
#         a.mon$attachment_id <> current_connection
#         and a.mon$system_flag is distinct from 1
#     ;
#     */
#     select count(*) as "Found worker ?"
#     from mon$attachments a
#     where
#         a.mon$attachment_id <> current_connection
#         and a.mon$system_flag is distinct from 1
#     ;
#
#     delete from mon$attachments
#     where
#         mon$attachment_id <> current_connection
#         and mon$system_flag is distinct from 1
#     returning
#       sign(mon$attachment_id) as deleted_mon_att_id,
#       mon$user as deleted_mon_user,
#       iif(mon$remote_protocol containing 'tcp', 'tcp', null) as deleted_mon_protocol,
#       iif(mon$remote_process containing 'isql', 'isql', null) as deleted_mon_process,
#       mon$system_flag as deleted_mon_sys_flag
#     ;
#  '''
#
#  # 11.05.2017, FB 4.0 only!
#  # Following messages can appear after 'connection shutdown'
#  # (letter from dimitr, 08-may-2017 20:41):
#  #   isc_att_shut_killed: Killed by database administrator
#  #   isc_att_shut_idle: Idle timeout expired
#  #   isc_att_shut_db_down: Database is shutdown
#  #   isc_att_shut_engine: Engine is shutdown
#
#
#  f_killer_sql=open( os.path.join(context['temp_directory'],'tmp_killer_4292.sql'), 'w')
#  f_killer_sql.write(killer_sql)
#  flush_and_close( f_killer_sql )
#
#  # Execute a child program in a new process, redirecting STDERR to the same target as of STDOUT:
#
#  f_killer_log=open( os.path.join(context['temp_directory'],'tmp_killer_4292.log'), 'w')
#  p_killer = Popen([context['isql_path'] , dsn, "-i" , f_killer_sql.name], stdout=f_killer_log, stderr=subprocess.STDOUT )
#
#  # Make delay at least on 6 seconds after that point.
#  # Otherwise temp database will not be removed and we get:
#  # Exception AttributeError: "'Connection' object has no attribute '_Connection__ic'"
#  # in <bound method Connection.__del__ of <fdb.fbcore.Connection object at 0x023E4850>> ignored
#  # Test cleanup: Exception raised while dropping database.
#
#  time.sleep(6)
#
#  p_worker.terminate()
#  flush_and_close( f_worker_log )
#
#  p_killer.terminate()
#  flush_and_close( f_killer_log )
#
#  with open( f_killer_log.name,'r') as f:
#      for line in f:
#          if line.split():
#              print('KILLER LOG: ' + line)
#
#  with open( f_worker_log.name,'r') as f:
#      for line in f:
#          if line.split():
#              print('WORKER LOG: ' + line)
#
#
#  # CLEANUP
#  #########
#  time.sleep(1)
#  cleanup( [i.name for i in (f_worker_sql,f_worker_log,f_killer_sql,f_killer_log)] )
#
#
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1_killer = """
Found worker ?                  1
Records affected: 1
DELETED_MON_ATT_ID              1
DELETED_MON_USER                SYSDBA
DELETED_MON_PROTOCOL            tcp
DELETED_MON_PROCESS             isql
DELETED_MON_SYS_FLAG            0
"""

expected_stdout_1_worker = """
Statement failed, SQLSTATE = 08003
connection shutdown
"""

heavy_script_1 = temp_file('heavy_script.sql')
heavy_output_1 = temp_file('heavy_script.out')

@pytest.mark.version('>=3.0')
def test_1(act_1: Action, heavy_script_1: Path, heavy_output_1: Path):
    killer_sql = """
    set list on;
    set count on;
    /*
    select a.*, s.*
    from mon$attachments a
    left join mon$statements s on a.mon$attachment_id = s.mon$attachment_id
    where
        a.mon$attachment_id <> current_connection
        and a.mon$system_flag is distinct from 1
    ;
    */
    select count(*) as "Found worker ?"
    from mon$attachments a
    where
        a.mon$attachment_id <> current_connection
        and a.mon$system_flag is distinct from 1
    ;

    delete from mon$attachments
    where
        mon$attachment_id <> current_connection
        and mon$system_flag is distinct from 1
    returning
      sign(mon$attachment_id) as deleted_mon_att_id,
      mon$user as deleted_mon_user,
      iif(mon$remote_protocol containing 'tcp', 'tcp', null) as deleted_mon_protocol,
      iif(mon$remote_process containing 'isql', 'isql', null) as deleted_mon_process,
      mon$system_flag as deleted_mon_sys_flag
    ;
"""
    heavy_script_1.write_text("""
    set bail on;
    set list on;
    set count on;
    with a as (
        select rf.rdb$field_id fid, rr.rdb$relation_id rid, rr.rdb$relation_name rnm
        from rdb$relation_fields rf join rdb$relations rr on rf.rdb$relation_name=rr.rdb$relation_name
    )
    ,b as (
        select fid, rnm, rid, iif(rid is null, 1, r) r
        from (--f
            select fid, rnm, rid,
                    iif(lag(fid) over(partition by rid order by fid) is not null
                        and lag(r) over(partition by rid order by fid) >= r
                        , r + 1, r) r
            from (--e
                select fid, rnm, rid,
                        iif(lag(fid) over(partition by rid order by fid) is not null
                            and lag(r) over(partition by rid order by fid) >= r
                            , r + 1, r) r
                from (--d
                    select fid, rnm, rid,
                            iif(lag(fid) over(partition by rid order by fid) is not null
                                and lag(r) over(partition by rid order by fid) >= r
                                , r + 1, r) r
                    from (--c
                        select fid, rnm, rid,
                                iif(lag(fid) over(partition by rid order by fid) is not null
                                    and lag(r) over(partition by rid order by fid) >= r
                               ,r + 1, r) r
                        from (--b
                            select fid, rnm, rid,
                                    iif( lag(fid) over(partition by rid order by fid) is not null
                                          and lag(r) over(partition by rid order by fid) >= r
                                         ,r + 1, r) r
                            from (
                                    select a.*, 1 r
                                    from a
                                  ) a
                            ) b
                      ) c
                  ) d
              ) e
          ) f
    )
    -- select max(r) r from b group by fid having max(r) < 6; -- ok

    ,c
    as (
        select fid, rnm, rid, iif(rid is null, 1, r) r
        from (--f
            select fid, rnm, rid,
                    iif(lag(fid) over(partition by rid order by fid) is not null
                         and lag(r) over(partition by rid order by fid) >= r
                        , r + 1, r) r
            from (--e
                select fid, rnm, rid,
                        iif(lag(fid) over(partition by rid order by fid) is not null
                             and lag(r) over(partition by rid order by fid) >= r
                            , r + 1, r) r
                from (--d
                    select fid, rnm, rid,
                            iif(lag(fid) over(partition by rid order by fid) is not null
                                 and lag(r) over(partition by rid order by fid) >= r
                                , r + 1, r) r
                    from (--c
                        select fid, rnm, rid,
                                iif(lag(fid) over(partition by rid order by fid) is not null
                                     and lag(r) over(partition by rid order by fid) >= r
                               ,r + 1, r) r
                        from (--b
                            select fid, rnm, rid,
                                    iif( lag(fid) over(partition by rid order by fid) is not null
                                          and lag(r) over(partition by rid order by fid) >= r
                                         ,r + 1, r) r
                            from (
                                    select fid, rnm, rid, max(r) over(partition by fid) r from b
                                  ) a
                            ) b
                      ) c
                  ) d
              ) e
          ) f
    )
    -- select * from c -- ok

    ,d
    as (
        select fid, rnm, rid, iif(rid is null, 1, r) r
        from (--f
            select fid, rnm, rid,
                    iif( lag(fid) over(partition by rid order by fid) is not null
                         and lag(r) over(partition by rid order by fid) >= r
                        , r + 1, r) r
            from (--e
                select fid, rnm, rid,
                        iif( lag(fid) over(partition by rid order by fid) is not null
                             and lag(r) over(partition by rid order by fid) >= r
                            , r + 1, r) r
                from (--d
                    select fid, rnm, rid,
                            iif( lag(fid) over(partition by rid order by fid) is not null
                                 and lag(r) over(partition by rid order by fid) >= r
                                , r + 1, r) r
                    from (--c
                        select fid, rnm, rid,
                                iif( lag(fid) over(partition by rid order by fid) is not null
                                     and lag(r) over(partition by rid order by fid) >= r
                               ,r + 1, r) r
                        from (--b
                            select fid, rnm, rid,
                                    iif( lag(fid) over(partition by rid order by fid) is not null
                                          and lag(r) over(partition by rid order by fid) >= r
                                         ,r + 1, r) r
                            from (
                                    select fid, rnm, rid, max(r) over(partition by fid) r from c
                                  ) a
                            ) b
                      ) c
                  ) d
              ) e
          ) f
    )
    select * from d rows 0;
    set count off;
    select 'WORKER FINISHED TOO FAST! DELAY IN TEST MUST BE REDUCED!' msg from rdb$database;
    """)
    with open(heavy_output_1, mode='w') as heavy_out:
        p_heavy_sql = subprocess.Popen([act_1.vars['isql'], '-i', str(heavy_script_1),
                                       '-user', act_1.db.user,
                                       '-password', act_1.db.password, act_1.db.dsn],
                                       stdout=heavy_out, stderr=subprocess.STDOUT)
        try:
            time.sleep(4)
            act_1.expected_stdout = expected_stdout_1_killer
            act_1.isql(switches=[], input=killer_sql)
        finally:
            p_heavy_sql.terminate()
    #
    assert act_1.clean_stdout == act_1.clean_expected_stdout
    # And worker...
    act_1.reset()
    act_1.expected_stdout = expected_stdout_1_worker
    act_1.stdout = heavy_output_1.read_text()
    assert act_1.clean_stdout == act_1.clean_expected_stdout
