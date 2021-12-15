#coding:utf-8
#
# id:           bugs.core_6336
# title:        Regression in FB 4.x: error "Implementation of text subtype <NNNN> not located" on attempt to use some collations defined in fbintl.conf
# decription:
#                   Test uses list of character sets and collations defined in %FB_HOME%\\intl
#               bintl.conf.
#                   For each charset <W> we try following:
#                   1) alter database set default character set <W>;
#                   2) alter this <W> set default collation <W>;
#                   3) create unicode collation <U> for this <W> and alter <W> so that default collation is <U>;
#                   4) for each of other (non-unicode) collations <C> alter <W> with set default collation to <C>.
#                   Each of these actions is verified by creating several DB objects: domains, table, view and stored procedure.
#                   Every created DB object will use fields/parameters which refer to current charset and collation, i.e.:
#                   * create two domains of type VARCHAR; one of them will be later modified so that its default collation will be dropped;
#                   * create one domain of type BLOB; it can not be modified anyway because of implementation limits;
#                   * create table with two fields (varchar and blob) of these domains;
#                   * create view which refers to rdb$fields (this statement did FAIL and it was the reason of creation this ticket);
#                   * create stored proc with parameters of these domains.
#                   Finally, we do query to RDB$ tables in order to show data related to these domains.
#
#                   Following is what occurs for iso8859_1 (and similarly for all other charsets):
#                   ========
#                       alter database set default character set iso8859_1
#                       alter character set iso8859_1 set default collation iso8859_1
#                       create collation co_non_unc for iso8859_1 from iso8859_1 PAD SPACE
#                       create domain dm_text varchar(50) character set iso8859_1 collate co_non_unc
#                       create domain dm_name varchar(50) character set iso8859_1 collate iso8859_1
#                       create domain dm_blob blob character set iso8859_1 collate iso8859_1
#                       ...
#                       -- here we check that 'collate co_non_unc' will be cuted off and default collation will be restored for this domain:
#                       alter domain dm_text type char(50) character set iso8859_1
#                       <SHOW DATA FROM RDB$DATABASE FOR ALL THREE DOMAINS: DM_TEXT, DM_NAME and DM_BLOB>
#                       <DROP JUST CREATED OBJECTS>
#
#                       create collation ISO8859_1_UNICODE for iso8859_1
#                       alter character set iso8859_1 set default collation ISO8859_1_UNICODE
#                       create collation co_unicode for iso8859_1 from iso8859_1_unicode case insensitive accent insensitive 'NUMERIC-SORT=1'
#                       create domain dm_text varchar(50) character set iso8859_1 collate co_unicode
#                       create domain dm_name varchar(50) character set iso8859_1 collate co_unicode
#                       create domain dm_blob blob character set iso8859_1 collate co_unicode
#                       ...
#                       -- here we check that 'collate co_unicode' will be cuted off and default collation will be restored for this domain:
#                       alter domain dm_text type char(50) character set iso8859_1
#                       <SHOW DATA FROM RDB$DATABASE FOR ALL THREE DOMAINS: DM_TEXT, DM_NAME and DM_BLOB>
#                       <DROP JUST CREATED OBJECTS>
#
#
#                       alter character set iso8859_1 set default collation da_da
#                       create collation co_non_unc for iso8859_1 from da_da PAD SPACE
#                       create domain dm_text varchar(50) character set iso8859_1 collate co_non_unc
#                       create domain dm_name varchar(50) character set iso8859_1 collate da_da
#                       create domain dm_blob blob character set iso8859_1 collate da_da
#                       ...
#                       -- here we check that 'collate co_non_unc' will be cuted off and default collation will be restored for this domain:
#                       alter domain dm_text type char(50) character set iso8859_1
#                       <SHOW DATA FROM RDB$DATABASE FOR ALL THREE DOMAINS: DM_TEXT, DM_NAME and DM_BLOB>
#                       <DROP JUST CREATED OBJECTS>
#
#                       ... and so on for all other collations defined for charset ISO8859_1 ...
#                   ========
#
#                   Checked on 4.0.0.2114 SS. Time of execution: 73.668s.
#
# tracker_id:   CORE-6336
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('COLL-VERSION=\\d{2,}.\\d{2,}', 'COLL-VERSION=111.222')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
#
#  import os
#  import sys
#  import subprocess
#  from fdb import services
#
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
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
#      for f in f_names_list:
#         if type(f) == file:
#            del_name = f.name
#         elif type(f) == str:
#            del_name = f
#         else:
#            print('Unrecognized type of element:', f, ' - can not be treated as file.')
#            del_name = None
#
#         if del_name and os.path.isfile( del_name ):
#             os.remove( del_name )
#
#  #--------------------------------------------
#
#  runProgram('gfix',[dsn,'-w','async'])
#
#  sql_text='''
#      set list on;
#      --set bail on;
#      set blob all;
#      set width f_name 20;
#      set width cset_name 20;
#      set width coll_name 20;
#      set width cset_default_coll 20;
#      set width domain_coll_name 20;
#
#      --set echo on;
#      --shell del c:	emp	mp4test.fdb 2>nul;
#      connect '$(DSN)';
#      set autoddl off;
#      SET KEEP_TRAN_PARAMS ON;
#
#      --create database '$(DSN)';
#
#      commit;
#      set transaction READ COMMITTED NO RECORD_VERSION NO WAIT;
#
#      set term ^;
#      create procedure sp_cleanup as
#      begin
#          begin
#              execute statement 'drop procedure sp_info';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop table t_info';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop view v_info';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop domain dm_name';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop domain dm_text';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop domain dm_blob';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop collation co_unicode';
#              when any do begin end
#          end
#
#          begin
#              execute statement 'drop collation co_non_unc';
#              when any do begin end
#          end
#      end
#      ^
#
#      create procedure sp_add_objects ( a_cset varchar(50), a_coll varchar(50) ) as
#      begin
#
#      	/*
#      	create collation win1252_unicode_ci for win1252 from win1252_unicode case insensitive;
#      	*/
#          -- NB: COLLATE clause can be used only in CREATE domain statement. ALTER domain does not allow this.
#      	if ( right(upper(a_coll),8) = upper('_UNICODE') ) then
#          	begin
#          	    execute statement 'create collation co_unicode for ' || a_cset || ' from ' || a_coll || q'{ case insensitive accent insensitive 'NUMERIC-SORT=1'}';
#                  execute statement 'create domain dm_text varchar(50) character set ' || a_cset || ' collate co_unicode';
#                  execute statement 'create domain dm_name varchar(50) character set ' || a_cset || ' collate co_unicode';
#                  execute statement 'create domain dm_blob blob character set ' || a_cset || ' collate co_unicode';
#          	end
#      	else
#      	    begin
#          	    -- CREATE COLLATION PT_PT2     FOR ISO8859_1 FROM PT_PT     'SPECIALS-FIRST=1';
#          	    -- create collation co_non_unc for SJIS_0208 from SJIS_0208 'SPECIALS-FIRST=1'; ==> invalid collation attr; the same for DISABLE-COMPRESSIONS=1
#          	    execute statement 'create collation co_non_unc for ' || a_cset || ' from ' || a_coll || ' PAD SPACE';
#                  execute statement 'create domain dm_text varchar(50) character set ' || a_cset || ' collate co_non_unc';
#                  execute statement 'create domain dm_name varchar(50) character set ' || a_cset || ' collate ' || a_coll;
#                  execute statement 'create domain dm_blob blob character set ' || a_cset || ' collate ' || a_coll ;
#              end
#
#          execute statement q'{recreate view v_name as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_name')}';
#
#          execute statement q'{recreate view v_blob as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_blob')}';
#
#          execute statement 'recreate table t_info(f_name dm_name, f_blob dm_blob)';
#
#          execute statement q'{create procedure sp_info(a_name dm_name, a_blob dm_blob) returns(o_name dm_name, o_blob dm_blob) as begin suspend; end }';
#
#          execute statement
#              q'{recreate view v_info as
#              select
#                  cast(f.rdb$field_name as varchar(20)) as f_name
#                  ,f.rdb$character_set_id as cset_id
#                  ,f.rdb$collation_id as coll_id
#                  ,cast(c.rdb$character_set_name as varchar(20)) as cset_name
#                  ,cast(c.rdb$default_collate_name as varchar(20)) as cset_default_coll
#                  ,cast(k.rdb$collation_name as varchar(20)) as domain_coll_name
#                  ,k.rdb$collation_attributes as coll_attr
#                  ,cast(k.rdb$specific_attributes as varchar(8190)) as coll_spec
#              from rdb$fields f
#              left join rdb$character_sets c on f.rdb$character_set_id = c.rdb$character_set_id
#              left join rdb$collations k on c.rdb$character_set_id = k.rdb$character_set_id and f.rdb$collation_id = k.rdb$collation_id
#              where f.rdb$field_name in ( upper('dm_text'), upper('dm_name'), upper('dm_blob') )
#              order by f_name
#              }'
#          ;
#
#
#          -- Here we try to REMOVE collation attribute from domain:
#          execute statement 'alter domain dm_text type char(50) character set ' || a_cset ;
#
#          -- dm_blob: "Cannot change datatype ... Changing datatype is not supported for BLOB or ARRAY columns."
#          -- NB: this is so even when a new type is the same as old: BLOB.
#          -- execute statement 'alter domain dm_blob type blob character set ' || a_cset ;
#
#      end
#      ^
#      set term ;^
#      commit;
#
#      --################################   S J I S _ 0 2 0 8  #############################
#
#      alter database set default character set SJIS_0208 ;
#
#
#      alter character set SJIS_0208 set default collation SJIS_0208;
#      commit;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('SJIS_0208', 'SJIS_0208');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation sjis_0208_unicode for sjis_0208;
#      alter character set SJIS_0208 set default collation SJIS_0208_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('SJIS_0208', 'SJIS_0208_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   E U C J _ 0 2 0 8  #############################
#
#      alter database set default character set EUCJ_0208;
#      alter character set EUCJ_0208 set default collation EUCJ_0208;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('EUCJ_0208', 'EUCJ_0208');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      create collation EUCJ_0208_UNICODE for EUCJ_0208;
#      alter character set EUCJ_0208 set default collation EUCJ_0208_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('EUCJ_0208', 'EUCJ_0208_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  4 3 7  #############################
#
#      alter database set default character set DOS437;
#
#      alter character set DOS437 set default collation DOS437;
#      create collation DOS437_UNICODE for DOS437;
#      alter character set DOS437 set default collation DOS437_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DOS437_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_DEU437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_DEU437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_ESP437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_ESP437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_FIN437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_FIN437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_FRA437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_FRA437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_ITA437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_ITA437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_NLD437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_NLD437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_SVE437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_SVE437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_UK437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_UK437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation DB_US437;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'DB_US437');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation PDOX_ASCII;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'PDOX_ASCII');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation PDOX_INTL;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'PDOX_INTL');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set DOS437 set default collation PDOX_SWEDFIN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS437', 'PDOX_SWEDFIN');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 5 0  #############################
#
#      alter database set default character set dos850;
#
#      alter character set dos850 set default collation dos850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DOS850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS850_UNICODE for DOS850;
#      alter character set dos850 set default collation DOS850_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DOS850_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_DEU850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_DEU850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_FRA850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_FRA850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_FRC850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_FRC850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_ITA850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_ITA850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_NLD850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_NLD850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_PTB850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_PTB850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_SVE850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_SVE850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_UK850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_UK850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos850 set default collation DB_US850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS850', 'DB_US850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 6 5  #############################
#
#      alter database set default character set dos865;
#
#      alter character set dos865 set default collation dos865;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS865', 'DOS865');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS865_UNICODE for DOS865;
#      alter character set dos865 set default collation DOS865_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS865', 'DOS865_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos865 set default collation DB_DAN865;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS865', 'DB_DAN865');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos865 set default collation DB_NOR865;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS865', 'DB_NOR865');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos865 set default collation PDOX_NORDAN4;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('DOS865', 'PDOX_NORDAN4');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 1  ###########################
#
#      alter database set default character set iso8859_1 ;
#
#      alter character set iso8859_1 set default collation iso8859_1;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'iso8859_1');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_1_UNICODE for iso8859_1;
#      alter character set iso8859_1 set default collation ISO8859_1_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'iso8859_1_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation da_da;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'da_da');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation de_de;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'de_de');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation du_nl;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'du_nl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation en_uk;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'en_uk');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation en_us;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'en_us');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation es_es;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'es_es');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation es_es_ci_ai;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'es_es_ci_ai');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation fi_fi;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'fi_fi');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation fr_ca;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'fr_ca');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation fr_fr;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'fr_fr');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation is_is;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'is_is');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation it_it;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'it_it');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation no_no;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'no_no');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation sv_sv;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'sv_sv');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation pt_br;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'pt_br');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_1 set default collation pt_pt;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('iso8859_1', 'pt_pt');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 2  ###########################
#
#      alter database set default character set ISO8859_2;
#
#      alter character set iso8859_2 set default collation ISO8859_2;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_2', 'ISO8859_2');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_2_UNICODE for iso8859_2;
#      alter character set iso8859_2 set default collation ISO8859_2_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_2', 'ISO8859_2_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_2 set default collation CS_CZ;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_2', 'CS_CZ');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_2 set default collation ISO_HUN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_2', 'ISO_HUN');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_2 set default collation ISO_PLK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_2', 'ISO_PLK');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 3  ###########################
#
#      alter database set default character set ISO8859_3;
#
#      alter character set iso8859_3 set default collation ISO8859_3;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_3', 'ISO8859_3');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_3_UNICODE for iso8859_3;
#      alter character set iso8859_3 set default collation ISO8859_3_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_3', 'ISO8859_3_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 4  ###########################
#
#      alter database set default character set ISO8859_4;
#
#      alter character set iso8859_4 set default collation ISO8859_4;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_4', 'ISO8859_4');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_4_UNICODE for iso8859_4;
#      alter character set iso8859_4 set default collation ISO8859_4_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_4', 'ISO8859_4_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 5  ###########################
#
#      alter database set default character set ISO8859_5;
#
#      alter character set iso8859_5 set default collation ISO8859_5;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_5', 'ISO8859_5');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_5_UNICODE for iso8859_5;
#      alter character set iso8859_5 set default collation ISO8859_5_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_5', 'ISO8859_5_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 6  ###########################
#
#      alter database set default character set ISO8859_6;
#
#      alter character set iso8859_6 set default collation ISO8859_6;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_6', 'ISO8859_6');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_6_UNICODE for iso8859_6;
#      alter character set iso8859_6 set default collation ISO8859_6_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_6', 'ISO8859_6_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 7  ###########################
#
#      alter database set default character set ISO8859_7;
#
#      alter character set iso8859_7 set default collation ISO8859_7;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_7', 'ISO8859_7');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_7_UNICODE for iso8859_7;
#      alter character set iso8859_7 set default collation ISO8859_7_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_7', 'ISO8859_7_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################  I S O 8 8 5 9 _ 8  ###########################
#
#      alter database set default character set ISO8859_8;
#
#      alter character set iso8859_8 set default collation ISO8859_8;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_8', 'ISO8859_8');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_8_UNICODE for iso8859_8;
#      alter character set iso8859_8 set default collation ISO8859_8_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_8', 'ISO8859_8_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --##############################  I S O 8 8 5 9 _ 9  ###########################
#
#      alter database set default character set ISO8859_9;
#
#      alter character set iso8859_9 set default collation ISO8859_9;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_9', 'ISO8859_9');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_9_UNICODE for iso8859_9;
#      alter character set iso8859_9 set default collation ISO8859_9_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_9', 'ISO8859_9_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --##############################  I S O 8 8 5 9 _ 1 3  ###########################
#
#      alter database set default character set ISO8859_13;
#
#      alter character set iso8859_13 set default collation ISO8859_13;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_13', 'ISO8859_13');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ISO8859_13_UNICODE for iso8859_13;
#      alter character set iso8859_13 set default collation ISO8859_13_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ISO8859_13', 'ISO8859_13_UNICODE');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set iso8859_13 set default collation LT_LT;
#      recreate view v_info as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_name');
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 5 2  #############################
#
#      alter database set default character set dos852;
#
#      alter character set dos852 set default collation dos852;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'dos852');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS852_UNICODE for DOS852;
#      alter character set dos852 set default collation DOS852_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'dos852_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation DB_CSY;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'DB_CSY');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation DB_PLK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'DB_PLK');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation DB_SLO;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'DB_SLO');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation PDOX_CSY;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'PDOX_CSY');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation PDOX_HUN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'PDOX_HUN');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation PDOX_PLK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'PDOX_PLK');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos852 set default collation PDOX_SLO;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos852', 'PDOX_SLO');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 5 7  #############################
#
#      alter database set default character set dos857;
#
#      alter character set dos857 set default collation dos857;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos857', 'dos857');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS857_UNICODE for dos857;
#      alter character set dos857 set default collation DOS857_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos857', 'dos857_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos857 set default collation DB_TRK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos857', 'db_trk');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 6 0  #############################
#
#      alter database set default character set dos860;
#
#      alter character set dos860 set default collation dos860;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos860', 'dos860');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS860_UNICODE for dos860;
#      alter character set dos860 set default collation DOS860_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos860', 'dos860_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos860 set default collation DB_PTG860;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos860', 'DB_PTG860');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 6 1  #############################
#
#      alter database set default character set dos861;
#
#      alter character set dos861 set default collation dos861;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos861', 'dos861');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS861_UNICODE for dos861;
#      alter character set dos861 set default collation DOS861_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos861', 'dos861_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos861 set default collation PDOX_ISL;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos861', 'pdox_isl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 6 3  #############################
#
#      alter database set default character set dos863;
#
#      alter character set dos863 set default collation dos863;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos863', 'dos863');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS863_UNICODE for dos863;
#      alter character set dos863 set default collation DOS863_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos863', 'dos863_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set dos863 set default collation DB_FRC863;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos863', 'db_frc863');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   C Y R L  #############################
#
#      alter database set default character set cyrl;
#
#      alter character set cyrl set default collation cyrl;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cyrl', 'cyrl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation cyrl_UNICODE for cyrl;
#      alter character set cyrl set default collation cyrl_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cyrl', 'cyrl_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set cyrl set default collation DB_RUS;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cyrl', 'db_rus');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set cyrl set default collation PDOX_CYRL;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cyrl', 'pdox_cyrl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  7 3 7  #############################
#
#      alter database set default character set dos737;
#
#      alter character set dos737 set default collation dos737;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos737', 'dos737');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS737_UNICODE for DOS737;
#      alter character set dos737 set default collation DOS737_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos737', 'dos737_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  7 7 5  #############################
#
#      alter database set default character set dos775;
#
#      alter character set dos775 set default collation dos775;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos775', 'dos775');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS775_UNICODE for DOS775;
#      alter character set dos775 set default collation DOS775_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos775', 'dos775_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   D O S  8 5 8  #############################
#
#      alter database set default character set dos858;
#
#      alter character set dos858 set default collation dos858;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos858', 'dos858');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS858_UNICODE for DOS858;
#      alter character set dos858 set default collation DOS858_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos858', 'dos858_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 6 2  #############################
#
#      alter database set default character set dos862;
#
#      alter character set dos862 set default collation dos862;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos862', 'dos862');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS862_UNICODE for DOS862;
#      alter character set dos862 set default collation DOS862_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos862', 'dos862_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 6 4  #############################
#
#      alter database set default character set dos864;
#
#      alter character set dos864 set default collation dos864;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos864', 'dos864');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS864_UNICODE for DOS864;
#      alter character set dos864 set default collation DOS864_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos864', 'dos864_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 6 6  #############################
#
#      alter database set default character set dos866;
#
#      alter character set dos866 set default collation dos866;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos866', 'dos866');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS866_UNICODE for DOS866;
#      alter character set dos866 set default collation DOS866_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos866', 'dos866_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --################################   D O S  8 6 9  #############################
#
#      alter database set default character set dos869;
#
#      alter character set dos869 set default collation dos869;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos869', 'dos869');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation DOS869_UNICODE for DOS869;
#      alter character set dos869 set default collation DOS869_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('dos869', 'dos869_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --###############################   W I N 1 2 5 0  #############################
#
#      alter database set default character set win1250;
#
#      alter character set win1250 set default collation win1250;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'win1250');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1250_UNICODE for win1250;
#      alter character set win1250 set default collation win1250_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'win1250_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation PXW_CSY;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'pxw_csy');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation PXW_HUN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'pxw_hun');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation PXW_HUNDC;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'pxw_hundc');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation PXW_PLK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'pxw_plk');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation PXW_SLOV;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'pxw_slov');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation BS_BA;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'bs_ba');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation WIN_CZ;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'win_cz');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1250 set default collation WIN_CZ_CI_AI;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1250', 'WIN_CZ_CI_AI');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 1  #############################
#
#      alter database set default character set win1251;
#
#      alter character set win1251 set default collation win1251;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1251', 'win1251');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1251_UNICODE for win1251;
#      alter character set win1251 set default collation win1251_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1251', 'win1251_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1251 set default collation PXW_CYRL;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1251', 'pxw_cyrl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1251 set default collation WIN1251_UA;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1251', 'win1251_ua');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 2  #############################
#
#      alter database set default character set win1252;
#
#      alter character set win1252 set default collation win1252;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'win1252');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1252_UNICODE for win1252;
#      alter character set win1252 set default collation win1252_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'win1252_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation PXW_INTL;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'pxw_intl');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation PXW_INTL850;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'pxw_intl850');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation PXW_NORDAN4;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'pxw_nordan4');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation WIN_PTBR;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'win_ptbr');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation PXW_SPAN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'pxw_span');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1252 set default collation PXW_SWEDFIN;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1252', 'pxw_swedfin');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 3  #############################
#
#      alter database set default character set win1253;
#
#      alter character set win1253 set default collation win1253;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1253', 'win1253');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1253_UNICODE for win1253;
#      alter character set win1253 set default collation win1253_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1253', 'win1253_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1253 set default collation PXW_GREEK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1253', 'pxw_greek');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 4  #############################
#
#      alter database set default character set win1254;
#
#      alter character set win1254 set default collation win1254;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1254', 'win1254');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1254_UNICODE for win1254;
#      alter character set win1254 set default collation win1254_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1254', 'win1254_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1254 set default collation PXW_TURK;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1254', 'pxw_turk');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      --##################################   N E X T   ###############################
#
#      alter database set default character set next;
#
#      alter character set next set default collation next;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'next');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation NEXT_UNICODE for next;
#      alter character set next set default collation NEXT_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'next_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set next set default collation NXT_DEU;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'nxt_deu');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set next set default collation NXT_ESP;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'nxt_esp');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set next set default collation NXT_FRA;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'nxt_fra');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set next set default collation NXT_ITA;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'nxt_ita');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set next set default collation NXT_US;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('next', 'nxt_us');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 5  #############################
#
#      alter database set default character set win1255;
#
#      alter character set win1255 set default collation win1255;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1255', 'win1255');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1255_UNICODE for win1255;
#      alter character set win1255 set default collation win1255_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1255', 'win1255_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 6  #############################
#
#      alter database set default character set win1256;
#
#      alter character set win1256 set default collation win1256;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1256', 'win1256');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1256_UNICODE for win1256;
#      alter character set win1256 set default collation win1256_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1256', 'win1256_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 7  #############################
#
#      alter database set default character set win1257;
#
#      alter character set win1257 set default collation win1257;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1257', 'win1257');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1257_UNICODE for win1257;
#      alter character set win1257 set default collation win1257_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1257', 'win1257_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1257 set default collation WIN1257_EE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1257', 'win1257_ee');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1257 set default collation WIN1257_LT;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1257', 'win1257_lt');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set win1257 set default collation WIN1257_LV;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1257', 'win1257_lv');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##############################   K S C _ 5 6 0 1  #############################
#
#      alter database set default character set ksc_5601;
#
#      alter character set ksc_5601 set default collation ksc_5601;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ksc_5601', 'ksc_5601');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation ksc_5601_UNICODE for ksc_5601;
#      alter character set ksc_5601 set default collation ksc_5601_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ksc_5601', 'ksc_5601_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set ksc_5601 set default collation KSC_DICTIONARY;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('ksc_5601', 'KSC_DICTIONARY');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --#################################  B I G _ 5  ###############################
#
#      alter database set default character set big_5;
#
#      alter character set big_5 set default collation big_5;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('big_5', 'big_5');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation big_5_UNICODE for big_5;
#      alter character set big_5 set default collation big_5_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('big_5', 'big_5_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --#############################  G B _ 2 3 1 2  ###############################
#
#      alter database set default character set gb_2312;
#
#      alter character set gb_2312 set default collation gb_2312;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gb_2312', 'gb_2312');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation gb_2312_UNICODE for gb_2312;
#      alter character set gb_2312 set default collation gb_2312_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gb_2312', 'gb_2312_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --#############################  K O I 8 R   #################################
#
#      alter database set default character set koi8r;
#
#      alter character set koi8r set default collation koi8r;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8r', 'koi8r');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation koi8r_UNICODE for koi8r;
#      alter character set koi8r set default collation koi8r_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8r', 'koi8r_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set koi8r set default collation koi8r_ru;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8r', 'koi8r_ru');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --#############################  K O I 8 U   #################################
#
#      alter database set default character set koi8u;
#
#      alter character set koi8u set default collation koi8u;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8u', 'koi8u');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation koi8u_UNICODE for koi8u;
#      alter character set koi8u set default collation koi8u_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8u', 'koi8u_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      alter character set koi8u set default collation koi8u_ua;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('koi8u', 'koi8u_ua');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --###############################   W I N 1 2 5 8  #############################
#
#      alter database set default character set win1258;
#
#      alter character set win1258 set default collation win1258;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1258', 'win1258');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      create collation win1258_UNICODE for win1258;
#      alter character set win1258 set default collation win1258_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('win1258', 'win1258_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   T I S 6 2 0 ##############################
#
#      alter database set default character set tis620;
#
#      alter character set tis620 set default collation tis620;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('tis620', 'tis620');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      -- pre-registered as system collation, SKIP creation: create collation tis620_UNICODE for tis620;
#      alter character set tis620 set default collation tis620_UNICODE;
#      commit;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('tis620', 'tis620_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --##################################   G B K   ################################
#
#      alter database set default character set gbk;
#
#      alter character set gbk set default collation gbk;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gbk', 'gbk');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      -- pre-registered as system collation, SKIP creation: create collation gbk_UNICODE for gbk;
#      alter character set gbk set default collation gbk_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gbk', 'gbk_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   C 9 6 4 3 C ##############################
#
#      alter database set default character set cp943c;
#
#      alter character set cp943c set default collation cp943c;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cp943c', 'cp943c');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      -- pre-registered as system collation, SKIP creation: create collation cp943c_UNICODE for cp943c;
#      alter character set cp943c set default collation cp943c_UNICODE;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('cp943c', 'cp943c_unicode');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#
#      --################################   G B 1 8 0 3 0  ##############################
#
#      alter database set default character set gb18030;
#
#      alter character set gb18030 set default collation gb18030;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gb18030', 'gb18030');
#      commit;
#      select * from v_info;
#      commit;
#      connect '$(DSN)';
#
#      -- pre-registered as system collation, SKIP creation: create collation gb18030_UNICODE for gb18030;
#      alter character set gb18030 set default collation gb18030_UNICODE;
#      commit;
#      -- remove existing objects:
#      execute procedure sp_cleanup;
#      commit;
#      execute procedure sp_add_objects('gb18030', 'gb18030_unicode');
#      commit;
#      select * from v_info;
#      commit;
#  '''  % dict(globals(), **locals())
#
#  fb_home = services.connect(host='localhost', user= user_name, password= user_password).get_home_directory()
#
#  f_sql_cmd=open( os.path.join(context['temp_directory'],'tmp_6336.sql'), 'w')
#  f_sql_cmd.write(sql_text)
#  flush_and_close( f_sql_cmd )
#
#  f_sql_log=open( os.path.join(context['temp_directory'],'tmp_6336.log'), 'w')
#  f_sql_err=open( os.path.join(context['temp_directory'],'tmp_6336.err'), 'w')
#  subprocess.call( [ context['isql_path'] , "-q", "-i", f_sql_cmd.name ], stdout=f_sql_log, stderr=f_sql_err )
#  flush_and_close( f_sql_log )
#  flush_and_close( f_sql_err )
#
#  with open(f_sql_err.name, 'r') as f:
#      for line in f:
#          print('UNEXPECTED STDERR: ' + line)
#
#  with open(f_sql_log.name, 'r') as f:
#      for line in f:
#          print(line)
#
#
#  cleanup( ( f_sql_cmd, f_sql_log, f_sql_err ) )
#
#
#---

test_script_1 = """
    set list on;
    --set bail on;
    set blob all;
    set width f_name 20;
    set width cset_name 20;
    set width coll_name 20;
    set width cset_default_coll 20;
    set width domain_coll_name 20;

    --set echo on;
    --shell del c:	emp	mp4test.fdb 2>nul;
    connect '$(DSN)';
    set autoddl off;
    SET KEEP_TRAN_PARAMS ON;

    --create database '$(DSN)';

    commit;
    set transaction READ COMMITTED NO RECORD_VERSION NO WAIT;

    set term ^;
    create procedure sp_cleanup as
    begin
        begin
            execute statement 'drop procedure sp_info';
            when any do begin end
        end

        begin
            execute statement 'drop table t_info';
            when any do begin end
        end

        begin
            execute statement 'drop view v_info';
            when any do begin end
        end

        begin
            execute statement 'drop domain dm_name';
            when any do begin end
        end

        begin
            execute statement 'drop domain dm_text';
            when any do begin end
        end

        begin
            execute statement 'drop domain dm_blob';
            when any do begin end
        end

        begin
            execute statement 'drop collation co_unicode';
            when any do begin end
        end

        begin
            execute statement 'drop collation co_non_unc';
            when any do begin end
        end
    end
    ^

    create procedure sp_add_objects ( a_cset varchar(50), a_coll varchar(50) ) as
    begin

            /*
            create collation win1252_unicode_ci for win1252 from win1252_unicode case insensitive;
            */
        -- NB: COLLATE clause can be used only in CREATE domain statement. ALTER domain does not allow this.
            if ( right(upper(a_coll),8) = upper('_UNICODE') ) then
                begin
                    execute statement 'create collation co_unicode for ' || a_cset || ' from ' || a_coll || q'{ case insensitive accent insensitive 'NUMERIC-SORT=1'}';
                execute statement 'create domain dm_text varchar(50) character set ' || a_cset || ' collate co_unicode';
                execute statement 'create domain dm_name varchar(50) character set ' || a_cset || ' collate co_unicode';
                execute statement 'create domain dm_blob blob character set ' || a_cset || ' collate co_unicode';
                end
            else
                begin
                    -- CREATE COLLATION PT_PT2     FOR ISO8859_1 FROM PT_PT     'SPECIALS-FIRST=1';
                    -- create collation co_non_unc for SJIS_0208 from SJIS_0208 'SPECIALS-FIRST=1'; ==> invalid collation attr; the same for DISABLE-COMPRESSIONS=1
                    execute statement 'create collation co_non_unc for ' || a_cset || ' from ' || a_coll || ' PAD SPACE';
                execute statement 'create domain dm_text varchar(50) character set ' || a_cset || ' collate co_non_unc';
                execute statement 'create domain dm_name varchar(50) character set ' || a_cset || ' collate ' || a_coll;
                execute statement 'create domain dm_blob blob character set ' || a_cset || ' collate ' || a_coll ;
            end

        execute statement q'{recreate view v_name as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_name')}';

        execute statement q'{recreate view v_blob as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_blob')}';

        execute statement 'recreate table t_info(f_name dm_name, f_blob dm_blob)';

        execute statement q'{create procedure sp_info(a_name dm_name, a_blob dm_blob) returns(o_name dm_name, o_blob dm_blob) as begin suspend; end }';

        execute statement
            q'{recreate view v_info as
            select
                cast(f.rdb$field_name as varchar(20)) as f_name
                ,f.rdb$character_set_id as cset_id
                ,f.rdb$collation_id as coll_id
                ,cast(c.rdb$character_set_name as varchar(20)) as cset_name
                ,cast(c.rdb$default_collate_name as varchar(20)) as cset_default_coll
                ,cast(k.rdb$collation_name as varchar(20)) as domain_coll_name
                ,k.rdb$collation_attributes as coll_attr
                ,cast(k.rdb$specific_attributes as varchar(8190)) as coll_spec
            from rdb$fields f
            left join rdb$character_sets c on f.rdb$character_set_id = c.rdb$character_set_id
            left join rdb$collations k on c.rdb$character_set_id = k.rdb$character_set_id and f.rdb$collation_id = k.rdb$collation_id
            where f.rdb$field_name in ( upper('dm_text'), upper('dm_name'), upper('dm_blob') )
            order by f_name
            }'
        ;


        -- Here we try to REMOVE collation attribute from domain:
        execute statement 'alter domain dm_text type char(50) character set ' || a_cset ;

        -- dm_blob: "Cannot change datatype ... Changing datatype is not supported for BLOB or ARRAY columns."
        -- NB: this is so even when a new type is the same as old: BLOB.
        -- execute statement 'alter domain dm_blob type blob character set ' || a_cset ;

    end
    ^
    set term ;^
    commit;

    --################################   S J I S _ 0 2 0 8  #############################

    alter database set default character set SJIS_0208 ;


    alter character set SJIS_0208 set default collation SJIS_0208;
    commit;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('SJIS_0208', 'SJIS_0208');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation sjis_0208_unicode for sjis_0208;
    alter character set SJIS_0208 set default collation SJIS_0208_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('SJIS_0208', 'SJIS_0208_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   E U C J _ 0 2 0 8  #############################

    alter database set default character set EUCJ_0208;
    alter character set EUCJ_0208 set default collation EUCJ_0208;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('EUCJ_0208', 'EUCJ_0208');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    create collation EUCJ_0208_UNICODE for EUCJ_0208;
    alter character set EUCJ_0208 set default collation EUCJ_0208_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('EUCJ_0208', 'EUCJ_0208_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  4 3 7  #############################

    alter database set default character set DOS437;

    alter character set DOS437 set default collation DOS437;
    create collation DOS437_UNICODE for DOS437;
    alter character set DOS437 set default collation DOS437_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DOS437_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_DEU437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_DEU437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_ESP437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_ESP437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_FIN437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_FIN437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_FRA437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_FRA437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_ITA437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_ITA437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_NLD437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_NLD437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_SVE437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_SVE437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_UK437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_UK437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation DB_US437;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'DB_US437');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation PDOX_ASCII;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'PDOX_ASCII');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation PDOX_INTL;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'PDOX_INTL');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set DOS437 set default collation PDOX_SWEDFIN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS437', 'PDOX_SWEDFIN');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 5 0  #############################

    alter database set default character set dos850;

    alter character set dos850 set default collation dos850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DOS850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS850_UNICODE for DOS850;
    alter character set dos850 set default collation DOS850_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DOS850_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_DEU850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_DEU850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_FRA850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_FRA850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_FRC850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_FRC850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_ITA850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_ITA850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_NLD850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_NLD850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_PTB850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_PTB850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_SVE850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_SVE850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_UK850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_UK850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos850 set default collation DB_US850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS850', 'DB_US850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  8 6 5  #############################

    alter database set default character set dos865;

    alter character set dos865 set default collation dos865;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS865', 'DOS865');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS865_UNICODE for DOS865;
    alter character set dos865 set default collation DOS865_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS865', 'DOS865_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos865 set default collation DB_DAN865;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS865', 'DB_DAN865');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos865 set default collation DB_NOR865;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS865', 'DB_NOR865');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos865 set default collation PDOX_NORDAN4;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('DOS865', 'PDOX_NORDAN4');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 1  ###########################

    alter database set default character set iso8859_1 ;

    alter character set iso8859_1 set default collation iso8859_1;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'iso8859_1');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_1_UNICODE for iso8859_1;
    alter character set iso8859_1 set default collation ISO8859_1_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'iso8859_1_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation da_da;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'da_da');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation de_de;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'de_de');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation du_nl;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'du_nl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation en_uk;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'en_uk');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation en_us;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'en_us');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation es_es;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'es_es');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation es_es_ci_ai;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'es_es_ci_ai');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation fi_fi;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'fi_fi');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation fr_ca;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'fr_ca');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation fr_fr;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'fr_fr');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation is_is;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'is_is');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation it_it;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'it_it');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation no_no;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'no_no');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation sv_sv;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'sv_sv');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation pt_br;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'pt_br');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_1 set default collation pt_pt;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('iso8859_1', 'pt_pt');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 2  ###########################

    alter database set default character set ISO8859_2;

    alter character set iso8859_2 set default collation ISO8859_2;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_2', 'ISO8859_2');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_2_UNICODE for iso8859_2;
    alter character set iso8859_2 set default collation ISO8859_2_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_2', 'ISO8859_2_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_2 set default collation CS_CZ;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_2', 'CS_CZ');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_2 set default collation ISO_HUN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_2', 'ISO_HUN');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_2 set default collation ISO_PLK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_2', 'ISO_PLK');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 3  ###########################

    alter database set default character set ISO8859_3;

    alter character set iso8859_3 set default collation ISO8859_3;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_3', 'ISO8859_3');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_3_UNICODE for iso8859_3;
    alter character set iso8859_3 set default collation ISO8859_3_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_3', 'ISO8859_3_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 4  ###########################

    alter database set default character set ISO8859_4;

    alter character set iso8859_4 set default collation ISO8859_4;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_4', 'ISO8859_4');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_4_UNICODE for iso8859_4;
    alter character set iso8859_4 set default collation ISO8859_4_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_4', 'ISO8859_4_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 5  ###########################

    alter database set default character set ISO8859_5;

    alter character set iso8859_5 set default collation ISO8859_5;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_5', 'ISO8859_5');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_5_UNICODE for iso8859_5;
    alter character set iso8859_5 set default collation ISO8859_5_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_5', 'ISO8859_5_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 6  ###########################

    alter database set default character set ISO8859_6;

    alter character set iso8859_6 set default collation ISO8859_6;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_6', 'ISO8859_6');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_6_UNICODE for iso8859_6;
    alter character set iso8859_6 set default collation ISO8859_6_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_6', 'ISO8859_6_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 7  ###########################

    alter database set default character set ISO8859_7;

    alter character set iso8859_7 set default collation ISO8859_7;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_7', 'ISO8859_7');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_7_UNICODE for iso8859_7;
    alter character set iso8859_7 set default collation ISO8859_7_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_7', 'ISO8859_7_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################  I S O 8 8 5 9 _ 8  ###########################

    alter database set default character set ISO8859_8;

    alter character set iso8859_8 set default collation ISO8859_8;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_8', 'ISO8859_8');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_8_UNICODE for iso8859_8;
    alter character set iso8859_8 set default collation ISO8859_8_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_8', 'ISO8859_8_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --##############################  I S O 8 8 5 9 _ 9  ###########################

    alter database set default character set ISO8859_9;

    alter character set iso8859_9 set default collation ISO8859_9;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_9', 'ISO8859_9');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_9_UNICODE for iso8859_9;
    alter character set iso8859_9 set default collation ISO8859_9_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_9', 'ISO8859_9_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --##############################  I S O 8 8 5 9 _ 1 3  ###########################

    alter database set default character set ISO8859_13;

    alter character set iso8859_13 set default collation ISO8859_13;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_13', 'ISO8859_13');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ISO8859_13_UNICODE for iso8859_13;
    alter character set iso8859_13 set default collation ISO8859_13_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ISO8859_13', 'ISO8859_13_UNICODE');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set iso8859_13 set default collation LT_LT;
    recreate view v_info as select f.rdb$field_name as f_name from rdb$fields f where f.rdb$field_name = upper('dm_name');
    commit;
    connect '$(DSN)';


    --################################   D O S  8 5 2  #############################

    alter database set default character set dos852;

    alter character set dos852 set default collation dos852;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'dos852');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS852_UNICODE for DOS852;
    alter character set dos852 set default collation DOS852_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'dos852_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation DB_CSY;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'DB_CSY');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation DB_PLK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'DB_PLK');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation DB_SLO;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'DB_SLO');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation PDOX_CSY;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'PDOX_CSY');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation PDOX_HUN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'PDOX_HUN');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation PDOX_PLK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'PDOX_PLK');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos852 set default collation PDOX_SLO;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos852', 'PDOX_SLO');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 5 7  #############################

    alter database set default character set dos857;

    alter character set dos857 set default collation dos857;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos857', 'dos857');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS857_UNICODE for dos857;
    alter character set dos857 set default collation DOS857_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos857', 'dos857_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos857 set default collation DB_TRK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos857', 'db_trk');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  8 6 0  #############################

    alter database set default character set dos860;

    alter character set dos860 set default collation dos860;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos860', 'dos860');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS860_UNICODE for dos860;
    alter character set dos860 set default collation DOS860_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos860', 'dos860_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos860 set default collation DB_PTG860;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos860', 'DB_PTG860');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  8 6 1  #############################

    alter database set default character set dos861;

    alter character set dos861 set default collation dos861;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos861', 'dos861');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS861_UNICODE for dos861;
    alter character set dos861 set default collation DOS861_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos861', 'dos861_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos861 set default collation PDOX_ISL;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos861', 'pdox_isl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  8 6 3  #############################

    alter database set default character set dos863;

    alter character set dos863 set default collation dos863;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos863', 'dos863');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS863_UNICODE for dos863;
    alter character set dos863 set default collation DOS863_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos863', 'dos863_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set dos863 set default collation DB_FRC863;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos863', 'db_frc863');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   C Y R L  #############################

    alter database set default character set cyrl;

    alter character set cyrl set default collation cyrl;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cyrl', 'cyrl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation cyrl_UNICODE for cyrl;
    alter character set cyrl set default collation cyrl_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cyrl', 'cyrl_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set cyrl set default collation DB_RUS;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cyrl', 'db_rus');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set cyrl set default collation PDOX_CYRL;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cyrl', 'pdox_cyrl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  7 3 7  #############################

    alter database set default character set dos737;

    alter character set dos737 set default collation dos737;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos737', 'dos737');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS737_UNICODE for DOS737;
    alter character set dos737 set default collation DOS737_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos737', 'dos737_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  7 7 5  #############################

    alter database set default character set dos775;

    alter character set dos775 set default collation dos775;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos775', 'dos775');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS775_UNICODE for DOS775;
    alter character set dos775 set default collation DOS775_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos775', 'dos775_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   D O S  8 5 8  #############################

    alter database set default character set dos858;

    alter character set dos858 set default collation dos858;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos858', 'dos858');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS858_UNICODE for DOS858;
    alter character set dos858 set default collation DOS858_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos858', 'dos858_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 6 2  #############################

    alter database set default character set dos862;

    alter character set dos862 set default collation dos862;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos862', 'dos862');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS862_UNICODE for DOS862;
    alter character set dos862 set default collation DOS862_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos862', 'dos862_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 6 4  #############################

    alter database set default character set dos864;

    alter character set dos864 set default collation dos864;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos864', 'dos864');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS864_UNICODE for DOS864;
    alter character set dos864 set default collation DOS864_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos864', 'dos864_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 6 6  #############################

    alter database set default character set dos866;

    alter character set dos866 set default collation dos866;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos866', 'dos866');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS866_UNICODE for DOS866;
    alter character set dos866 set default collation DOS866_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos866', 'dos866_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --################################   D O S  8 6 9  #############################

    alter database set default character set dos869;

    alter character set dos869 set default collation dos869;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos869', 'dos869');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation DOS869_UNICODE for DOS869;
    alter character set dos869 set default collation DOS869_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('dos869', 'dos869_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --###############################   W I N 1 2 5 0  #############################

    alter database set default character set win1250;

    alter character set win1250 set default collation win1250;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'win1250');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1250_UNICODE for win1250;
    alter character set win1250 set default collation win1250_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'win1250_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation PXW_CSY;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'pxw_csy');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation PXW_HUN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'pxw_hun');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation PXW_HUNDC;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'pxw_hundc');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation PXW_PLK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'pxw_plk');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation PXW_SLOV;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'pxw_slov');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation BS_BA;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'bs_ba');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation WIN_CZ;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'win_cz');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1250 set default collation WIN_CZ_CI_AI;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1250', 'WIN_CZ_CI_AI');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 1  #############################

    alter database set default character set win1251;

    alter character set win1251 set default collation win1251;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1251', 'win1251');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1251_UNICODE for win1251;
    alter character set win1251 set default collation win1251_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1251', 'win1251_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1251 set default collation PXW_CYRL;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1251', 'pxw_cyrl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1251 set default collation WIN1251_UA;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1251', 'win1251_ua');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 2  #############################

    alter database set default character set win1252;

    alter character set win1252 set default collation win1252;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'win1252');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1252_UNICODE for win1252;
    alter character set win1252 set default collation win1252_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'win1252_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation PXW_INTL;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'pxw_intl');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation PXW_INTL850;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'pxw_intl850');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation PXW_NORDAN4;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'pxw_nordan4');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation WIN_PTBR;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'win_ptbr');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation PXW_SPAN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'pxw_span');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1252 set default collation PXW_SWEDFIN;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1252', 'pxw_swedfin');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 3  #############################

    alter database set default character set win1253;

    alter character set win1253 set default collation win1253;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1253', 'win1253');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1253_UNICODE for win1253;
    alter character set win1253 set default collation win1253_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1253', 'win1253_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1253 set default collation PXW_GREEK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1253', 'pxw_greek');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 4  #############################

    alter database set default character set win1254;

    alter character set win1254 set default collation win1254;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1254', 'win1254');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1254_UNICODE for win1254;
    alter character set win1254 set default collation win1254_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1254', 'win1254_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1254 set default collation PXW_TURK;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1254', 'pxw_turk');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    --##################################   N E X T   ###############################

    alter database set default character set next;

    alter character set next set default collation next;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'next');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation NEXT_UNICODE for next;
    alter character set next set default collation NEXT_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'next_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set next set default collation NXT_DEU;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'nxt_deu');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set next set default collation NXT_ESP;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'nxt_esp');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set next set default collation NXT_FRA;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'nxt_fra');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set next set default collation NXT_ITA;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'nxt_ita');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set next set default collation NXT_US;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('next', 'nxt_us');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 5  #############################

    alter database set default character set win1255;

    alter character set win1255 set default collation win1255;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1255', 'win1255');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1255_UNICODE for win1255;
    alter character set win1255 set default collation win1255_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1255', 'win1255_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 6  #############################

    alter database set default character set win1256;

    alter character set win1256 set default collation win1256;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1256', 'win1256');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1256_UNICODE for win1256;
    alter character set win1256 set default collation win1256_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1256', 'win1256_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 7  #############################

    alter database set default character set win1257;

    alter character set win1257 set default collation win1257;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1257', 'win1257');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1257_UNICODE for win1257;
    alter character set win1257 set default collation win1257_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1257', 'win1257_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1257 set default collation WIN1257_EE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1257', 'win1257_ee');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1257 set default collation WIN1257_LT;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1257', 'win1257_lt');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set win1257 set default collation WIN1257_LV;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1257', 'win1257_lv');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##############################   K S C _ 5 6 0 1  #############################

    alter database set default character set ksc_5601;

    alter character set ksc_5601 set default collation ksc_5601;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ksc_5601', 'ksc_5601');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation ksc_5601_UNICODE for ksc_5601;
    alter character set ksc_5601 set default collation ksc_5601_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ksc_5601', 'ksc_5601_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set ksc_5601 set default collation KSC_DICTIONARY;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('ksc_5601', 'KSC_DICTIONARY');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --#################################  B I G _ 5  ###############################

    alter database set default character set big_5;

    alter character set big_5 set default collation big_5;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('big_5', 'big_5');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation big_5_UNICODE for big_5;
    alter character set big_5 set default collation big_5_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('big_5', 'big_5_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --#############################  G B _ 2 3 1 2  ###############################

    alter database set default character set gb_2312;

    alter character set gb_2312 set default collation gb_2312;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gb_2312', 'gb_2312');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation gb_2312_UNICODE for gb_2312;
    alter character set gb_2312 set default collation gb_2312_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gb_2312', 'gb_2312_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --#############################  K O I 8 R   #################################

    alter database set default character set koi8r;

    alter character set koi8r set default collation koi8r;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8r', 'koi8r');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation koi8r_UNICODE for koi8r;
    alter character set koi8r set default collation koi8r_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8r', 'koi8r_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set koi8r set default collation koi8r_ru;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8r', 'koi8r_ru');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --#############################  K O I 8 U   #################################

    alter database set default character set koi8u;

    alter character set koi8u set default collation koi8u;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8u', 'koi8u');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation koi8u_UNICODE for koi8u;
    alter character set koi8u set default collation koi8u_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8u', 'koi8u_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    alter character set koi8u set default collation koi8u_ua;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('koi8u', 'koi8u_ua');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --###############################   W I N 1 2 5 8  #############################

    alter database set default character set win1258;

    alter character set win1258 set default collation win1258;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1258', 'win1258');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    create collation win1258_UNICODE for win1258;
    alter character set win1258 set default collation win1258_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('win1258', 'win1258_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   T I S 6 2 0 ##############################

    alter database set default character set tis620;

    alter character set tis620 set default collation tis620;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('tis620', 'tis620');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    -- pre-registered as system collation, SKIP creation: create collation tis620_UNICODE for tis620;
    alter character set tis620 set default collation tis620_UNICODE;
    commit;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('tis620', 'tis620_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --##################################   G B K   ################################

    alter database set default character set gbk;

    alter character set gbk set default collation gbk;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gbk', 'gbk');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    -- pre-registered as system collation, SKIP creation: create collation gbk_UNICODE for gbk;
    alter character set gbk set default collation gbk_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gbk', 'gbk_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   C 9 6 4 3 C ##############################

    alter database set default character set cp943c;

    alter character set cp943c set default collation cp943c;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cp943c', 'cp943c');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    -- pre-registered as system collation, SKIP creation: create collation cp943c_UNICODE for cp943c;
    alter character set cp943c set default collation cp943c_UNICODE;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('cp943c', 'cp943c_unicode');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';


    --################################   G B 1 8 0 3 0  ##############################

    alter database set default character set gb18030;

    alter character set gb18030 set default collation gb18030;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gb18030', 'gb18030');
    commit;
    select * from v_info;
    commit;
    connect '$(DSN)';

    -- pre-registered as system collation, SKIP creation: create collation gb18030_UNICODE for gb18030;
    alter character set gb18030 set default collation gb18030_UNICODE;
    commit;
    -- remove existing objects:
    execute procedure sp_cleanup;
    commit;
    execute procedure sp_add_objects('gb18030', 'gb18030_unicode');
    commit;
    select * from v_info;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    F_NAME                          DM_BLOB
    CSET_ID                         5
    COLL_ID                         0
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208
    DOMAIN_COLL_NAME                SJIS_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         5
    COLL_ID                         0
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208
    DOMAIN_COLL_NAME                SJIS_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         5
    COLL_ID                         0
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208
    DOMAIN_COLL_NAME                SJIS_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         5
    COLL_ID                         126
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         5
    COLL_ID                         126
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         5
    COLL_ID                         125
    CSET_NAME                       SJIS_0208
    CSET_DEFAULT_COLL               SJIS_0208_UNICODE
    DOMAIN_COLL_NAME                SJIS_0208_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         6
    COLL_ID                         0
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208
    DOMAIN_COLL_NAME                EUCJ_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         6
    COLL_ID                         0
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208
    DOMAIN_COLL_NAME                EUCJ_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         6
    COLL_ID                         0
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208
    DOMAIN_COLL_NAME                EUCJ_0208
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         6
    COLL_ID                         126
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         6
    COLL_ID                         126
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         6
    COLL_ID                         125
    CSET_NAME                       EUCJ_0208
    CSET_DEFAULT_COLL               EUCJ_0208_UNICODE
    DOMAIN_COLL_NAME                EUCJ_0208_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         125
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DOS437_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         125
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DOS437_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         126
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DOS437_UNICODE
    DOMAIN_COLL_NAME                DOS437_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         4
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_DEU437
    DOMAIN_COLL_NAME                DB_DEU437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         4
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_DEU437
    DOMAIN_COLL_NAME                DB_DEU437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         4
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_DEU437
    DOMAIN_COLL_NAME                DB_DEU437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         5
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ESP437
    DOMAIN_COLL_NAME                DB_ESP437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         5
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ESP437
    DOMAIN_COLL_NAME                DB_ESP437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         5
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ESP437
    DOMAIN_COLL_NAME                DB_ESP437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         6
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FIN437
    DOMAIN_COLL_NAME                DB_FIN437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         6
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FIN437
    DOMAIN_COLL_NAME                DB_FIN437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         6
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FIN437
    DOMAIN_COLL_NAME                DB_FIN437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         7
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FRA437
    DOMAIN_COLL_NAME                DB_FRA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         7
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FRA437
    DOMAIN_COLL_NAME                DB_FRA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         7
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_FRA437
    DOMAIN_COLL_NAME                DB_FRA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         8
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ITA437
    DOMAIN_COLL_NAME                DB_ITA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         8
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ITA437
    DOMAIN_COLL_NAME                DB_ITA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         8
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_ITA437
    DOMAIN_COLL_NAME                DB_ITA437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         9
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_NLD437
    DOMAIN_COLL_NAME                DB_NLD437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         9
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_NLD437
    DOMAIN_COLL_NAME                DB_NLD437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         9
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_NLD437
    DOMAIN_COLL_NAME                DB_NLD437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         10
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_SVE437
    DOMAIN_COLL_NAME                DB_SVE437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         10
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_SVE437
    DOMAIN_COLL_NAME                DB_SVE437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         10
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_SVE437
    DOMAIN_COLL_NAME                DB_SVE437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         11
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_UK437
    DOMAIN_COLL_NAME                DB_UK437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         11
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_UK437
    DOMAIN_COLL_NAME                DB_UK437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         11
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_UK437
    DOMAIN_COLL_NAME                DB_UK437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         12
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_US437
    DOMAIN_COLL_NAME                DB_US437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         12
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_US437
    DOMAIN_COLL_NAME                DB_US437
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         12
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               DB_US437
    DOMAIN_COLL_NAME                DB_US437
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         1
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_ASCII
    DOMAIN_COLL_NAME                PDOX_ASCII
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         1
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_ASCII
    DOMAIN_COLL_NAME                PDOX_ASCII
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         1
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_ASCII
    DOMAIN_COLL_NAME                PDOX_ASCII
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         2
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_INTL
    DOMAIN_COLL_NAME                PDOX_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         2
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_INTL
    DOMAIN_COLL_NAME                PDOX_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         2
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_INTL
    DOMAIN_COLL_NAME                PDOX_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         10
    COLL_ID                         3
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_SWEDFIN
    DOMAIN_COLL_NAME                PDOX_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         10
    COLL_ID                         3
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_SWEDFIN
    DOMAIN_COLL_NAME                PDOX_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         10
    COLL_ID                         3
    CSET_NAME                       DOS437
    CSET_DEFAULT_COLL               PDOX_SWEDFIN
    DOMAIN_COLL_NAME                PDOX_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         0
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850
    DOMAIN_COLL_NAME                DOS850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         0
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850
    DOMAIN_COLL_NAME                DOS850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         0
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850
    DOMAIN_COLL_NAME                DOS850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         126
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         126
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         125
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DOS850_UNICODE
    DOMAIN_COLL_NAME                DOS850_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         2
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_DEU850
    DOMAIN_COLL_NAME                DB_DEU850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         2
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_DEU850
    DOMAIN_COLL_NAME                DB_DEU850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         2
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_DEU850
    DOMAIN_COLL_NAME                DB_DEU850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         4
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRA850
    DOMAIN_COLL_NAME                DB_FRA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         4
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRA850
    DOMAIN_COLL_NAME                DB_FRA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         4
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRA850
    DOMAIN_COLL_NAME                DB_FRA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         1
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRC850
    DOMAIN_COLL_NAME                DB_FRC850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         1
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRC850
    DOMAIN_COLL_NAME                DB_FRC850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         1
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_FRC850
    DOMAIN_COLL_NAME                DB_FRC850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         5
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_ITA850
    DOMAIN_COLL_NAME                DB_ITA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         5
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_ITA850
    DOMAIN_COLL_NAME                DB_ITA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         5
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_ITA850
    DOMAIN_COLL_NAME                DB_ITA850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         6
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_NLD850
    DOMAIN_COLL_NAME                DB_NLD850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         6
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_NLD850
    DOMAIN_COLL_NAME                DB_NLD850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         6
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_NLD850
    DOMAIN_COLL_NAME                DB_NLD850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         7
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_PTB850
    DOMAIN_COLL_NAME                DB_PTB850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         7
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_PTB850
    DOMAIN_COLL_NAME                DB_PTB850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         7
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_PTB850
    DOMAIN_COLL_NAME                DB_PTB850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         8
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_SVE850
    DOMAIN_COLL_NAME                DB_SVE850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         8
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_SVE850
    DOMAIN_COLL_NAME                DB_SVE850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         8
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_SVE850
    DOMAIN_COLL_NAME                DB_SVE850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         9
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_UK850
    DOMAIN_COLL_NAME                DB_UK850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         9
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_UK850
    DOMAIN_COLL_NAME                DB_UK850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         9
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_UK850
    DOMAIN_COLL_NAME                DB_UK850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         11
    COLL_ID                         10
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_US850
    DOMAIN_COLL_NAME                DB_US850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         11
    COLL_ID                         10
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_US850
    DOMAIN_COLL_NAME                DB_US850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         11
    COLL_ID                         10
    CSET_NAME                       DOS850
    CSET_DEFAULT_COLL               DB_US850
    DOMAIN_COLL_NAME                DB_US850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         12
    COLL_ID                         0
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865
    DOMAIN_COLL_NAME                DOS865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         12
    COLL_ID                         0
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865
    DOMAIN_COLL_NAME                DOS865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         12
    COLL_ID                         0
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865
    DOMAIN_COLL_NAME                DOS865
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         12
    COLL_ID                         126
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         12
    COLL_ID                         126
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         12
    COLL_ID                         125
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DOS865_UNICODE
    DOMAIN_COLL_NAME                DOS865_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         12
    COLL_ID                         2
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_DAN865
    DOMAIN_COLL_NAME                DB_DAN865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         12
    COLL_ID                         2
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_DAN865
    DOMAIN_COLL_NAME                DB_DAN865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         12
    COLL_ID                         2
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_DAN865
    DOMAIN_COLL_NAME                DB_DAN865
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         12
    COLL_ID                         3
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_NOR865
    DOMAIN_COLL_NAME                DB_NOR865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         12
    COLL_ID                         3
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_NOR865
    DOMAIN_COLL_NAME                DB_NOR865
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         12
    COLL_ID                         3
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               DB_NOR865
    DOMAIN_COLL_NAME                DB_NOR865
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         12
    COLL_ID                         1
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               PDOX_NORDAN4
    DOMAIN_COLL_NAME                PDOX_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         12
    COLL_ID                         1
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               PDOX_NORDAN4
    DOMAIN_COLL_NAME                PDOX_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         12
    COLL_ID                         1
    CSET_NAME                       DOS865
    CSET_DEFAULT_COLL               PDOX_NORDAN4
    DOMAIN_COLL_NAME                PDOX_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         0
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1
    DOMAIN_COLL_NAME                ISO8859_1
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         0
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1
    DOMAIN_COLL_NAME                ISO8859_1
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         0
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1
    DOMAIN_COLL_NAME                ISO8859_1
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         126
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         126
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         125
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ISO8859_1_UNICODE
    DOMAIN_COLL_NAME                ISO8859_1_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         1
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DA_DA
    DOMAIN_COLL_NAME                DA_DA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         1
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DA_DA
    DOMAIN_COLL_NAME                DA_DA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         1
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DA_DA
    DOMAIN_COLL_NAME                DA_DA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         6
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DE_DE
    DOMAIN_COLL_NAME                DE_DE
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         6
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DE_DE
    DOMAIN_COLL_NAME                DE_DE
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         6
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DE_DE
    DOMAIN_COLL_NAME                DE_DE
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         2
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DU_NL
    DOMAIN_COLL_NAME                DU_NL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         2
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DU_NL
    DOMAIN_COLL_NAME                DU_NL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         2
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               DU_NL
    DOMAIN_COLL_NAME                DU_NL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         12
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_UK
    DOMAIN_COLL_NAME                EN_UK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         12
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_UK
    DOMAIN_COLL_NAME                EN_UK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         12
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_UK
    DOMAIN_COLL_NAME                EN_UK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         14
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_US
    DOMAIN_COLL_NAME                EN_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         14
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_US
    DOMAIN_COLL_NAME                EN_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         14
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               EN_US
    DOMAIN_COLL_NAME                EN_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         10
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES
    DOMAIN_COLL_NAME                ES_ES
    COLL_ATTR                       1
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         10
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES
    DOMAIN_COLL_NAME                ES_ES
    COLL_ATTR                       1
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         10
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES
    DOMAIN_COLL_NAME                ES_ES
    COLL_ATTR                       1
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         17
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES_CI_AI
    DOMAIN_COLL_NAME                ES_ES_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         17
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES_CI_AI
    DOMAIN_COLL_NAME                ES_ES_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         17
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               ES_ES_CI_AI
    DOMAIN_COLL_NAME                ES_ES_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       DISABLE-COMPRESSIONS=1;SPECIALS-FIRST=1



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         3
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FI_FI
    DOMAIN_COLL_NAME                FI_FI
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         3
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FI_FI
    DOMAIN_COLL_NAME                FI_FI
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         3
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FI_FI
    DOMAIN_COLL_NAME                FI_FI
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         5
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_CA
    DOMAIN_COLL_NAME                FR_CA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         5
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_CA
    DOMAIN_COLL_NAME                FR_CA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         5
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_CA
    DOMAIN_COLL_NAME                FR_CA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         4
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_FR
    DOMAIN_COLL_NAME                FR_FR
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         4
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_FR
    DOMAIN_COLL_NAME                FR_FR
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         4
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               FR_FR
    DOMAIN_COLL_NAME                FR_FR
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         7
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IS_IS
    DOMAIN_COLL_NAME                IS_IS
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         7
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IS_IS
    DOMAIN_COLL_NAME                IS_IS
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         7
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IS_IS
    DOMAIN_COLL_NAME                IS_IS
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         8
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IT_IT
    DOMAIN_COLL_NAME                IT_IT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         8
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IT_IT
    DOMAIN_COLL_NAME                IT_IT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         8
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               IT_IT
    DOMAIN_COLL_NAME                IT_IT
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         9
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               NO_NO
    DOMAIN_COLL_NAME                NO_NO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         9
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               NO_NO
    DOMAIN_COLL_NAME                NO_NO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         9
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               NO_NO
    DOMAIN_COLL_NAME                NO_NO
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         11
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               SV_SV
    DOMAIN_COLL_NAME                SV_SV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         11
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               SV_SV
    DOMAIN_COLL_NAME                SV_SV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         11
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               SV_SV
    DOMAIN_COLL_NAME                SV_SV
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         16
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_BR
    DOMAIN_COLL_NAME                PT_BR
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         16
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_BR
    DOMAIN_COLL_NAME                PT_BR
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         16
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_BR
    DOMAIN_COLL_NAME                PT_BR
    COLL_ATTR                       7
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         21
    COLL_ID                         15
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_PT
    DOMAIN_COLL_NAME                PT_PT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         21
    COLL_ID                         15
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_PT
    DOMAIN_COLL_NAME                PT_PT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         21
    COLL_ID                         15
    CSET_NAME                       ISO8859_1
    CSET_DEFAULT_COLL               PT_PT
    DOMAIN_COLL_NAME                PT_PT
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         22
    COLL_ID                         0
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2
    DOMAIN_COLL_NAME                ISO8859_2
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         22
    COLL_ID                         0
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2
    DOMAIN_COLL_NAME                ISO8859_2
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         22
    COLL_ID                         0
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2
    DOMAIN_COLL_NAME                ISO8859_2
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         22
    COLL_ID                         126
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         22
    COLL_ID                         126
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         22
    COLL_ID                         125
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO8859_2_UNICODE
    DOMAIN_COLL_NAME                ISO8859_2_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         22
    COLL_ID                         1
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               CS_CZ
    DOMAIN_COLL_NAME                CS_CZ
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         22
    COLL_ID                         1
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               CS_CZ
    DOMAIN_COLL_NAME                CS_CZ
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         22
    COLL_ID                         1
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               CS_CZ
    DOMAIN_COLL_NAME                CS_CZ
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         22
    COLL_ID                         2
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_HUN
    DOMAIN_COLL_NAME                ISO_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         22
    COLL_ID                         2
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_HUN
    DOMAIN_COLL_NAME                ISO_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         22
    COLL_ID                         2
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_HUN
    DOMAIN_COLL_NAME                ISO_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         22
    COLL_ID                         3
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_PLK
    DOMAIN_COLL_NAME                ISO_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         22
    COLL_ID                         3
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_PLK
    DOMAIN_COLL_NAME                ISO_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         22
    COLL_ID                         3
    CSET_NAME                       ISO8859_2
    CSET_DEFAULT_COLL               ISO_PLK
    DOMAIN_COLL_NAME                ISO_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         23
    COLL_ID                         0
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3
    DOMAIN_COLL_NAME                ISO8859_3
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         23
    COLL_ID                         0
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3
    DOMAIN_COLL_NAME                ISO8859_3
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         23
    COLL_ID                         0
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3
    DOMAIN_COLL_NAME                ISO8859_3
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         23
    COLL_ID                         126
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         23
    COLL_ID                         126
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         23
    COLL_ID                         125
    CSET_NAME                       ISO8859_3
    CSET_DEFAULT_COLL               ISO8859_3_UNICODE
    DOMAIN_COLL_NAME                ISO8859_3_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         34
    COLL_ID                         0
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4
    DOMAIN_COLL_NAME                ISO8859_4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         34
    COLL_ID                         0
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4
    DOMAIN_COLL_NAME                ISO8859_4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         34
    COLL_ID                         0
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4
    DOMAIN_COLL_NAME                ISO8859_4
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         34
    COLL_ID                         126
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         34
    COLL_ID                         126
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         34
    COLL_ID                         125
    CSET_NAME                       ISO8859_4
    CSET_DEFAULT_COLL               ISO8859_4_UNICODE
    DOMAIN_COLL_NAME                ISO8859_4_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         35
    COLL_ID                         0
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5
    DOMAIN_COLL_NAME                ISO8859_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         35
    COLL_ID                         0
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5
    DOMAIN_COLL_NAME                ISO8859_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         35
    COLL_ID                         0
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5
    DOMAIN_COLL_NAME                ISO8859_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         35
    COLL_ID                         126
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         35
    COLL_ID                         126
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         35
    COLL_ID                         125
    CSET_NAME                       ISO8859_5
    CSET_DEFAULT_COLL               ISO8859_5_UNICODE
    DOMAIN_COLL_NAME                ISO8859_5_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         36
    COLL_ID                         0
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6
    DOMAIN_COLL_NAME                ISO8859_6
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         36
    COLL_ID                         0
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6
    DOMAIN_COLL_NAME                ISO8859_6
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         36
    COLL_ID                         0
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6
    DOMAIN_COLL_NAME                ISO8859_6
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         36
    COLL_ID                         126
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         36
    COLL_ID                         126
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         36
    COLL_ID                         125
    CSET_NAME                       ISO8859_6
    CSET_DEFAULT_COLL               ISO8859_6_UNICODE
    DOMAIN_COLL_NAME                ISO8859_6_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         37
    COLL_ID                         0
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7
    DOMAIN_COLL_NAME                ISO8859_7
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         37
    COLL_ID                         0
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7
    DOMAIN_COLL_NAME                ISO8859_7
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         37
    COLL_ID                         0
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7
    DOMAIN_COLL_NAME                ISO8859_7
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         37
    COLL_ID                         126
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         37
    COLL_ID                         126
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         37
    COLL_ID                         125
    CSET_NAME                       ISO8859_7
    CSET_DEFAULT_COLL               ISO8859_7_UNICODE
    DOMAIN_COLL_NAME                ISO8859_7_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         38
    COLL_ID                         0
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8
    DOMAIN_COLL_NAME                ISO8859_8
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         38
    COLL_ID                         0
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8
    DOMAIN_COLL_NAME                ISO8859_8
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         38
    COLL_ID                         0
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8
    DOMAIN_COLL_NAME                ISO8859_8
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         38
    COLL_ID                         126
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         38
    COLL_ID                         126
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         38
    COLL_ID                         125
    CSET_NAME                       ISO8859_8
    CSET_DEFAULT_COLL               ISO8859_8_UNICODE
    DOMAIN_COLL_NAME                ISO8859_8_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         39
    COLL_ID                         0
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9
    DOMAIN_COLL_NAME                ISO8859_9
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         39
    COLL_ID                         0
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9
    DOMAIN_COLL_NAME                ISO8859_9
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         39
    COLL_ID                         0
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9
    DOMAIN_COLL_NAME                ISO8859_9
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         39
    COLL_ID                         126
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         39
    COLL_ID                         126
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         39
    COLL_ID                         125
    CSET_NAME                       ISO8859_9
    CSET_DEFAULT_COLL               ISO8859_9_UNICODE
    DOMAIN_COLL_NAME                ISO8859_9_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         40
    COLL_ID                         0
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13
    DOMAIN_COLL_NAME                ISO8859_13
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         40
    COLL_ID                         0
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13
    DOMAIN_COLL_NAME                ISO8859_13
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         40
    COLL_ID                         0
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13
    DOMAIN_COLL_NAME                ISO8859_13
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         40
    COLL_ID                         126
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         40
    COLL_ID                         126
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         40
    COLL_ID                         125
    CSET_NAME                       ISO8859_13
    CSET_DEFAULT_COLL               ISO8859_13_UNICODE
    DOMAIN_COLL_NAME                ISO8859_13_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         0
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852
    DOMAIN_COLL_NAME                DOS852
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         0
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852
    DOMAIN_COLL_NAME                DOS852
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         0
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852
    DOMAIN_COLL_NAME                DOS852
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         126
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         126
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         125
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DOS852_UNICODE
    DOMAIN_COLL_NAME                DOS852_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         1
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_CSY
    DOMAIN_COLL_NAME                DB_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         1
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_CSY
    DOMAIN_COLL_NAME                DB_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         1
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_CSY
    DOMAIN_COLL_NAME                DB_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         2
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_PLK
    DOMAIN_COLL_NAME                DB_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         2
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_PLK
    DOMAIN_COLL_NAME                DB_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         2
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_PLK
    DOMAIN_COLL_NAME                DB_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         4
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_SLO
    DOMAIN_COLL_NAME                DB_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         4
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_SLO
    DOMAIN_COLL_NAME                DB_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         4
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               DB_SLO
    DOMAIN_COLL_NAME                DB_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         5
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_CSY
    DOMAIN_COLL_NAME                PDOX_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         5
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_CSY
    DOMAIN_COLL_NAME                PDOX_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         5
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_CSY
    DOMAIN_COLL_NAME                PDOX_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         7
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_HUN
    DOMAIN_COLL_NAME                PDOX_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         7
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_HUN
    DOMAIN_COLL_NAME                PDOX_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         7
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_HUN
    DOMAIN_COLL_NAME                PDOX_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         6
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_PLK
    DOMAIN_COLL_NAME                PDOX_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         6
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_PLK
    DOMAIN_COLL_NAME                PDOX_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         6
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_PLK
    DOMAIN_COLL_NAME                PDOX_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         45
    COLL_ID                         8
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_SLO
    DOMAIN_COLL_NAME                PDOX_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         45
    COLL_ID                         8
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_SLO
    DOMAIN_COLL_NAME                PDOX_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         45
    COLL_ID                         8
    CSET_NAME                       DOS852
    CSET_DEFAULT_COLL               PDOX_SLO
    DOMAIN_COLL_NAME                PDOX_SLO
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         46
    COLL_ID                         0
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857
    DOMAIN_COLL_NAME                DOS857
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         46
    COLL_ID                         0
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857
    DOMAIN_COLL_NAME                DOS857
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         46
    COLL_ID                         0
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857
    DOMAIN_COLL_NAME                DOS857
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         46
    COLL_ID                         126
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         46
    COLL_ID                         126
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         46
    COLL_ID                         125
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DOS857_UNICODE
    DOMAIN_COLL_NAME                DOS857_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         46
    COLL_ID                         1
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DB_TRK
    DOMAIN_COLL_NAME                DB_TRK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         46
    COLL_ID                         1
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DB_TRK
    DOMAIN_COLL_NAME                DB_TRK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         46
    COLL_ID                         1
    CSET_NAME                       DOS857
    CSET_DEFAULT_COLL               DB_TRK
    DOMAIN_COLL_NAME                DB_TRK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         13
    COLL_ID                         0
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860
    DOMAIN_COLL_NAME                DOS860
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         13
    COLL_ID                         0
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860
    DOMAIN_COLL_NAME                DOS860
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         13
    COLL_ID                         0
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860
    DOMAIN_COLL_NAME                DOS860
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         13
    COLL_ID                         126
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         13
    COLL_ID                         126
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         13
    COLL_ID                         125
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DOS860_UNICODE
    DOMAIN_COLL_NAME                DOS860_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         13
    COLL_ID                         1
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DB_PTG860
    DOMAIN_COLL_NAME                DB_PTG860
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         13
    COLL_ID                         1
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DB_PTG860
    DOMAIN_COLL_NAME                DB_PTG860
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         13
    COLL_ID                         1
    CSET_NAME                       DOS860
    CSET_DEFAULT_COLL               DB_PTG860
    DOMAIN_COLL_NAME                DB_PTG860
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         47
    COLL_ID                         0
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861
    DOMAIN_COLL_NAME                DOS861
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         47
    COLL_ID                         0
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861
    DOMAIN_COLL_NAME                DOS861
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         47
    COLL_ID                         0
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861
    DOMAIN_COLL_NAME                DOS861
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         47
    COLL_ID                         126
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         47
    COLL_ID                         126
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         47
    COLL_ID                         125
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               DOS861_UNICODE
    DOMAIN_COLL_NAME                DOS861_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         47
    COLL_ID                         1
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               PDOX_ISL
    DOMAIN_COLL_NAME                PDOX_ISL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         47
    COLL_ID                         1
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               PDOX_ISL
    DOMAIN_COLL_NAME                PDOX_ISL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         47
    COLL_ID                         1
    CSET_NAME                       DOS861
    CSET_DEFAULT_COLL               PDOX_ISL
    DOMAIN_COLL_NAME                PDOX_ISL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         14
    COLL_ID                         0
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863
    DOMAIN_COLL_NAME                DOS863
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         14
    COLL_ID                         0
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863
    DOMAIN_COLL_NAME                DOS863
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         14
    COLL_ID                         0
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863
    DOMAIN_COLL_NAME                DOS863
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         14
    COLL_ID                         126
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         14
    COLL_ID                         126
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         14
    COLL_ID                         125
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DOS863_UNICODE
    DOMAIN_COLL_NAME                DOS863_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         14
    COLL_ID                         1
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DB_FRC863
    DOMAIN_COLL_NAME                DB_FRC863
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         14
    COLL_ID                         1
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DB_FRC863
    DOMAIN_COLL_NAME                DB_FRC863
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         14
    COLL_ID                         1
    CSET_NAME                       DOS863
    CSET_DEFAULT_COLL               DB_FRC863
    DOMAIN_COLL_NAME                DB_FRC863
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         50
    COLL_ID                         0
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL
    DOMAIN_COLL_NAME                CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         50
    COLL_ID                         0
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL
    DOMAIN_COLL_NAME                CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         50
    COLL_ID                         0
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL
    DOMAIN_COLL_NAME                CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         50
    COLL_ID                         126
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         50
    COLL_ID                         126
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         50
    COLL_ID                         125
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               CYRL_UNICODE
    DOMAIN_COLL_NAME                CYRL_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         50
    COLL_ID                         1
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               DB_RUS
    DOMAIN_COLL_NAME                DB_RUS
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         50
    COLL_ID                         1
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               DB_RUS
    DOMAIN_COLL_NAME                DB_RUS
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         50
    COLL_ID                         1
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               DB_RUS
    DOMAIN_COLL_NAME                DB_RUS
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         50
    COLL_ID                         2
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               PDOX_CYRL
    DOMAIN_COLL_NAME                PDOX_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         50
    COLL_ID                         2
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               PDOX_CYRL
    DOMAIN_COLL_NAME                PDOX_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         50
    COLL_ID                         2
    CSET_NAME                       CYRL
    CSET_DEFAULT_COLL               PDOX_CYRL
    DOMAIN_COLL_NAME                PDOX_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         9
    COLL_ID                         0
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737
    DOMAIN_COLL_NAME                DOS737
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         9
    COLL_ID                         0
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737
    DOMAIN_COLL_NAME                DOS737
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         9
    COLL_ID                         0
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737
    DOMAIN_COLL_NAME                DOS737
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         9
    COLL_ID                         126
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         9
    COLL_ID                         126
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         9
    COLL_ID                         125
    CSET_NAME                       DOS737
    CSET_DEFAULT_COLL               DOS737_UNICODE
    DOMAIN_COLL_NAME                DOS737_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         15
    COLL_ID                         0
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775
    DOMAIN_COLL_NAME                DOS775
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         15
    COLL_ID                         0
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775
    DOMAIN_COLL_NAME                DOS775
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         15
    COLL_ID                         0
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775
    DOMAIN_COLL_NAME                DOS775
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         15
    COLL_ID                         126
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         15
    COLL_ID                         126
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         15
    COLL_ID                         125
    CSET_NAME                       DOS775
    CSET_DEFAULT_COLL               DOS775_UNICODE
    DOMAIN_COLL_NAME                DOS775_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         16
    COLL_ID                         0
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858
    DOMAIN_COLL_NAME                DOS858
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         16
    COLL_ID                         0
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858
    DOMAIN_COLL_NAME                DOS858
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         16
    COLL_ID                         0
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858
    DOMAIN_COLL_NAME                DOS858
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         16
    COLL_ID                         126
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         16
    COLL_ID                         126
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         16
    COLL_ID                         125
    CSET_NAME                       DOS858
    CSET_DEFAULT_COLL               DOS858_UNICODE
    DOMAIN_COLL_NAME                DOS858_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         17
    COLL_ID                         0
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862
    DOMAIN_COLL_NAME                DOS862
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         17
    COLL_ID                         0
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862
    DOMAIN_COLL_NAME                DOS862
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         17
    COLL_ID                         0
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862
    DOMAIN_COLL_NAME                DOS862
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         17
    COLL_ID                         126
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         17
    COLL_ID                         126
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         17
    COLL_ID                         125
    CSET_NAME                       DOS862
    CSET_DEFAULT_COLL               DOS862_UNICODE
    DOMAIN_COLL_NAME                DOS862_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         18
    COLL_ID                         0
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864
    DOMAIN_COLL_NAME                DOS864
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         18
    COLL_ID                         0
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864
    DOMAIN_COLL_NAME                DOS864
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         18
    COLL_ID                         0
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864
    DOMAIN_COLL_NAME                DOS864
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         18
    COLL_ID                         126
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         18
    COLL_ID                         126
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         18
    COLL_ID                         125
    CSET_NAME                       DOS864
    CSET_DEFAULT_COLL               DOS864_UNICODE
    DOMAIN_COLL_NAME                DOS864_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         48
    COLL_ID                         0
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866
    DOMAIN_COLL_NAME                DOS866
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         48
    COLL_ID                         0
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866
    DOMAIN_COLL_NAME                DOS866
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         48
    COLL_ID                         0
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866
    DOMAIN_COLL_NAME                DOS866
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         48
    COLL_ID                         126
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         48
    COLL_ID                         126
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         48
    COLL_ID                         125
    CSET_NAME                       DOS866
    CSET_DEFAULT_COLL               DOS866_UNICODE
    DOMAIN_COLL_NAME                DOS866_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         49
    COLL_ID                         0
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869
    DOMAIN_COLL_NAME                DOS869
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         49
    COLL_ID                         0
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869
    DOMAIN_COLL_NAME                DOS869
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         49
    COLL_ID                         0
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869
    DOMAIN_COLL_NAME                DOS869
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         49
    COLL_ID                         126
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         49
    COLL_ID                         126
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         49
    COLL_ID                         125
    CSET_NAME                       DOS869
    CSET_DEFAULT_COLL               DOS869_UNICODE
    DOMAIN_COLL_NAME                DOS869_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         0
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250
    DOMAIN_COLL_NAME                WIN1250
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         0
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250
    DOMAIN_COLL_NAME                WIN1250
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         0
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250
    DOMAIN_COLL_NAME                WIN1250
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         126
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         126
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         125
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN1250_UNICODE
    DOMAIN_COLL_NAME                WIN1250_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         1
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_CSY
    DOMAIN_COLL_NAME                PXW_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         1
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_CSY
    DOMAIN_COLL_NAME                PXW_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         1
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_CSY
    DOMAIN_COLL_NAME                PXW_CSY
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         5
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUN
    DOMAIN_COLL_NAME                PXW_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         5
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUN
    DOMAIN_COLL_NAME                PXW_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         5
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUN
    DOMAIN_COLL_NAME                PXW_HUN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         2
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUNDC
    DOMAIN_COLL_NAME                PXW_HUNDC
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         2
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUNDC
    DOMAIN_COLL_NAME                PXW_HUNDC
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         2
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_HUNDC
    DOMAIN_COLL_NAME                PXW_HUNDC
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         3
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_PLK
    DOMAIN_COLL_NAME                PXW_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         3
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_PLK
    DOMAIN_COLL_NAME                PXW_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         3
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_PLK
    DOMAIN_COLL_NAME                PXW_PLK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         4
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_SLOV
    DOMAIN_COLL_NAME                PXW_SLOV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         4
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_SLOV
    DOMAIN_COLL_NAME                PXW_SLOV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         4
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               PXW_SLOV
    DOMAIN_COLL_NAME                PXW_SLOV
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         6
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               BS_BA
    DOMAIN_COLL_NAME                BS_BA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         6
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               BS_BA
    DOMAIN_COLL_NAME                BS_BA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         6
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               BS_BA
    DOMAIN_COLL_NAME                BS_BA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         7
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ
    DOMAIN_COLL_NAME                WIN_CZ
    COLL_ATTR                       3
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         7
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ
    DOMAIN_COLL_NAME                WIN_CZ
    COLL_ATTR                       3
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         7
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ
    DOMAIN_COLL_NAME                WIN_CZ
    COLL_ATTR                       3
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         51
    COLL_ID                         8
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ_CI_AI
    DOMAIN_COLL_NAME                WIN_CZ_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         51
    COLL_ID                         8
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ_CI_AI
    DOMAIN_COLL_NAME                WIN_CZ_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         51
    COLL_ID                         8
    CSET_NAME                       WIN1250
    CSET_DEFAULT_COLL               WIN_CZ_CI_AI
    DOMAIN_COLL_NAME                WIN_CZ_CI_AI
    COLL_ATTR                       7
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         52
    COLL_ID                         0
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251
    DOMAIN_COLL_NAME                WIN1251
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         52
    COLL_ID                         0
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251
    DOMAIN_COLL_NAME                WIN1251
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         52
    COLL_ID                         0
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251
    DOMAIN_COLL_NAME                WIN1251
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         52
    COLL_ID                         126
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         52
    COLL_ID                         126
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         52
    COLL_ID                         125
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UNICODE
    DOMAIN_COLL_NAME                WIN1251_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         52
    COLL_ID                         1
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               PXW_CYRL
    DOMAIN_COLL_NAME                PXW_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         52
    COLL_ID                         1
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               PXW_CYRL
    DOMAIN_COLL_NAME                PXW_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         52
    COLL_ID                         1
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               PXW_CYRL
    DOMAIN_COLL_NAME                PXW_CYRL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         52
    COLL_ID                         2
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UA
    DOMAIN_COLL_NAME                WIN1251_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         52
    COLL_ID                         2
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UA
    DOMAIN_COLL_NAME                WIN1251_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         52
    COLL_ID                         2
    CSET_NAME                       WIN1251
    CSET_DEFAULT_COLL               WIN1251_UA
    DOMAIN_COLL_NAME                WIN1251_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         0
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252
    DOMAIN_COLL_NAME                WIN1252
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         0
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252
    DOMAIN_COLL_NAME                WIN1252
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         0
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252
    DOMAIN_COLL_NAME                WIN1252
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         126
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         126
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         125
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN1252_UNICODE
    DOMAIN_COLL_NAME                WIN1252_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         1
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL
    DOMAIN_COLL_NAME                PXW_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         1
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL
    DOMAIN_COLL_NAME                PXW_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         1
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL
    DOMAIN_COLL_NAME                PXW_INTL
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         2
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL850
    DOMAIN_COLL_NAME                PXW_INTL850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         2
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL850
    DOMAIN_COLL_NAME                PXW_INTL850
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         2
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_INTL850
    DOMAIN_COLL_NAME                PXW_INTL850
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         3
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_NORDAN4
    DOMAIN_COLL_NAME                PXW_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         3
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_NORDAN4
    DOMAIN_COLL_NAME                PXW_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         3
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_NORDAN4
    DOMAIN_COLL_NAME                PXW_NORDAN4
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         6
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN_PTBR
    DOMAIN_COLL_NAME                WIN_PTBR
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         6
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN_PTBR
    DOMAIN_COLL_NAME                WIN_PTBR
    COLL_ATTR                       7
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         6
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               WIN_PTBR
    DOMAIN_COLL_NAME                WIN_PTBR
    COLL_ATTR                       7
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         4
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SPAN
    DOMAIN_COLL_NAME                PXW_SPAN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         4
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SPAN
    DOMAIN_COLL_NAME                PXW_SPAN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         4
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SPAN
    DOMAIN_COLL_NAME                PXW_SPAN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         53
    COLL_ID                         5
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SWEDFIN
    DOMAIN_COLL_NAME                PXW_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         53
    COLL_ID                         5
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SWEDFIN
    DOMAIN_COLL_NAME                PXW_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         53
    COLL_ID                         5
    CSET_NAME                       WIN1252
    CSET_DEFAULT_COLL               PXW_SWEDFIN
    DOMAIN_COLL_NAME                PXW_SWEDFIN
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         54
    COLL_ID                         0
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253
    DOMAIN_COLL_NAME                WIN1253
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         54
    COLL_ID                         0
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253
    DOMAIN_COLL_NAME                WIN1253
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         54
    COLL_ID                         0
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253
    DOMAIN_COLL_NAME                WIN1253
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         54
    COLL_ID                         126
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         54
    COLL_ID                         126
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         54
    COLL_ID                         125
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               WIN1253_UNICODE
    DOMAIN_COLL_NAME                WIN1253_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         54
    COLL_ID                         1
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               PXW_GREEK
    DOMAIN_COLL_NAME                PXW_GREEK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         54
    COLL_ID                         1
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               PXW_GREEK
    DOMAIN_COLL_NAME                PXW_GREEK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         54
    COLL_ID                         1
    CSET_NAME                       WIN1253
    CSET_DEFAULT_COLL               PXW_GREEK
    DOMAIN_COLL_NAME                PXW_GREEK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         55
    COLL_ID                         0
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254
    DOMAIN_COLL_NAME                WIN1254
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         55
    COLL_ID                         0
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254
    DOMAIN_COLL_NAME                WIN1254
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         55
    COLL_ID                         0
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254
    DOMAIN_COLL_NAME                WIN1254
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         55
    COLL_ID                         126
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         55
    COLL_ID                         126
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         55
    COLL_ID                         125
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               WIN1254_UNICODE
    DOMAIN_COLL_NAME                WIN1254_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         55
    COLL_ID                         1
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               PXW_TURK
    DOMAIN_COLL_NAME                PXW_TURK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         55
    COLL_ID                         1
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               PXW_TURK
    DOMAIN_COLL_NAME                PXW_TURK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         55
    COLL_ID                         1
    CSET_NAME                       WIN1254
    CSET_DEFAULT_COLL               PXW_TURK
    DOMAIN_COLL_NAME                PXW_TURK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         0
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT
    DOMAIN_COLL_NAME                NEXT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         0
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT
    DOMAIN_COLL_NAME                NEXT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         0
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT
    DOMAIN_COLL_NAME                NEXT
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         126
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         126
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         125
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NEXT_UNICODE
    DOMAIN_COLL_NAME                NEXT_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         2
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_DEU
    DOMAIN_COLL_NAME                NXT_DEU
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         2
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_DEU
    DOMAIN_COLL_NAME                NXT_DEU
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         2
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_DEU
    DOMAIN_COLL_NAME                NXT_DEU
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         5
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ESP
    DOMAIN_COLL_NAME                NXT_ESP
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         5
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ESP
    DOMAIN_COLL_NAME                NXT_ESP
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         5
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ESP
    DOMAIN_COLL_NAME                NXT_ESP
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         3
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_FRA
    DOMAIN_COLL_NAME                NXT_FRA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         3
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_FRA
    DOMAIN_COLL_NAME                NXT_FRA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         3
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_FRA
    DOMAIN_COLL_NAME                NXT_FRA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         4
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ITA
    DOMAIN_COLL_NAME                NXT_ITA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         4
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ITA
    DOMAIN_COLL_NAME                NXT_ITA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         4
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_ITA
    DOMAIN_COLL_NAME                NXT_ITA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         19
    COLL_ID                         1
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_US
    DOMAIN_COLL_NAME                NXT_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         19
    COLL_ID                         1
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_US
    DOMAIN_COLL_NAME                NXT_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         19
    COLL_ID                         1
    CSET_NAME                       NEXT
    CSET_DEFAULT_COLL               NXT_US
    DOMAIN_COLL_NAME                NXT_US
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         58
    COLL_ID                         0
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255
    DOMAIN_COLL_NAME                WIN1255
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         58
    COLL_ID                         0
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255
    DOMAIN_COLL_NAME                WIN1255
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         58
    COLL_ID                         0
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255
    DOMAIN_COLL_NAME                WIN1255
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         58
    COLL_ID                         126
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         58
    COLL_ID                         126
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         58
    COLL_ID                         125
    CSET_NAME                       WIN1255
    CSET_DEFAULT_COLL               WIN1255_UNICODE
    DOMAIN_COLL_NAME                WIN1255_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         59
    COLL_ID                         0
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256
    DOMAIN_COLL_NAME                WIN1256
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         59
    COLL_ID                         0
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256
    DOMAIN_COLL_NAME                WIN1256
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         59
    COLL_ID                         0
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256
    DOMAIN_COLL_NAME                WIN1256
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         59
    COLL_ID                         126
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         59
    COLL_ID                         126
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         59
    COLL_ID                         125
    CSET_NAME                       WIN1256
    CSET_DEFAULT_COLL               WIN1256_UNICODE
    DOMAIN_COLL_NAME                WIN1256_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         60
    COLL_ID                         0
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257
    DOMAIN_COLL_NAME                WIN1257
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         60
    COLL_ID                         0
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257
    DOMAIN_COLL_NAME                WIN1257
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         60
    COLL_ID                         0
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257
    DOMAIN_COLL_NAME                WIN1257
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         60
    COLL_ID                         126
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         60
    COLL_ID                         126
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         60
    COLL_ID                         125
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_UNICODE
    DOMAIN_COLL_NAME                WIN1257_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         60
    COLL_ID                         1
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_EE
    DOMAIN_COLL_NAME                WIN1257_EE
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         60
    COLL_ID                         1
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_EE
    DOMAIN_COLL_NAME                WIN1257_EE
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         60
    COLL_ID                         1
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_EE
    DOMAIN_COLL_NAME                WIN1257_EE
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         60
    COLL_ID                         2
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LT
    DOMAIN_COLL_NAME                WIN1257_LT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         60
    COLL_ID                         2
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LT
    DOMAIN_COLL_NAME                WIN1257_LT
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         60
    COLL_ID                         2
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LT
    DOMAIN_COLL_NAME                WIN1257_LT
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         60
    COLL_ID                         3
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LV
    DOMAIN_COLL_NAME                WIN1257_LV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         60
    COLL_ID                         3
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LV
    DOMAIN_COLL_NAME                WIN1257_LV
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         60
    COLL_ID                         3
    CSET_NAME                       WIN1257
    CSET_DEFAULT_COLL               WIN1257_LV
    DOMAIN_COLL_NAME                WIN1257_LV
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         44
    COLL_ID                         0
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601
    DOMAIN_COLL_NAME                KSC_5601
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         44
    COLL_ID                         0
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601
    DOMAIN_COLL_NAME                KSC_5601
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         44
    COLL_ID                         0
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601
    DOMAIN_COLL_NAME                KSC_5601
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         44
    COLL_ID                         126
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         44
    COLL_ID                         126
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         44
    COLL_ID                         125
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_5601_UNICODE
    DOMAIN_COLL_NAME                KSC_5601_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         44
    COLL_ID                         1
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_DICTIONARY
    DOMAIN_COLL_NAME                KSC_DICTIONARY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         44
    COLL_ID                         1
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_DICTIONARY
    DOMAIN_COLL_NAME                KSC_DICTIONARY
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         44
    COLL_ID                         1
    CSET_NAME                       KSC_5601
    CSET_DEFAULT_COLL               KSC_DICTIONARY
    DOMAIN_COLL_NAME                KSC_DICTIONARY
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         56
    COLL_ID                         0
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5
    DOMAIN_COLL_NAME                BIG_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         56
    COLL_ID                         0
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5
    DOMAIN_COLL_NAME                BIG_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         56
    COLL_ID                         0
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5
    DOMAIN_COLL_NAME                BIG_5
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         56
    COLL_ID                         126
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         56
    COLL_ID                         126
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         56
    COLL_ID                         125
    CSET_NAME                       BIG_5
    CSET_DEFAULT_COLL               BIG_5_UNICODE
    DOMAIN_COLL_NAME                BIG_5_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         57
    COLL_ID                         0
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312
    DOMAIN_COLL_NAME                GB_2312
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         57
    COLL_ID                         0
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312
    DOMAIN_COLL_NAME                GB_2312
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         57
    COLL_ID                         0
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312
    DOMAIN_COLL_NAME                GB_2312
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         57
    COLL_ID                         126
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         57
    COLL_ID                         126
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         57
    COLL_ID                         125
    CSET_NAME                       GB_2312
    CSET_DEFAULT_COLL               GB_2312_UNICODE
    DOMAIN_COLL_NAME                GB_2312_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         63
    COLL_ID                         0
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R
    DOMAIN_COLL_NAME                KOI8R
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         63
    COLL_ID                         0
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R
    DOMAIN_COLL_NAME                KOI8R
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         63
    COLL_ID                         0
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R
    DOMAIN_COLL_NAME                KOI8R
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         63
    COLL_ID                         126
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         63
    COLL_ID                         126
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         63
    COLL_ID                         125
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_UNICODE
    DOMAIN_COLL_NAME                KOI8R_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         63
    COLL_ID                         1
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_RU
    DOMAIN_COLL_NAME                KOI8R_RU
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         63
    COLL_ID                         1
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_RU
    DOMAIN_COLL_NAME                KOI8R_RU
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         63
    COLL_ID                         1
    CSET_NAME                       KOI8R
    CSET_DEFAULT_COLL               KOI8R_RU
    DOMAIN_COLL_NAME                KOI8R_RU
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         64
    COLL_ID                         0
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U
    DOMAIN_COLL_NAME                KOI8U
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         64
    COLL_ID                         0
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U
    DOMAIN_COLL_NAME                KOI8U
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         64
    COLL_ID                         0
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U
    DOMAIN_COLL_NAME                KOI8U
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         64
    COLL_ID                         126
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         64
    COLL_ID                         126
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         64
    COLL_ID                         125
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UNICODE
    DOMAIN_COLL_NAME                KOI8U_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         64
    COLL_ID                         1
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UA
    DOMAIN_COLL_NAME                KOI8U_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         64
    COLL_ID                         1
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UA
    DOMAIN_COLL_NAME                KOI8U_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         64
    COLL_ID                         1
    CSET_NAME                       KOI8U
    CSET_DEFAULT_COLL               KOI8U_UA
    DOMAIN_COLL_NAME                KOI8U_UA
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         65
    COLL_ID                         0
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258
    DOMAIN_COLL_NAME                WIN1258
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         65
    COLL_ID                         0
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258
    DOMAIN_COLL_NAME                WIN1258
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         65
    COLL_ID                         0
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258
    DOMAIN_COLL_NAME                WIN1258
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         65
    COLL_ID                         126
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         65
    COLL_ID                         126
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       6
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         65
    COLL_ID                         125
    CSET_NAME                       WIN1258
    CSET_DEFAULT_COLL               WIN1258_UNICODE
    DOMAIN_COLL_NAME                WIN1258_UNICODE
    COLL_ATTR                       0
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         66
    COLL_ID                         0
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620
    DOMAIN_COLL_NAME                TIS620
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         66
    COLL_ID                         0
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620
    DOMAIN_COLL_NAME                TIS620
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         66
    COLL_ID                         0
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620
    DOMAIN_COLL_NAME                TIS620
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         66
    COLL_ID                         126
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         66
    COLL_ID                         126
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         66
    COLL_ID                         1
    CSET_NAME                       TIS620
    CSET_DEFAULT_COLL               TIS620_UNICODE
    DOMAIN_COLL_NAME                TIS620_UNICODE
    COLL_ATTR                       1
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         67
    COLL_ID                         0
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK
    DOMAIN_COLL_NAME                GBK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         67
    COLL_ID                         0
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK
    DOMAIN_COLL_NAME                GBK
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         67
    COLL_ID                         0
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK
    DOMAIN_COLL_NAME                GBK
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         67
    COLL_ID                         126
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         67
    COLL_ID                         126
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         67
    COLL_ID                         1
    CSET_NAME                       GBK
    CSET_DEFAULT_COLL               GBK_UNICODE
    DOMAIN_COLL_NAME                GBK_UNICODE
    COLL_ATTR                       1
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         68
    COLL_ID                         0
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C
    DOMAIN_COLL_NAME                CP943C
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         68
    COLL_ID                         0
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C
    DOMAIN_COLL_NAME                CP943C
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         68
    COLL_ID                         0
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C
    DOMAIN_COLL_NAME                CP943C
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         68
    COLL_ID                         126
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         68
    COLL_ID                         126
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         68
    COLL_ID                         1
    CSET_NAME                       CP943C
    CSET_DEFAULT_COLL               CP943C_UNICODE
    DOMAIN_COLL_NAME                CP943C_UNICODE
    COLL_ATTR                       1
    COLL_SPEC                       COLL-VERSION=153.88



    F_NAME                          DM_BLOB
    CSET_ID                         69
    COLL_ID                         0
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030
    DOMAIN_COLL_NAME                GB18030
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_NAME
    CSET_ID                         69
    COLL_ID                         0
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030
    DOMAIN_COLL_NAME                GB18030
    COLL_ATTR                       1
    COLL_SPEC                       <null>

    F_NAME                          DM_TEXT
    CSET_ID                         69
    COLL_ID                         0
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030
    DOMAIN_COLL_NAME                GB18030
    COLL_ATTR                       1
    COLL_SPEC                       <null>



    F_NAME                          DM_BLOB
    CSET_ID                         69
    COLL_ID                         126
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_NAME
    CSET_ID                         69
    COLL_ID                         126
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030_UNICODE
    DOMAIN_COLL_NAME                CO_UNICODE
    COLL_ATTR                       7
    COLL_SPEC                       COLL-VERSION=153.88;NUMERIC-SORT=1

    F_NAME                          DM_TEXT
    CSET_ID                         69
    COLL_ID                         1
    CSET_NAME                       GB18030
    CSET_DEFAULT_COLL               GB18030_UNICODE
    DOMAIN_COLL_NAME                GB18030_UNICODE
    COLL_ATTR                       1
    COLL_SPEC                       COLL-VERSION=153.88

"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.db.set_async_write()
    act_1.expected_stdout = expected_stdout_1
    with act_1.envar('ISC_USER', act_1.db.user), act_1.envar('ISC_PASSWORD', act_1.db.password):
        act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout
