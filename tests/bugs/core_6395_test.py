#coding:utf-8

"""
ID:          issue-6633
ISSUE:       6633
TITLE:       Allow usage of time zone displacement in config DefaultTimeZone
DESCRIPTION:
    We make backup of current firebird.conf for changing it two times:
    1. Add line with DefaultTimeZone = -7:00 and get local time by making *LOCAL* connect to current DB;
    2. Restore previous firebird.conf from its .bak-copy do second change: add line with DefaultTimeZone = 7:00.
       Then we run second local connect.

    Each connect will ask FB to return CURRENT_TIME value (with casting it to '%H:%M:%S' format).
    Expected result: values must change from 1st to 2nd run for 14 hours (840 minutes).
JIRA:        CORE-6395
FBTEST:      bugs.core_6395
NOTES:
    Confirmed improvement on 4.0.0.2185.
    Value of time did not differ on previous builds (checked 4..0.2170).
"""

from pathlib import Path
import pytest
from firebird.qa import *
import subprocess
import datetime


server = server_factory()
db = db_factory(control='server')
act = python_act('db')

new_config = temp_file('new_firebird.conf')

@pytest.mark.version('>=4.0')
def test_1(act: Action, new_config):
    
#db_name=db_conn.database_name

#--------------------------------------------

    def get_local_time(act: Action):
        connect_sql = """
        set heading off;
        select substring( cast(cast(current_time as time) as varchar(13)) from 1 for 8) from rdb$database;
        """
        act.reset()
        act.isql(switches=['-q'], input=connect_sql)
        changed_time = '00:00:00'
        for line in act.stdout.split('\n'):
            if line.split():
                changed_time = line.strip()
                print(changed_time)

        return changed_time

    text2app="""
    ### TEMPORARY CHANGED BY FBTEST FRAMEWORK ###
    DefaultTimeZone = -7:00
    ##############################################
    """
    new_config.write_text(text2app)
    act.db.control.config.add('firebird.conf', new_config)
    act.db.control.restart()

    changed_time1 = get_local_time(act)
    
    act.db.control.config.restore()  

    text2app="""
    ### TEMPORARY CHANGED BY FBTEST FRAMEWORK ###
    DefaultTimeZone = +7:00
    ##############################################
    """
    new_config.write_text(text2app)
    act.db.control.config.add('firebird.conf', new_config)
    act.db.control.restart()

    changed_time2 = get_local_time(act)
    time_diff = (datetime.datetime.strptime(changed_time2, '%H:%M:%S') - datetime.datetime.strptime(changed_time1, '%H:%M:%S')).seconds // 60
    assert time_diff == 840
