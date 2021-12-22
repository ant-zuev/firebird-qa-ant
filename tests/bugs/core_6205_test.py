#coding:utf-8
#
# id:           bugs.core_6205
# title:        Generate proper error for UNION DISTINCT with more than 255 columns
# decription:   
#                   Confirmed bug on 4.0.0.1691, got STDERR:
#                       Statement failed, SQLSTATE = HY000
#                       invalid request BLR at offset 5668
#                       -BLR syntax error: expected record selection expression clause at offset 5669, encountered 24
#               
#                   Checked on 4.0.0.1693: OK, 1.196s.
#                
# tracker_id:   CORE-6205
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 4.0
# resources: None

substitutions_1 = []

init_script_1 = """"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """
    set list on;

    select
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256
    from rdb$database

    union all

    select
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256
    from rdb$database
    ;

    select
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256
    from rdb$database

    union --all

    select
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256
    from rdb$database
    ;
"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """
    CONSTANT                        1
    CONSTANT                        2
    CONSTANT                        3
    CONSTANT                        4
    CONSTANT                        5
    CONSTANT                        6
    CONSTANT                        7
    CONSTANT                        8
    CONSTANT                        9
    CONSTANT                        10
    CONSTANT                        11
    CONSTANT                        12
    CONSTANT                        13
    CONSTANT                        14
    CONSTANT                        15
    CONSTANT                        16
    CONSTANT                        17
    CONSTANT                        18
    CONSTANT                        19
    CONSTANT                        20
    CONSTANT                        21
    CONSTANT                        22
    CONSTANT                        23
    CONSTANT                        24
    CONSTANT                        25
    CONSTANT                        26
    CONSTANT                        27
    CONSTANT                        28
    CONSTANT                        29
    CONSTANT                        30
    CONSTANT                        31
    CONSTANT                        32
    CONSTANT                        33
    CONSTANT                        34
    CONSTANT                        35
    CONSTANT                        36
    CONSTANT                        37
    CONSTANT                        38
    CONSTANT                        39
    CONSTANT                        40
    CONSTANT                        41
    CONSTANT                        42
    CONSTANT                        43
    CONSTANT                        44
    CONSTANT                        45
    CONSTANT                        46
    CONSTANT                        47
    CONSTANT                        48
    CONSTANT                        49
    CONSTANT                        50
    CONSTANT                        51
    CONSTANT                        52
    CONSTANT                        53
    CONSTANT                        54
    CONSTANT                        55
    CONSTANT                        56
    CONSTANT                        57
    CONSTANT                        58
    CONSTANT                        59
    CONSTANT                        60
    CONSTANT                        61
    CONSTANT                        62
    CONSTANT                        63
    CONSTANT                        64
    CONSTANT                        65
    CONSTANT                        66
    CONSTANT                        67
    CONSTANT                        68
    CONSTANT                        69
    CONSTANT                        70
    CONSTANT                        71
    CONSTANT                        72
    CONSTANT                        73
    CONSTANT                        74
    CONSTANT                        75
    CONSTANT                        76
    CONSTANT                        77
    CONSTANT                        78
    CONSTANT                        79
    CONSTANT                        80
    CONSTANT                        81
    CONSTANT                        82
    CONSTANT                        83
    CONSTANT                        84
    CONSTANT                        85
    CONSTANT                        86
    CONSTANT                        87
    CONSTANT                        88
    CONSTANT                        89
    CONSTANT                        90
    CONSTANT                        91
    CONSTANT                        92
    CONSTANT                        93
    CONSTANT                        94
    CONSTANT                        95
    CONSTANT                        96
    CONSTANT                        97
    CONSTANT                        98
    CONSTANT                        99
    CONSTANT                        100
    CONSTANT                        101
    CONSTANT                        102
    CONSTANT                        103
    CONSTANT                        104
    CONSTANT                        105
    CONSTANT                        106
    CONSTANT                        107
    CONSTANT                        108
    CONSTANT                        109
    CONSTANT                        110
    CONSTANT                        111
    CONSTANT                        112
    CONSTANT                        113
    CONSTANT                        114
    CONSTANT                        115
    CONSTANT                        116
    CONSTANT                        117
    CONSTANT                        118
    CONSTANT                        119
    CONSTANT                        120
    CONSTANT                        121
    CONSTANT                        122
    CONSTANT                        123
    CONSTANT                        124
    CONSTANT                        125
    CONSTANT                        126
    CONSTANT                        127
    CONSTANT                        128
    CONSTANT                        129
    CONSTANT                        130
    CONSTANT                        131
    CONSTANT                        132
    CONSTANT                        133
    CONSTANT                        134
    CONSTANT                        135
    CONSTANT                        136
    CONSTANT                        137
    CONSTANT                        138
    CONSTANT                        139
    CONSTANT                        140
    CONSTANT                        141
    CONSTANT                        142
    CONSTANT                        143
    CONSTANT                        144
    CONSTANT                        145
    CONSTANT                        146
    CONSTANT                        147
    CONSTANT                        148
    CONSTANT                        149
    CONSTANT                        150
    CONSTANT                        151
    CONSTANT                        152
    CONSTANT                        153
    CONSTANT                        154
    CONSTANT                        155
    CONSTANT                        156
    CONSTANT                        157
    CONSTANT                        158
    CONSTANT                        159
    CONSTANT                        160
    CONSTANT                        161
    CONSTANT                        162
    CONSTANT                        163
    CONSTANT                        164
    CONSTANT                        165
    CONSTANT                        166
    CONSTANT                        167
    CONSTANT                        168
    CONSTANT                        169
    CONSTANT                        170
    CONSTANT                        171
    CONSTANT                        172
    CONSTANT                        173
    CONSTANT                        174
    CONSTANT                        175
    CONSTANT                        176
    CONSTANT                        177
    CONSTANT                        178
    CONSTANT                        179
    CONSTANT                        180
    CONSTANT                        181
    CONSTANT                        182
    CONSTANT                        183
    CONSTANT                        184
    CONSTANT                        185
    CONSTANT                        186
    CONSTANT                        187
    CONSTANT                        188
    CONSTANT                        189
    CONSTANT                        190
    CONSTANT                        191
    CONSTANT                        192
    CONSTANT                        193
    CONSTANT                        194
    CONSTANT                        195
    CONSTANT                        196
    CONSTANT                        197
    CONSTANT                        198
    CONSTANT                        199
    CONSTANT                        200
    CONSTANT                        201
    CONSTANT                        202
    CONSTANT                        203
    CONSTANT                        204
    CONSTANT                        205
    CONSTANT                        206
    CONSTANT                        207
    CONSTANT                        208
    CONSTANT                        209
    CONSTANT                        210
    CONSTANT                        211
    CONSTANT                        212
    CONSTANT                        213
    CONSTANT                        214
    CONSTANT                        215
    CONSTANT                        216
    CONSTANT                        217
    CONSTANT                        218
    CONSTANT                        219
    CONSTANT                        220
    CONSTANT                        221
    CONSTANT                        222
    CONSTANT                        223
    CONSTANT                        224
    CONSTANT                        225
    CONSTANT                        226
    CONSTANT                        227
    CONSTANT                        228
    CONSTANT                        229
    CONSTANT                        230
    CONSTANT                        231
    CONSTANT                        232
    CONSTANT                        233
    CONSTANT                        234
    CONSTANT                        235
    CONSTANT                        236
    CONSTANT                        237
    CONSTANT                        238
    CONSTANT                        239
    CONSTANT                        240
    CONSTANT                        241
    CONSTANT                        242
    CONSTANT                        243
    CONSTANT                        244
    CONSTANT                        245
    CONSTANT                        246
    CONSTANT                        247
    CONSTANT                        248
    CONSTANT                        249
    CONSTANT                        250
    CONSTANT                        251
    CONSTANT                        252
    CONSTANT                        253
    CONSTANT                        254
    CONSTANT                        255
    CONSTANT                        256

    CONSTANT                        1
    CONSTANT                        2
    CONSTANT                        3
    CONSTANT                        4
    CONSTANT                        5
    CONSTANT                        6
    CONSTANT                        7
    CONSTANT                        8
    CONSTANT                        9
    CONSTANT                        10
    CONSTANT                        11
    CONSTANT                        12
    CONSTANT                        13
    CONSTANT                        14
    CONSTANT                        15
    CONSTANT                        16
    CONSTANT                        17
    CONSTANT                        18
    CONSTANT                        19
    CONSTANT                        20
    CONSTANT                        21
    CONSTANT                        22
    CONSTANT                        23
    CONSTANT                        24
    CONSTANT                        25
    CONSTANT                        26
    CONSTANT                        27
    CONSTANT                        28
    CONSTANT                        29
    CONSTANT                        30
    CONSTANT                        31
    CONSTANT                        32
    CONSTANT                        33
    CONSTANT                        34
    CONSTANT                        35
    CONSTANT                        36
    CONSTANT                        37
    CONSTANT                        38
    CONSTANT                        39
    CONSTANT                        40
    CONSTANT                        41
    CONSTANT                        42
    CONSTANT                        43
    CONSTANT                        44
    CONSTANT                        45
    CONSTANT                        46
    CONSTANT                        47
    CONSTANT                        48
    CONSTANT                        49
    CONSTANT                        50
    CONSTANT                        51
    CONSTANT                        52
    CONSTANT                        53
    CONSTANT                        54
    CONSTANT                        55
    CONSTANT                        56
    CONSTANT                        57
    CONSTANT                        58
    CONSTANT                        59
    CONSTANT                        60
    CONSTANT                        61
    CONSTANT                        62
    CONSTANT                        63
    CONSTANT                        64
    CONSTANT                        65
    CONSTANT                        66
    CONSTANT                        67
    CONSTANT                        68
    CONSTANT                        69
    CONSTANT                        70
    CONSTANT                        71
    CONSTANT                        72
    CONSTANT                        73
    CONSTANT                        74
    CONSTANT                        75
    CONSTANT                        76
    CONSTANT                        77
    CONSTANT                        78
    CONSTANT                        79
    CONSTANT                        80
    CONSTANT                        81
    CONSTANT                        82
    CONSTANT                        83
    CONSTANT                        84
    CONSTANT                        85
    CONSTANT                        86
    CONSTANT                        87
    CONSTANT                        88
    CONSTANT                        89
    CONSTANT                        90
    CONSTANT                        91
    CONSTANT                        92
    CONSTANT                        93
    CONSTANT                        94
    CONSTANT                        95
    CONSTANT                        96
    CONSTANT                        97
    CONSTANT                        98
    CONSTANT                        99
    CONSTANT                        100
    CONSTANT                        101
    CONSTANT                        102
    CONSTANT                        103
    CONSTANT                        104
    CONSTANT                        105
    CONSTANT                        106
    CONSTANT                        107
    CONSTANT                        108
    CONSTANT                        109
    CONSTANT                        110
    CONSTANT                        111
    CONSTANT                        112
    CONSTANT                        113
    CONSTANT                        114
    CONSTANT                        115
    CONSTANT                        116
    CONSTANT                        117
    CONSTANT                        118
    CONSTANT                        119
    CONSTANT                        120
    CONSTANT                        121
    CONSTANT                        122
    CONSTANT                        123
    CONSTANT                        124
    CONSTANT                        125
    CONSTANT                        126
    CONSTANT                        127
    CONSTANT                        128
    CONSTANT                        129
    CONSTANT                        130
    CONSTANT                        131
    CONSTANT                        132
    CONSTANT                        133
    CONSTANT                        134
    CONSTANT                        135
    CONSTANT                        136
    CONSTANT                        137
    CONSTANT                        138
    CONSTANT                        139
    CONSTANT                        140
    CONSTANT                        141
    CONSTANT                        142
    CONSTANT                        143
    CONSTANT                        144
    CONSTANT                        145
    CONSTANT                        146
    CONSTANT                        147
    CONSTANT                        148
    CONSTANT                        149
    CONSTANT                        150
    CONSTANT                        151
    CONSTANT                        152
    CONSTANT                        153
    CONSTANT                        154
    CONSTANT                        155
    CONSTANT                        156
    CONSTANT                        157
    CONSTANT                        158
    CONSTANT                        159
    CONSTANT                        160
    CONSTANT                        161
    CONSTANT                        162
    CONSTANT                        163
    CONSTANT                        164
    CONSTANT                        165
    CONSTANT                        166
    CONSTANT                        167
    CONSTANT                        168
    CONSTANT                        169
    CONSTANT                        170
    CONSTANT                        171
    CONSTANT                        172
    CONSTANT                        173
    CONSTANT                        174
    CONSTANT                        175
    CONSTANT                        176
    CONSTANT                        177
    CONSTANT                        178
    CONSTANT                        179
    CONSTANT                        180
    CONSTANT                        181
    CONSTANT                        182
    CONSTANT                        183
    CONSTANT                        184
    CONSTANT                        185
    CONSTANT                        186
    CONSTANT                        187
    CONSTANT                        188
    CONSTANT                        189
    CONSTANT                        190
    CONSTANT                        191
    CONSTANT                        192
    CONSTANT                        193
    CONSTANT                        194
    CONSTANT                        195
    CONSTANT                        196
    CONSTANT                        197
    CONSTANT                        198
    CONSTANT                        199
    CONSTANT                        200
    CONSTANT                        201
    CONSTANT                        202
    CONSTANT                        203
    CONSTANT                        204
    CONSTANT                        205
    CONSTANT                        206
    CONSTANT                        207
    CONSTANT                        208
    CONSTANT                        209
    CONSTANT                        210
    CONSTANT                        211
    CONSTANT                        212
    CONSTANT                        213
    CONSTANT                        214
    CONSTANT                        215
    CONSTANT                        216
    CONSTANT                        217
    CONSTANT                        218
    CONSTANT                        219
    CONSTANT                        220
    CONSTANT                        221
    CONSTANT                        222
    CONSTANT                        223
    CONSTANT                        224
    CONSTANT                        225
    CONSTANT                        226
    CONSTANT                        227
    CONSTANT                        228
    CONSTANT                        229
    CONSTANT                        230
    CONSTANT                        231
    CONSTANT                        232
    CONSTANT                        233
    CONSTANT                        234
    CONSTANT                        235
    CONSTANT                        236
    CONSTANT                        237
    CONSTANT                        238
    CONSTANT                        239
    CONSTANT                        240
    CONSTANT                        241
    CONSTANT                        242
    CONSTANT                        243
    CONSTANT                        244
    CONSTANT                        245
    CONSTANT                        246
    CONSTANT                        247
    CONSTANT                        248
    CONSTANT                        249
    CONSTANT                        250
    CONSTANT                        251
    CONSTANT                        252
    CONSTANT                        253
    CONSTANT                        254
    CONSTANT                        255
    CONSTANT                        256
"""
expected_stderr_1 = """
    Statement failed, SQLSTATE = 54011
    Dynamic SQL Error
    -SQL error code = -104
    -Invalid command
    -Cannot have more than 255 items in DISTINCT / UNION DISTINCT list
"""

@pytest.mark.version('>=4.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.expected_stderr = expected_stderr_1
    act_1.execute()
    assert act_1.clean_stderr == act_1.clean_expected_stderr
    assert act_1.clean_stdout == act_1.clean_expected_stdout

