#coding:utf-8
#
# id:           functional.arno.optimizer.opt_inner_join_05
# title:        INNER JOIN join order LIKE and STARTING WITH
# decription:   LIKE and STARTING WITH should also be used for determing join order.
# tracker_id:   
# min_versions: []
# versions:     2.0
# qmid:         functional.arno.optimizer.opt_inner_join_05

import pytest
from firebird.qa import db_factory, isql_act, Action

# version: 2.0
# resources: None

substitutions_1 = []

init_script_1 = """CREATE TABLE Countries (
  CountryID INTEGER NOT NULL,
  CountryName VARCHAR(50),
  ISO3166_1_A2 CHAR(2)
);

CREATE TABLE Relations (
  RelationID INTEGER,
  RelationName VARCHAR(35),
  Location VARCHAR(50),
  Address VARCHAR(50),
  ZipCode VARCHAR(12),
  CountryID INTEGER
);

COMMIT;

/*
  COUNTRIES
  ---------
  Exporting all rows
*/
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (1, 'AFGHANISTAN', 'AF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (2, 'ALBANIA', 'AL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (3, 'ALGERIA', 'DZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (4, 'AMERICAN SAMOA', 'AS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (5, 'ANDORRA', 'AD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (6, 'ANGOLA', 'AO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (7, 'ANGUILLA', 'AI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (8, 'ANTARCTICA', 'AQ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (9, 'ANTIGUA AND BARBUDA', 'AG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (10, 'ARGENTINA', 'AR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (11, 'ARMENIA', 'AM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (12, 'ARUBA', 'AW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (13, 'AUSTRALIA', 'AU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (14, 'AUSTRIA', 'AT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (15, 'AZERBAIJAN', 'AZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (16, 'BAHAMAS', 'BS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (17, 'BAHRAIN', 'BH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (18, 'BANGLADESH', 'BD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (19, 'BARBADOS', 'BB');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (20, 'BELARUS', 'BY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (21, 'BELGIUM', 'BE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (22, 'BELIZE', 'BZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (23, 'BENIN', 'BJ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (24, 'BERMUDA', 'BM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (25, 'BHUTAN', 'BT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (26, 'BOLIVIA', 'BO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (27, 'BOSNIA AND HERZEGOVINA', 'BA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (28, 'BOTSWANA', 'BW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (29, 'BOUVET ISLAND', 'BV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (30, 'BRAZIL', 'BR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (31, 'BRITISH INDIAN OCEAN TERRITORY', 'IO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (32, 'BRUNEI DARUSSALAM', 'BN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (33, 'BULGARIA', 'BG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (34, 'BURKINA FASO', 'BF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (35, 'BURUNDI', 'BI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (36, 'CAMBODIA', 'KH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (37, 'CAMEROON', 'CM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (38, 'CANADA', 'CA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (39, 'CAPE VERDE', 'CV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (40, 'CAYMAN ISLANDS', 'KY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (41, 'CENTRAL AFRICAN REPUBLIC', 'CF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (42, 'CHAD', 'TD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (43, 'CHILE', 'CL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (44, 'CHINA', 'CN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (45, 'CHRISTMAS ISLAND', 'CX');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (46, 'COCOS (KEELING) ISLANDS', 'CC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (47, 'COLOMBIA', 'CO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (48, 'COMOROS', 'KM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (49, 'CONGO', 'CG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (50, 'CONGO, THE DEMOCRATIC REPUBLIC OF THE', 'CD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (51, 'COOK ISLANDS', 'CK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (52, 'COSTA RICA', 'CR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (53, 'COTE D''IVOIRE', 'CI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (54, 'CROATIA', 'HR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (55, 'CUBA', 'CU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (56, 'CYPRUS', 'CY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (57, 'CZECH REPUBLIC', 'CZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (58, 'DENMARK', 'DK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (59, 'DJIBOUTI', 'DJ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (60, 'DOMINICA', 'DM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (61, 'DOMINICAN REPUBLIC', 'DO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (62, 'EAST TIMOR', 'TL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (63, 'ECUADOR', 'EC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (64, 'EGYPT', 'EG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (65, 'EL SALVADOR', 'SV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (66, 'EQUATORIAL GUINEA', 'GQ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (67, 'ERITREA', 'ER');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (68, 'ESTONIA', 'EE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (69, 'ETHIOPIA', 'ET');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (70, 'FALKLAND ISLANDS (MALVINAS)', 'FK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (71, 'FAROE ISLANDS', 'FO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (72, 'FIJI', 'FJ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (73, 'FINLAND', 'FI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (74, 'FRANCE', 'FR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (75, 'FRENCH GUIANA', 'GF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (76, 'FRENCH POLYNESIA', 'PF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (77, 'FRENCH SOUTHERN TERRITORIES', 'TF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (78, 'GABON', 'GA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (79, 'GAMBIA', 'GM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (80, 'GEORGIA', 'GE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (81, 'GERMANY', 'DE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (82, 'GHANA', 'GH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (83, 'GIBRALTAR', 'GI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (84, 'GREECE', 'GR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (85, 'GREENLAND', 'GL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (86, 'GRENADA', 'GD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (87, 'GUADELOUPE', 'GP');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (88, 'GUAM', 'GU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (89, 'GUATEMALA', 'GT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (90, 'GUINEA', 'GN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (91, 'GUINEA-BISSAU', 'GW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (92, 'GUYANA', 'GY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (93, 'HAITI', 'HT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (94, 'HEARD ISLAND AND MCDONALD ISLANDS', 'HM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (95, 'HOLY SEE (VATICAN CITY STATE)', 'VA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (96, 'HONDURAS', 'HN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (97, 'HONG KONG', 'HK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (98, 'HUNGARY', 'HU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (99, 'ICELAND', 'IS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (100, 'INDIA', 'IN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (101, 'INDONESIA', 'ID');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (102, 'IRAN, ISLAMIC REPUBLIC OF', 'IR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (103, 'IRAQ', 'IQ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (104, 'IRELAND', 'IE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (105, 'ISRAEL', 'IL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (106, 'ITALY', 'IT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (107, 'JAMAICA', 'JM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (108, 'JAPAN', 'JP');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (109, 'JORDAN', 'JO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (110, 'KAZAKHSTAN', 'KZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (111, 'KENYA', 'KE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (112, 'KIRIBATI', 'KI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (113, 'KOREA, DEMOCRATIC PEOPLE''S REPUBLIC OF', 'KP');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (114, 'KOREA, REPUBLIC OF', 'KR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (115, 'KUWAIT', 'KW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (116, 'KYRGYZSTAN', 'KG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (117, 'LAO PEOPLE''S DEMOCRATIC REPUBLIC', 'LA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (118, 'LATVIA', 'LV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (119, 'LEBANON', 'LB');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (120, 'LESOTHO', 'LS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (121, 'LIBERIA', 'LR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (122, 'LIBYAN ARAB JAMAHIRIYA', 'LY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (123, 'LIECHTENSTEIN', 'LI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (124, 'LITHUANIA', 'LT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (125, 'LUXEMBOURG', 'LU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (126, 'MACAO', 'MO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (127, 'MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF', 'MK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (128, 'MADAGASCAR', 'MG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (129, 'MALAWI', 'MW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (130, 'MALAYSIA', 'MY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (131, 'MALDIVES', 'MV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (132, 'MALI', 'ML');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (133, 'MALTA', 'MT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (134, 'MARSHALL ISLANDS', 'MH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (135, 'MARTINIQUE', 'MQ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (136, 'MAURITANIA', 'MR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (137, 'MAURITIUS', 'MU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (138, 'MAYOTTE', 'YT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (139, 'MEXICO', 'MX');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (140, 'MICRONESIA, FEDERATED STATES OF', 'FM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (141, 'MOLDOVA, REPUBLIC OF', 'MD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (142, 'MONACO', 'MC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (143, 'MONGOLIA', 'MN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (144, 'MONTSERRAT', 'MS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (145, 'MOROCCO', 'MA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (146, 'MOZAMBIQUE', 'MZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (147, 'MYANMAR', 'MM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (148, 'NAMIBIA', 'NA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (149, 'NAURU', 'NR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (150, 'NEPAL', 'NP');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (151, 'NETHERLANDS', 'NL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (152, 'NETHERLANDS ANTILLES', 'AN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (153, 'NEW CALEDONIA', 'NC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (154, 'NEW ZEALAND', 'NZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (155, 'NICARAGUA', 'NI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (156, 'NIGER', 'NE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (157, 'NIGERIA', 'NG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (158, 'NIUE', 'NU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (159, 'NORFOLK ISLAND', 'NF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (160, 'NORTHERN MARIANA ISLANDS', 'MP');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (161, 'NORWAY', 'NO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (162, 'OMAN', 'OM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (163, 'PAKISTAN', 'PK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (164, 'PALAU', 'PW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (165, 'PALESTINIAN TERRITORY, OCCUPIED', 'PS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (166, 'PANAMA', 'PA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (167, 'PAPUA NEW GUINEA', 'PG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (168, 'PARAGUAY', 'PY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (169, 'PERU', 'PE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (170, 'PHILIPPINES', 'PH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (171, 'PITCAIRN', 'PN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (172, 'POLAND', 'PL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (173, 'PORTUGAL', 'PT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (174, 'PUERTO RICO', 'PR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (175, 'QATAR', 'QA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (176, 'REUNION', 'RE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (177, 'ROMANIA', 'RO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (178, 'RUSSIAN FEDERATION', 'RU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (179, 'RWANDA', 'RW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (180, 'SAINT HELENA', 'SH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (181, 'SAINT KITTS AND NEVIS', 'KN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (182, 'SAINT LUCIA', 'LC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (183, 'SAINT PIERRE AND MIQUELON', 'PM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (184, 'SAINT VINCENT AND THE GRENADINES', 'VC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (185, 'SAMOA', 'WS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (186, 'SAN MARINO', 'SM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (187, 'SAO TOME AND PRINCIPE', 'ST');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (188, 'SAUDI ARABIA', 'SA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (189, 'SENEGAL', 'SN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (190, 'SEYCHELLES', 'SC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (191, 'SIERRA LEONE', 'SL');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (192, 'SINGAPORE', 'SG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (193, 'SLOVAKIA', 'SK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (194, 'SLOVENIA', 'SI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (195, 'SOLOMON ISLANDS', 'SB');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (196, 'SOMALIA', 'SO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (197, 'SOUTH AFRICA', 'ZA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (198, 'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS', 'GS');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (199, 'SPAIN', 'ES');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (200, 'SRI LANKA', 'LK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (201, 'SUDAN', 'SD');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (202, 'SURINAME', 'SR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (203, 'SVALBARD AND JAN MAYEN', 'SJ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (204, 'SWAZILAND', 'SZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (205, 'SWEDEN', 'SE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (206, 'SWITZERLAND', 'CH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (207, 'SYRIAN ARAB REPUBLIC', 'SY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (208, 'TAIWAN, PROVINCE OF CHINA', 'TW');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (209, 'TAJIKISTAN', 'TJ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (210, 'TANZANIA, UNITED REPUBLIC OF', 'TZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (211, 'THAILAND', 'TH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (212, 'TOGO', 'TG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (213, 'TOKELAU', 'TK');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (214, 'TONGA', 'TO');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (215, 'TRINIDAD AND TOBAGO', 'TT');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (216, 'TUNISIA', 'TN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (217, 'TURKEY', 'TR');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (218, 'TURKMENISTAN', 'TM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (219, 'TURKS AND CAICOS ISLANDS', 'TC');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (220, 'TUVALU', 'TV');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (221, 'UGANDA', 'UG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (222, 'UKRAINE', 'UA');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (223, 'UNITED ARAB EMIRATES', 'AE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (224, 'UNITED KINGDOM', 'GB');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (225, 'UNITED STATES', 'US');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (226, 'UNITED STATES MINOR OUTLYING ISLANDS', 'UM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (227, 'URUGUAY', 'UY');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (228, 'UZBEKISTAN', 'UZ');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (229, 'VANUATU', 'VU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (230, 'VENEZUELA', 'VE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (231, 'VIET NAM', 'VN');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (232, 'VIRGIN ISLANDS, BRITISH', 'VG');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (233, 'VIRGIN ISLANDS, U.S.', 'VI');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (234, 'WALLIS AND FUTUNA', 'WF');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (235, 'WESTERN SAHARA', 'EH');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (236, 'YEMEN', 'YE');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (237, 'YUGOSLAVIA', 'YU');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (238, 'ZAMBIA', 'ZM');
INSERT INTO COUNTRIES(COUNTRYID, COUNTRYNAME, ISO3166_1_A2) VALUES (239, 'ZIMBABWE', 'ZW');

/*
  RELATIONS
  ---------
  Exporting all rows
*/
INSERT INTO RELATIONS(RELATIONID, RELATIONNAME, LOCATION, ADDRESS, ZIPCODE, COUNTRYID) VALUES (101, 'University Amsterdam', 'Amsterdam', 'De Boelelaan 1081A', '1081 HV', 151);
INSERT INTO RELATIONS(RELATIONID, RELATIONNAME, LOCATION, ADDRESS, ZIPCODE, COUNTRYID) VALUES (102, 'University Brussel', 'ELSENE', 'Pleinlaan 2', '1050', 21);
INSERT INTO RELATIONS(RELATIONID, RELATIONNAME, LOCATION, ADDRESS, ZIPCODE, COUNTRYID) VALUES (103, 'University Leiden', 'Leiden', 'Niels Bohrweg 1', '2333 CA', 151);
INSERT INTO RELATIONS(RELATIONID, RELATIONNAME, LOCATION, ADDRESS, ZIPCODE, COUNTRYID) VALUES (104, 'University Delft', 'Delft', 'Julianalaan 134', '2628 BL', 151);

COMMIT;

/* Normally these indexes are created by the primary/foreign keys, but we don't want to rely on them for this test */

CREATE UNIQUE ASC INDEX PK_Countries ON Countries (CountryID);
CREATE UNIQUE ASC INDEX PK_Relations ON Relations (RelationID);
CREATE ASC INDEX FK_Relations_Countries ON Relations (CountryID);
CREATE UNIQUE ASC INDEX I_RelationName ON Relations (RelationName);
CREATE UNIQUE ASC INDEX I_CountryName ON Countries (CountryName);


COMMIT;
"""

db_1 = db_factory(sql_dialect=3, init=init_script_1)

test_script_1 = """SET PLAN ON;
SELECT
  r.RelationName,
  c.CountryName
FROM
  RELATIONS r
  JOIN COUNTRIES c ON (c.COUNTRYID = r.COUNTRYID)
WHERE
  c.CountryName LIKE 'N%'
ORDER BY
r.RelationName DESC;"""

act_1 = isql_act('db_1', test_script_1, substitutions=substitutions_1)

expected_stdout_1 = """PLAN SORT (JOIN (C INDEX (I_COUNTRYNAME), R INDEX (FK_RELATIONS_COUNTRIES)))

RELATIONNAME                        COUNTRYNAME
=================================== ==================================================

University Leiden                   NETHERLANDS
University Delft                    NETHERLANDS
University Amsterdam                NETHERLANDS"""

@pytest.mark.version('>=2.0')
def test_1(act_1: Action):
    act_1.expected_stdout = expected_stdout_1
    act_1.execute()
    assert act_1.clean_stdout == act_1.clean_expected_stdout

