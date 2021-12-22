#coding:utf-8
#
# id:           functional.tabloid.eqc_306263
# title:        Check ability to run complex query
# decription:   
#                 
# tracker_id:   
# min_versions: ['2.5.5']
# versions:     2.5.5
# qmid:         

import pytest
from firebird.qa import db_factory, python_act, Action

# version: 2.5.5
# resources: None

substitutions_1 = [('0.000000000000000.*', '0.0000000000000000')]

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
# import os
#  import zipfile
#  os.environ["ISC_USER"] = 'SYSDBA'
#  os.environ["ISC_PASSWORD"] = 'masterkey'
#  
#  db_conn.close()
#  
#  zf = zipfile.ZipFile( os.path.join(context['files_location'],'eqc306263.zip') )
#  zf.extractall( context['temp_directory'] )
#  zf.close()
#  
#  fbk = os.path.join(context['temp_directory'],'eqc306263.fbk')
#  
#  runProgram('gbak',['-rep', fbk, dsn])
#  
#  script="""set list on; 
#      select
#          objeschlue.obsch_schl,
#          schluedef.schld_bzg,
#          objeschlue.obj_id,
#          darlehen.vertrag,
#          darlkond.dlko_annui,
#          zuschkond.zuko_wrt,
#          darlkond.dlko_unom,
#          darlgeber.darlg_bzg,
#          objeschlue.obsch_gb,
#          objeschlue.obsch_gabd,
#          darlkond.flgk_kz,
#          zuschkond.faelligkeit,
#          darl_obper.top_id,
#          darlkond.dlko_gvond,
#          darlkond.dlko_gbisd,
#          zuschkond.zuko_id,
#          zuschkond.zuko_gvond,
#          zuschkond.zuko_gbid,
#          darl_obper.obj_id
#      from
#      (
#          (
#              (
#                  (
#                      (
#                          (
#                              darl_obper darl_obper
#                              inner join darlehen darlehen on darl_obper.darl_id=darlehen.darl_id
#                          )
#                          inner join objeschlue objeschlue on darlehen.darl_id=objeschlue.darl_id
#                      )
#                      inner join darlgeber darlgeber on darlehen.darlg_id=darlgeber.darlg_id
#                  )
#                  inner join darlkond darlkond on darlehen.darl_id=darlkond.darl_id
#              )
#              left outer join schluedef schluedef on objeschlue.schld_id=schluedef.schld_id
#          )
#          left outer join zuschkond zuschkond on darlehen.darl_id=zuschkond.darl_id
#      )
#      where
#          darl_obper.obj_id=3759
#          and darlkond.dlko_gvond<'12/02/2011 00:00:00'
#          and darlkond.dlko_gbisd>='12/01/2011 00:00:00'
#          and objeschlue.obj_id=3759
#          and objeschlue.obsch_gb>='12/02/2011 00:00:00'
#          and objeschlue.obsch_gabd<'12/02/2011 00:00:00'
#          and darl_obper.top_id is  null
#          and (
#                  zuschkond.zuko_id is  null
#                  or zuschkond.zuko_gvond<'12/02/2011 00:00:00' and zuschkond.zuko_gbid>='12/01/2011 00:00:00'
#              );
#      commit;
#  """
#  runProgram('isql',[dsn,'-q'],script)
#  
#  ###############################
#  # Cleanup.
#  os.remove(fbk)
#---
act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    OBSCH_SCHL                      1.000000000000000
    SCHLD_BZG                       <null>
    OBJ_ID                          3759
    VERTRAG                         <null>
    DLKO_ANNUI                      0.0000000000000000
    ZUKO_WRT                        <null>
    DLKO_UNOM                       0.0000000000000000
    DARLG_BZG                       <null>
    OBSCH_GB                        2100-01-01 00:00:00.0000
    OBSCH_GABD                      2005-08-01 00:00:00.0000
    FLGK_KZ                         4
    FAELLIGKEIT                     <null>
    TOP_ID                          <null>
    DLKO_GVOND                      2011-01-01 00:00:00.0000
    DLKO_GBISD                      2100-01-01 00:00:00.0000
    ZUKO_ID                         <null>
    ZUKO_GVOND                      <null>
    ZUKO_GBID                       <null>
    OBJ_ID                          3759
"""

@pytest.mark.version('>=2.5.5')
def test_1(act_1: Action):
    pytest.fail("Test not IMPLEMENTED")


