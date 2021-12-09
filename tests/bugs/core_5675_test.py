#coding:utf-8
#
# id:           bugs.core_5675
# title:        isc_vax_integer() and isc_portable_integer() work wrongly with short negative numbers
# decription:
#                  Confirmed bug on4.0.0.800.
#                  Works fine on:
#                       FB25SC, build 2.5.8.27089: OK, 0.422s.
#                       FB30SS, build 3.0.3.32876: OK, 1.484s.
#                       FB40SS, build 4.0.0.852: OK, 1.156s.
#
#                  NB. It seems that some bug exists in function _renderSizedIntegerForSPB from fdb package (services.py):
#                     iRaw = struct.pack(myformat, i)
#                     iConv = api.isc_vax_integer(iRaw, len(iRaw))
#                  This function cuts off high 4 bytes when we pass to it bugint values greater than 2^31, i.e.:
#                  2147483648L  ==> reversed = b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
#                  -2147483649L ==> reversed = b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00'
#
#                  For this reason it was decided currently to limit scope by specifying numbers with abs() less than 2^31 - untill fdb driver will be fixed.
#                  See letter from dimitr 08-jan-2018 20:56
#
#                  25.08.2020: adjusted name of function from services that must work here:
#                  its name is "_render_sized_integer_for_spb" rather than old "_renderSizedIntegerForSPB".
#                  Checked on 4.0.0.2173; 3.0.7.33357; 2.5.9.27152.
#
# tracker_id:   CORE-5675
# min_versions: ['2.5.8']
# versions:     2.5.8
# qmid:         None

import pytest
from firebird.qa import db_factory, python_act, Action

# version: 2.5.8
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

# test_script_1
#---
#
#  from __future__ import print_function
#  import os
#  import binascii
#  from fdb import services
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#  db_conn.close()
#  con = services.connect(host='localhost', user='sysdba', password='masterkey')
#  #print( con.get_server_version() )
#
#  dec_values=(  1,     -1,   127,  -128,   128,  -256, 255,  -32768, 32767, 32768, -65536, 65535, 65536 ) #,    32767, -32768, 32768, -32769,  2147483647, -2147483648, 2147483648, -2147483649, 3000000000, 3000000000000, 9223372036854775807 )
#  num_ctypes=( 'b',   'b',   'b',   'b',   'b',   'B',  'B',    'h',   'h',   'h',    'H',   'H',   'H' ) #,     'i',    'i',   'i',    'i',         'i',         'i',         'q',        'q',        'q',          'q',                  'q' )
#
#  #dec_values=(  1,     -1,   127,  -128,   128,  -256, 255,  -32768, 32767, 32768, -65536, 65535, 65536 ,    32767, -32768, 32768, -32769,  2147483647, -2147483648, 2147483648, -2147483649, 3000000000, 3000000000000, 9223372036854775807 )
#  #num_ctypes=( 'b',   'b',   'b',   'b',   'b',   'B',  'B',    'h',   'h',   'h',    'H',   'H',   'H' ,      'i',    'i',   'i',    'i',         'i',         'i',        'q',         'q',        'q',           'q',                  'q')
#
#
#  for i in range(0, len(dec_values)):
#     num = dec_values[i]
#     fmt = num_ctypes[i]
#     msg = ['Try revert bytes in decimal value:', "{:12d}".format(num), ' using struct format: ', '"'+fmt+'"']
#     try:
#         # OLD name of function: (numericFormat, numericBytes) = services._renderSizedIntegerForSPB(num, fmt)
#         (numericFormat, numericBytes) = services._render_sized_integer_for_spb(num, fmt)
#         rev = binascii.hexlify(numericBytes)
#     except Exception, e:
#         rev = e[0]
#     finally:
#         print( ' '.join( (msg + ['; result: ',rev,]) ) )
#
#  con.close()
#
#---

act_1 = python_act('db_1', substitutions=substitutions_1)

expected_stdout_1 = """
    Try revert bytes in decimal value:            1  using struct format:  "b" ; result:  01
    Try revert bytes in decimal value:           -1  using struct format:  "b" ; result:  ff
    Try revert bytes in decimal value:          127  using struct format:  "b" ; result:  7f
    Try revert bytes in decimal value:         -128  using struct format:  "b" ; result:  80
    Try revert bytes in decimal value:          128  using struct format:  "b" ; result:  byte format requires -128 <= number <= 127
    Try revert bytes in decimal value:         -256  using struct format:  "B" ; result:  ubyte format requires 0 <= number <= 255
    Try revert bytes in decimal value:          255  using struct format:  "B" ; result:  ubyte format requires 0 <= number <= 255
    Try revert bytes in decimal value:       -32768  using struct format:  "h" ; result:  0080
    Try revert bytes in decimal value:        32767  using struct format:  "h" ; result:  ff7f
    Try revert bytes in decimal value:        32768  using struct format:  "h" ; result:  short format requires SHRT_MIN <= number <= SHRT_MAX
    Try revert bytes in decimal value:       -65536  using struct format:  "H" ; result:  ushort format requires 0 <= number <= USHRT_MAX
    Try revert bytes in decimal value:        65535  using struct format:  "H" ; result:  ushort format requires 0 <= number <= USHRT_MAX
    Try revert bytes in decimal value:        65536  using struct format:  "H" ; result:  ushort format requires 0 <= number <= USHRT_MAX
"""

@pytest.mark.version('>=2.5.8')
def test_1(act_1: Action):
    pytest.skip("Requires function not provided by driver")
