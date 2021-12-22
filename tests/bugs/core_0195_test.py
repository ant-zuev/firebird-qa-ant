#coding:utf-8
#
# id:           bugs.core_0195
# title:        Bugcheck 291
# decription:   
# tracker_id:   
# min_versions: ['2.0.7']
# versions:     2.0.7
# qmid:         bugs.core_0195

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.0.7
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    create table tbl_bugcheck291
    (
     ID integer NOT NULL PRIMARY KEY,
     DATA integer
    );
    
    commit;
    
    insert into tbl_bugcheck291 (id, data) values (1,100);
    
    commit;
    
    set term ^;
    create trigger bu_tbl_bugcheck291 for tbl_bugcheck291
        before update
    as
    begin
        if(new.data is not null) then
        begin
           if(new.data<110) then
           begin
               update tbl_bugcheck291 x set x.data=new.data+1 where x.id=new.id;
           end
        end
    end
    ^
    set term ;^
    commit;
    
    update tbl_bugcheck291 set data=105 where id=1;
    
    commit;
    
    update tbl_bugcheck291 set data=105 where id=1;
    
    /*FB2.5: internal Firebird consistency check (cannot find record back version (291), file: vio.cpp line: 5014).*/
    update tbl_bugcheck291 set data=105 where id=1;
    
    /*internal Firebird consistency check (can't continue after bugcheck).*/
    update tbl_bugcheck291 set data=105 where id=1;
    update tbl_bugcheck291 set data=105 where id=1;
    update tbl_bugcheck291 set data=105 where id=1;
    update tbl_bugcheck291 set data=105 where id=1;
    commit;

    ------------------------------------------------

    create table "TBL_BUGCHECK291B"
    (
      "DATA" integer,
      "FLAG" integer
    );
    
    set term ^;
    create trigger "TRG_BUGCHECK291B" for "TBL_BUGCHECK291B"
    active before update position 1
    as
    begin
        if (new.Flag = 16 and new.Data = 1) then begin
          update tbl_bugcheck291b set Data = 2 where Flag = 46;
          update tbl_bugcheck291b set Data = 3 where Flag = 46;
        end
        if (new.Flag = 46 and new.Data = 2) then begin
          update tbl_bugcheck291b set Data = 4 where Flag = 14;
          update tbl_bugcheck291b set Data = 5 where Flag = 15;
        end
        if (new.Flag = 14 and new.Data = 4) then begin
          update tbl_bugcheck291b set Data = 6 where Flag = 46;
        end
        if (new.Flag = 15 and new.Data = 5) then begin
          update tbl_bugcheck291b set Data = 7 where Flag = 46;
        end
        if (new.Flag = 46 and new.Data = 3) then begin
          update tbl_bugcheck291b set Data = 8 where Flag = 46;
        end
    end
    ^
    set term ;^
    commit;
    
    insert into tbl_bugcheck291b(Flag) values(14);
    insert into tbl_bugcheck291b(Flag) values(15);
    insert into tbl_bugcheck291b(Flag) values(16);
    insert into tbl_bugcheck291b(Flag) values(46);
    commit;
    
    update tbl_bugcheck291b set Data=1 where Flag = 16;
    commit;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)


@pytest.mark.version('>=2.0.7')
def test_1(act_1: Action):
    act_1.execute()

