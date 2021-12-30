#coding:utf-8
#
# id:           functional.util.gbak_zip
# title:        gbak utility: check ability to use -ZIP command switch when create backup
# decription:   
#                   We create some metadata, extracte them into .SQL script, make backup with '-ZIP' switch.
#               	Then we try to restore this DB, validate it and again extract metadata with saving to new .SQL.
#               	Comparing old and new metadata must show that they are equal.
#               	All STDERR logs must be empty. Logs of backup, restore and validation must also be empty.
#               	To make test more complex non-ascii metadata are used. 
#               	
#                   Checked on:
#               		4.0.0.1694 SS: 4.921s.
#               		4.0.0.1691 CS: 7.796s. 
#               		
#               	NOTE. Command key '-zip' does not convert .fbk to .zip format; rather it just produces .fbk
#               	which content is compressed using LZ-algorothm and sign (flag) that this was done.
#               	
#               	Beside of that, database is encrypted before backup using IBSurgeon Demo Encryption package
#                   ( https://ib-aid.com/download-demo-firebird-encryption-plugin/ ; https://ib-aid.com/download/crypt/CryptTest.zip )
#                   License file plugins\\dbcrypt.conf with unlimited expiration was provided by IBSurgeon to Firebird Foundation (FF).
#                   This file was preliminary stored in FF Test machine.
#                   Test assumes that this file and all neccessary libraries already were stored into FB_HOME and %FB_HOME%\\plugins.
#               
#                   Anyone who wants to run this test on his own machine must
#                   1) download https://ib-aid.com/download/crypt/CryptTest.zip AND 
#                   2) PURCHASE LICENSE and get from IBSurgeon file plugins\\dbcrypt.conf with apropriate expiration date and other info.
#                   
#                   ################################################ ! ! !    N O T E    ! ! ! ##############################################
#                   FF tests storage (aka "fbt-repo") does not (and will not) contain any license file for IBSurgeon Demo Encryption package!
#                   #########################################################################################################################
#                
# tracker_id:   
# min_versions: ['4.0']
# versions:     4.0
# qmid:         None

import pytest
from firebird.qa import db_factory, python_act, Action

# version: 4.0
# resources: None

substitutions_1 = [('[ \t]+', ' ')]

init_script_1 = """"""

db_1 = db_factory(charset='UTF8', sql_dialect=3, init=init_script_1)

# test_script_1
#---
# import os
#  import time
#  import difflib
#  import subprocess
#  from fdb import services
#  
#  os.environ["ISC_USER"] = user_name
#  os.environ["ISC_PASSWORD"] = user_password
#  
#  this_db = db_conn.database_name
#  tmpfbk='$(DATABASE_LOCATION)'+'tmp_zipped_backup.fbk'
#  tmpfdb='$(DATABASE_LOCATION)'+'tmp_zipped_restore.fdb'
#  
#  # 27.02.2021.
#  # Name of encryption plugin depends on OS:
#  # * for Windows we (currently) use plugin by IBSurgeon, its name is 'dbcrypt';
#  #      later it can be replaced with built-in plugin 'fbSampleDbCrypt'
#  #      but currently it is included only in FB 4.x builds (not in FB 3.x).
#  #      Discussed tih Dimitr, Alex, Vlad, letters since: 08-feb-2021 00:22
#  #      "Windows-distributive FB 3.x: it is desired to see sub-folder 'examples\\prebuild' with files for encryption, like it is in FB 4.x
#  #      *** DEFERRED ***
#  # * for Linux we use:
#  #   ** 'DbCrypt_example' for FB 3.x
#  #   ** 'fbSampleDbCrypt' for FB 4.x+
#  #
#  PLUGIN_NAME = 'dbcrypt' if os.name == 'nt' else ( '"DbCrypt_example"' if db_conn.engine_version < 4 else '"fbSampleDbCrypt"' )
#  
#  ################################################
#  ###    e n c r y p t      d a t a b a s e    ###
#  ################################################
#  runProgram('isql', [ dsn ], 'alter database encrypt with %(PLUGIN_NAME)s key Red;' % locals())
#  time.sleep(1)
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
#  #-------------------------------------------
#  sql_ddl='''
#      set bail on;
#  
#  	-- ######################################################
#  	-- ################   C O R E    0 9 8 6    #############
#  	-- ######################################################
#  
#      create collation "Циферки" for utf8 from unicode case insensitive 'NUMERIC-SORT=1';
#      create collation "Испания" for iso8859_1 from es_es_ci_ai 'SPECIALS-FIRST=1';;
#      commit;
#  	
#      create domain "ИД'шники" int;
#      create domain "Группы" varchar(30) check( value in ('Электрика', 'Ходовая', 'Арматурка', 'Кузовщина') );
#      create domain "Артикулы" varchar(12) character set utf8 check( value = upper(value) ) 
#      collate "Циферки" -- enabled since core-5220 was fixed (30.04.2016)
#      ;
#      create domain "Комрады" varchar(40) character set iso8859_1 
#      collate "Испания" -- enabled since core-5220 was fixed (30.04.2016)
#      ;
#      create domain "Кол-во" numeric(12,3) not null;
#  
#      create sequence generilka;
#      create sequence "Генерилка";
#  
#      --create role "манагер";
#      --create role "начсклд";
#  
#      -- TEMPLY COMMENTED UNTIL CORE-5209 IS OPEN:
#      -- ISQL -X ignores connection charset for text of EXCEPTION message (restoring it in initial charset when exception was created)
#      --recreate exception "Невзлет" 'Запись обломалась, ваши не пляшут. Но не стесняйтесь и обязательно заходите еще, мы всегда рады видеть вас. До скорой встречи, товарищ!';
#      commit;
#  	
#      -------------------------------------------------
#      recreate table "склад" (
#           "ИД'шник" "ИД'шники"
#          ,"Откудова" "Группы"
#          ,"Номенклатура" "Артикулы"
#          ,"ИД'родителя" "ИД'шники"
#          ,"сколько там" "Кол-во"
#          ,constraint "ПК-ИД'шник" primary key ("ИД'шник") using index "склад_ПК"
#          ,constraint "ФК-на-родока" foreign key("ИД'родителя") references "склад" ("ИД'шник")  using index "склад_ФК"
#          ,constraint "остаток >=0" check ("сколько там" >= 0)
#      );
#  
#      recreate view "Электрика"("ид изделия", "Название", "Запас") as
#      select 
#           "ИД'шник" 
#          ,"Номенклатура"
#          ,"сколько там"
#      from "склад"
#      where "Откудова" = 'Электрика'
#      ;
#  
#      set term ^;
#      create or alter trigger "склад би" for "склад" active before insert as
#      begin
#          --new."ИД'шник" = coalesce( new."ИД'шник", gen_id(generilka, 1) );
#          -- not avail up to 2.5.6: 
#          new."ИД'шник" = coalesce( new."ИД'шник", gen_id("Генерилка", 1) );
#      end
#      ^
#  
#      create or alter procedure "Доб на склад"(
#           "Откудова" varchar(30)
#          ,"Номенклатура" varchar(30)
#          ,"ИД'родителя" int
#          ,"сколько там" numeric(12,3)
#      ) returns (
#          "код возврата" int
#      ) as
#      begin
#          insert into "склад"(
#               "Откудова"
#              ,"Номенклатура"
#              ,"ИД'родителя" 
#              ,"сколько там"
#          ) values (
#               :"Откудова"
#              ,:"Номенклатура"
#              ,:"ИД'родителя" 
#              ,:"сколько там"
#          );
#          
#      end
#      ^
#      create or alter procedure "Удалить" as
#      begin
#       /*
#              Антон Павлович Чехов. Каштанка
#  
#              1. Дурное поведение
#  
#               Молодая рыжая собака - помесь такса с дворняжкой - очень похожая мордой
#          на лисицу, бегала взад и вперед по тротуару  и  беспокойно  оглядывалась  по
#          сторонам. Изредка она останавливалась и, плача, приподнимая то одну  озябшую
#          лапу, то другую, старалась дать себе отчет: как это могло случиться, что она
#          заблудилась?
#       */
#      end
#      ^
#      set term ;^
#  
#      --grant select on "склад" to "манагер";
#      --grant select, insert, update, delete on "склад" to "начсклд";
#  
#      comment on sequence "Генерилка" is 'Генератор простых идей';
#      comment on table "склад" is 'Это всё, что мы сейчас имеем в наличии';
#      comment on view "Электрика" is 'Не суй пальцы в розетку, будет бо-бо!';
#      comment on procedure "Доб на склад" is 'Процедурка добавления изделия на склад';
#      comment on parameter "Доб на склад"."Откудова" is 'Группа изделия, которое собираемся добавить';
#  
#      comment on parameter "Доб на склад"."ИД'родителя"  is '
#          Федор Михайлович Достоевский
#  
#          Преступление и наказание
#  
#          Роман в шести частях с эпилогом
#            
#  
#          Часть первая
#  
#          I
#         В начале июля, в чрезвычайно жаркое время, под вечер, один молодой человек вышел из своей каморки, которую нанимал от жильцов в С -- м переулке, на улицу и медленно, как бы в нерешимости, отправился к К -- ну мосту. 
#         Он благополучно избегнул встречи с своею хозяйкой на лестнице. Каморка его приходилась под самою кровлей высокого пятиэтажного дома и походила более на шкаф, чем на квартиру. Квартирная же хозяйка его, у которой он нанимал эту каморку с обедом и прислугой, помещалась одною лестницей ниже, в отдельной квартире, и каждый раз, при выходе на улицу, ему непременно надо было проходить мимо хозяйкиной кухни, почти всегда настежь отворенной на лестницу. И каждый раз молодой человек, проходя мимо, чувствовал какое-то болезненное и трусливое ощущение, которого стыдился и от которого морщился. Он был должен кругом хозяйке и боялся с нею встретиться. 
#         Не то чтоб он был так труслив и забит, совсем даже напротив; но с некоторого времени он был в раздражительном и напряженном состоянии, похожем на ипохондрию. Он до того углубился в себя и уединился от всех, что боялся даже всякой встречи, не только встречи с хозяйкой. Он был задавлен бедностью; но даже стесненное положение перестало в последнее время тяготить его. Насущными делами своими он совсем перестал и не хотел заниматься. Никакой хозяйки, в сущности, он не боялся, что бы та ни замышляла против него. Но останавливаться на лестнице, слушать всякий вздор про всю эту обыденную дребедень, до которой ему нет никакого дела, все эти приставания о платеже, угрозы, жалобы, и при этом самому изворачиваться, извиняться, лгать, -- нет уж, лучше проскользнуть как-нибудь кошкой по лестнице и улизнуть, чтобы никто не видал. 
#         Впрочем, на этот раз страх встречи с своею кредиторшей даже его самого поразил по выходе на улицу. 
#         "На какое дело хочу покуситься и в то же время каких пустяков боюсь! -- подумал он с странною улыбкой. -- Гм... да... всё в руках человека, и всё-то он мимо носу проносит, единственно от одной трусости... это уж аксиома... Любопытно, чего люди больше всего боятся? Нового шага, нового собственного слова они всего больше боятся... А впрочем, я слишком много болтаю. Оттого и ничего не делаю, что болтаю. Пожалуй, впрочем, и так: оттого болтаю, что ничего не делаю. Это я в этот последний месяц выучился болтать, лежа по целым суткам в углу и думая... о царе Горохе. Ну зачем я теперь иду? Разве я способен на это? Разве это серьезно? Совсем не серьезно. Так, ради фантазии сам себя тешу; игрушки! Да, пожалуй что и игрушки!" 
#         На улице жара стояла страшная, к тому же духота, толкотня, всюду известка, леса, кирпич, пыль и та особенная летняя вонь, столь известная каждому петербуржцу, не имеющему возможности нанять дачу, -- всё это разом неприятно потрясло и без того уже расстроенные нервы юноши. Нестерпимая же вонь из распивочных, которых в этой части города особенное множество, и пьяные, поминутно попадавшиеся, несмотря на буднее время, довершили отвратительный и грустный колорит картины. Чувство глубочайшего омерзения мелькнуло на миг в тонких чертах молодого человека. Кстати, он был замечательно хорош собою, с прекрасными темными глазами, темно-рус, ростом выше среднего, тонок и строен. Но скоро он впал как бы в глубокую задумчивость, даже, вернее сказать, как бы в какое-то забытье, и пошел, уже не замечая окружающего, да и не желая его замечать. Изредка только бормотал он что-то про себя, от своей привычки к монологам, в которой он сейчас сам себе признался. В эту же минуту он и сам сознавал, что мысли его порою мешаются и что он очень слаб: второй день как уж он почти совсем ничего не ел. 
#         Он был до того худо одет, что иной, даже и привычный человек, посовестился бы днем выходить в таких лохмотьях на улицу. Впрочем, квартал был таков, что костюмом здесь было трудно кого-нибудь удивить. Близость Сенной, обилие известных заведений и, по преимуществу, цеховое и ремесленное население, скученное в этих серединных петербургских улицах и переулках, пестрили иногда общую панораму такими субъектами, что странно было бы и удивляться при встрече с иною фигурой. Но столько злобного презрения уже накопилось в душе молодого человека, что, несмотря на всю свою, иногда очень молодую, щекотливость, он менее всего совестился своих лохмотьев на улице. Другое дело при встрече с иными знакомыми или с прежними товарищами, с которыми вообще он не любил встречаться... А между тем, когда один пьяный, которого неизвестно почему и куда провозили в это время по улице в огромной телеге, запряженной огромною ломовою лошадью, крикнул ему вдруг, проезжая: "Эй ты, немецкий шляпник!" -- и заорал во всё горло, указывая на него рукой, -- молодой человек вдруг остановился и судорожно схватился за свою шляпу. Шляпа эта была высокая, круглая, циммермановская, но вся уже изношенная, совсем рыжая, вся в дырах и пятнах, без полей и самым безобразнейшим углом заломившаяся на сторону. Но не стыд, а совсем другое чувство, похожее даже на испуг, охватило его. 
#         "Я так и знал! -- бормотал он в смущении, -- я так и думал! Это уж всего сквернее! Вот эдакая какая-нибудь глупость, какая-нибудь пошлейшая мелочь, весь замысел может испортить! Да, слишком приметная шляпа... Смешная, потому и приметная... К моим лохмотьям непременно нужна фуражка, хотя бы старый блин какой-нибудь, а не этот урод. Никто таких не носит, за версту заметят, запомнят... главное, потом запомнят, ан и улика. Тут нужно быть как можно неприметнее... Мелочи, мелочи главное!.. Вот эти-то мелочи и губят всегда и всё..." 
#      ';
#  
#      commit;
#  	
#  	
#  	-- ######################################################
#  	-- ################   C O R E    2 2 3 8    #############
#  	-- ######################################################
#      create domain dm_long_utf8 as varchar(8191) character set utf8;
#      create table test (long_text dm_long_utf8, long_descr blob sub_type text character set utf8 );
#      commit;
#      set count on;
#      -- Length of this literal is exact 8191 characters:
#      insert into test(long_text)
#      values(
#          'Kaikki neuvon-antajat ja etevimmät päälliköt ja mollat ja imamit ja kadit ja kaupungin päähenkilöt olivat suuresti hämmästyksissään. Hänen tunnettu hurskautensa vaati kaikkia äänettömyyteen, sillä välin kuin hän itse lausui pitkän rukouksen, pyytäen Allah''ta ja Profeettaa hämmentämään kaikkia häväiseviä Juutalaisia ja uskottomia ja vuodattamaan totuuden sanoja jumalisten ihmisten suuhun. Ja nyt kunnian-arvoisa sheiki kutsui esiin kaikki todistajat David Alroy''ta vastaan. Heti Kisloch, Kurdilainen, joka oli koroitettu Bagdadin kadiksi, astui esiin, veti sametti-kukkarostansa paperikääryn ja luki semmoisen todistuksen, jossa arvoisa Kisloch vakuutti, että hän ensin tutustui vangin, David Alroy''n kanssa joissakin erämaan raunioissa -- muutamain rosvojen pesässä, joita Alroy johdatti; että hän, Kisloch, oli rehellinen kauppias ja että nämät konnat olivat ryöstäneet hänen karavaninsa ja hän itse joutunut vankeuteen; että hänen vankeutensa toisena yönä Alroy oli ilmestynyt hänen eteensä leijonan muodossa ja kolmantena tuimasilmäisenä härkänä; että hänen oli tapa alinomaa muuttaa itsensä; että hän usein nosti henkiä; että viimein eräänä kauheana yönä Eblis itse tuli suurella juhlasaatolla ja antoi Alroy''lle Salomonin, Davidin pojan valtikan; ja että tämä seuraavana päivänä kohotti lippunsa ja kohta sen jälkeen kukisti Hassan Subah''n ja tämän Seldshukit useitten hirmuisten paholaisten silminnähtävällä avulla.  Kalidaan, Indialaisen, Guebriläisen ja Neekerin ja muutamien muitten saman hengen lapsien todistukset vetivät täysin määrin vertoja Kisloch Kurdilaisen uhkealle kertomukselle. Hebrealaisen valloittajan vastustamaton menestys oli kieltämättömällä tavalla selitetty, Mahomettilaisten aseitten kunnia ja Moslemin uskon puhtaus olivat asetetut jälleen entiseen loistoonsa ja saastuttamattomaan maineesensa. Todeksi saatiin, että David Alroy oli Ebliin lapsi, noitamies, taikakalujen ja myrkkyjen käyttäjä. Kansa kuunteli kauhulla ja harmilla. He olisivat tunkeneet vartiaväen läpitse ja repineet hänet kappaleiksi, jolleivät olisi pelänneet Karamanialaisten sotatapparoita. Niin he lohduttivat mieltänsä sillä, että he ennen pitkää saisivat nähdä hänen kidutuksensa.  Bagdadin kadi kumarsi Karamanian kuningasta ja kuiskasi soveliaan matkan päästä jotakin kuninkaalliseen korvaan. Torvet kaikkuivat, kuuluttajat vaativat äänettömyyttä ja kuninkaan huulet liikkuivat taas.  "Kuule, oi kansa, ja ole viisas. Pääkadi aikoo nyt lukea kuninkaallisen prinsessan Schirenen, noiturin etevimmän uhrin todistuksen."  Ja todistus luettiin, joka vakuutti, että David Alroy omisti ja kantoi lähinnä sydäntänsä erästä talismania, jonka Eblis oli antanut hänelle ja jonka voima oli niin suuri, että, jos sitä kerta painettiin naisen rintaa vastaan, tämä ei enää voinut hallita tahtoansa. Tämmöinen kova onni oli kohdannut oikeauskoisten hallitsian tytärtä.  "Onko siinä niin kirjoitettu?" vanki kysyi.  "On", kadi vastasi, "ja sen alla on vielä prinsessan kuninkaallinen allekirjoitus."  "Se on väärennetty."  Karamanian kuningas kavahti valta-istuimeltansa ja oli vihoissansa astumallaan sen portaita alas. Hänen kasvonsa olivat veripunaiset, hänen partansa kuin tulen liekki. Joku lempiministeri rohkeni vienosti pidättää häntä hänen kuninkaallisesta vaipastansa.  "Tapa paikalla pois se koira", Karamanian kuningas mutisi.  "Prinsessa on itse täällä", lausui kadi, "todistamassa niitä noitakeinoja, joitten alaisena hän oli, vaan joitten vaikutuksesta hän nyt Allah''n ja Profeetan voiman kautta on pääsnyt."  Alroy''ta vävähti!  "Astu esiin, kuninkaallinen prinsessa", kadi sanoi, "ja jos se todistus, jonka kuulit, on perustettu, nosta ylös se kuninkaallinen käsi, joka koristi sen allekirjoituksellaan."  Lähellä valta-istuinta oleva eunukkien joukko teki tilaa; naishaamu, joka oli verhottu hunnulla jalkoihin saakka, astui esiin. Hän nosti ylös kätensä; koko kerääntynyt kansa tuskin hengitti mielenliikutuksesta; eunukkien rivit ummistuivat jälleen; huuto kuului ja hunnustettu haamu katosi.  "Minä odotan kidutuskoneitasi, kuningas", Alroy lausui raskaan surun äänellä. Hänen lujuutensa näytti luopuneen hänestä. Hänen silmänsä olivat luodut maahan. Hän oli nähtävästi vaipunut syvään miettimiseen taikka heittäynyt epätoivoon.  "Valmistakaat seipäät", käski Alp Arslan.  Koko kansan joukkoa värisytti vasten mieltäkin.  Yksi orja lähestyi ja tarjosi paperikääryä Alroy''lle. Hän tunsi Nubialaisen, joka oli Honainin palveluksessa. Hänen entinen ministerinsä ilmoitti hänelle, että hän oli saapuvilla; että ne ehdot, joita hän vankihuoneessa tarjosi, vielä myönnettäisiin; että jos Alroy, jota asiaa hän ei epäillyt ja jota hän rukoili, suostuisi niitä vastaan-ottamaan, hänen tuli pistää paperikäärö poveensa, mutta, jos hän yhä oli taipumaton, jos hänen yhä oli mieletön päätös kuolla hirveä ja häväisevä kuolema, hänen tuli repiä se rikki ja heittää se tanterelle. Silmänräpäyksellä Alroy otti paperikääryn ja repi sen kiivaasti tuhansiin palasiin. Tuulen puuska levitti kappaleet laajalle yliympäri. Alhaiso riiteli näistä David Alroy''n viimeisistä muistoista; ja tämä vähäinen tapaus tuotti paljon hämminkiä.  Tällä välin Neekerit varustivat kidutuksen ja kuoleman koneita.  "Tuon juutalaisen koiran itsepintaisuus tekee minun hulluksi", lausui Karamanian kuningas hovimiehillensä. "Minua haluttaa puhutella häntä vähän, ennenkuin hän kuolee." Lempiministeri pyysi hallitsiaansa olemaan levollisena; mutta kuninkaallinen parta kävi niin punaiseksi, ja kuninkaalliset silmät iskivät niin kauheata tulta, että lempiministerikin lopulta myöntyi.  Torvi kaikkui, kuuluttajat vaativat vaiti-oloa, ja Alp Arslanin ääni eroitettiin jälleen.  "Senkin koira, näetkö sinä, mikä on tarjonasi? Tiedätkö sinä, mikä vartoo sinua sinun herrasi Ebliin asunnoissa? Voiko väärä ylpeys viehättää Juutalaistakin? Eikö elämä ole suloista? Eikö olisi parempi olla minun varvaskenkieni kantaja kuin tulla seivästetyksi?"  "Jalomielinen Alp Arslan", vastasi Alroy ilmeisen ylenkatseen äänellä; "luuletko, että mikään kidutus rasittaa niin, kuin se muisto, että sinä olet voittanut minun?"  "Partani kautta, hän ivaa minua!" Karamanialaisten hallitsia huudahti; "hän tekee kiusaa minulle! Älkäät koskeko vaippaani. Minä tahdon puhua hänen kanssaan. Te ette näe kauemmaksi kuin hunnustettu haukka, te sokean äidin lapset. Se on noita; hänellä on vielä jälellä joku päätaika; hän pelastaa vielä henkensä. Hän lentää ilmaan taikka vaipuu maan sisään. Hän nauraa meidän kidutuksiamme." Karamanian kuningas astui tuota pikaa valta-istuimensa portaita alaspäin; häntä seurasivat hänen lempiministerinsä ja hänen neuvon-antajansa ja hänen etevimmät päällikkönsä ja kadit ja mollat ja imamit ja kaupungin päähenkilöt.  "Sinä noita!" Alp Arslan huudahti, "hävytön noita! halvan äidin halpa poika! koirien koira! niskotteletko sinä meitä vastaan? Kuiskaako herrasi Eblis toivoa sinun korviisi? Nauratko meidän rangaistuksiamme? Aiotko lentää ylös ilmaan? vai painua alas maahan? Niinkö, niinkö?" Hengästyneenä ja vihastansa uupuneena hallitsia vaikeni. Hän repi partaansa ja polki maata rajussa vimmassaan.  "Sinä olet viisaampi kuin neuvon-antajasi, kuningas Arslan; minä en nöyrry sinun edessäsi. Minun Herrani, vaikka hän ei ole Eblis, ei ole hylännyt minua. Minä nauran sinun rangaistuksiasi. Sinun kidutuksiasi minä ylenkatson. Minä sekä vaivun maan sisään että kohoan ilmaan. Tyydytkö nyt vastaukseeni?"  "Partani kautta", huudahti tulistunut Arslan, "minä tyydyn vastaukseesi. Pelastakoon Eblis sinut, jos hän voi;" ja Karamanian kuningas, Aasian mainioin miekan piteliä veti säilänsä, ikäänkuin salaman, tupesta ja silpaisi yhdellä säväyksellä Alroy''lta pään. Se kaatui, vaan, kun se kaatui, riemuitsevan pilkan hymy näytti vivahtelevan sankarin kylmenevillä kasvoilla ja kysyvän hänen vihollisiltansa: "missä kaikki teidän kidutuksenne nyt ovat?" Do Dzieci Gołąbki i Dziewczynka Dziecię i Koza Wróbel i Jaskółka Osieł i Chłopczyk Nieposłuszny Zajączek Kotek Brytan i Pudelek Egzamin Małego "Misia" Wilk i Owce Lis i Gąski Chłopczyk i Źrebię Gęsia Kapela Lew i Piesek Niedźwiedź i Pszczółka Śniadanie Artysta Z Zimowych Rozrywek Leniwy Chłopczyk Przygoda z Indykiem O hämmästyksissään. Leniwy ЙЦУКЕН'
#      );
#      insert into test(long_text)
#      values(
#          'Kaikki neuvon-antajat ja etevimmät päälliköt ja mollat ja imamit ja kadit ja kaupungin päähenkilöt olivat suuresti hämmästyksissään. Hänen tunnettu hurskautensa vaati kaikkia äänettömyyteen, sillä välin kuin hän itse lausui pitkän rukouksen, pyytäen Allah''ta ja Profeettaa hämmentämään kaikkia häväiseviä Juutalaisia ja uskottomia ja vuodattamaan totuuden sanoja jumalisten ihmisten suuhun. Ja nyt kunnian-arvoisa sheiki kutsui esiin kaikki todistajat David Alroy''ta vastaan. Heti Kisloch, Kurdilainen, joka oli koroitettu Bagdadin kadiksi, astui esiin, veti sametti-kukkarostansa paperikääryn ja luki semmoisen todistuksen, jossa arvoisa Kisloch vakuutti, että hän ensin tutustui vangin, David Alroy''n kanssa joissakin erämaan raunioissa -- muutamain rosvojen pesässä, joita Alroy johdatti; että hän, Kisloch, oli rehellinen kauppias ja että nämät konnat olivat ryöstäneet hänen karavaninsa ja hän itse joutunut vankeuteen; että hänen vankeutensa toisena yönä Alroy oli ilmestynyt hänen eteensä leijonan muodossa ja kolmantena tuimasilmäisenä härkänä; että hänen oli tapa alinomaa muuttaa itsensä; että hän usein nosti henkiä; että viimein eräänä kauheana yönä Eblis itse tuli suurella juhlasaatolla ja antoi Alroy''lle Salomonin, Davidin pojan valtikan; ja että tämä seuraavana päivänä kohotti lippunsa ja kohta sen jälkeen kukisti Hassan Subah''n ja tämän Seldshukit useitten hirmuisten paholaisten silminnähtävällä avulla.  Kalidaan, Indialaisen, Guebriläisen ja Neekerin ja muutamien muitten saman hengen lapsien todistukset vetivät täysin määrin vertoja Kisloch Kurdilaisen uhkealle kertomukselle. Hebrealaisen valloittajan vastustamaton menestys oli kieltämättömällä tavalla selitetty, Mahomettilaisten aseitten kunnia ja Moslemin uskon puhtaus olivat asetetut jälleen entiseen loistoonsa ja saastuttamattomaan maineesensa. Todeksi saatiin, että David Alroy oli Ebliin lapsi, noitamies, taikakalujen ja myrkkyjen käyttäjä. Kansa kuunteli kauhulla ja harmilla. He olisivat tunkeneet vartiaväen läpitse ja repineet hänet kappaleiksi, jolleivät olisi pelänneet Karamanialaisten sotatapparoita. Niin he lohduttivat mieltänsä sillä, että he ennen pitkää saisivat nähdä hänen kidutuksensa.  Bagdadin kadi kumarsi Karamanian kuningasta ja kuiskasi soveliaan matkan päästä jotakin kuninkaalliseen korvaan. Torvet kaikkuivat, kuuluttajat vaativat äänettömyyttä ja kuninkaan huulet liikkuivat taas.  "Kuule, oi kansa, ja ole viisas. Pääkadi aikoo nyt lukea kuninkaallisen prinsessan Schirenen, noiturin etevimmän uhrin todistuksen."  Ja todistus luettiin, joka vakuutti, että David Alroy omisti ja kantoi lähinnä sydäntänsä erästä talismania, jonka Eblis oli antanut hänelle ja jonka voima oli niin suuri, että, jos sitä kerta painettiin naisen rintaa vastaan, tämä ei enää voinut hallita tahtoansa. Tämmöinen kova onni oli kohdannut oikeauskoisten hallitsian tytärtä.  "Onko siinä niin kirjoitettu?" vanki kysyi.  "On", kadi vastasi, "ja sen alla on vielä prinsessan kuninkaallinen allekirjoitus."  "Se on väärennetty."  Karamanian kuningas kavahti valta-istuimeltansa ja oli vihoissansa astumallaan sen portaita alas. Hänen kasvonsa olivat veripunaiset, hänen partansa kuin tulen liekki. Joku lempiministeri rohkeni vienosti pidättää häntä hänen kuninkaallisesta vaipastansa.  "Tapa paikalla pois se koira", Karamanian kuningas mutisi.  "Prinsessa on itse täällä", lausui kadi, "todistamassa niitä noitakeinoja, joitten alaisena hän oli, vaan joitten vaikutuksesta hän nyt Allah''n ja Profeetan voiman kautta on pääsnyt."  Alroy''ta vävähti!  "Astu esiin, kuninkaallinen prinsessa", kadi sanoi, "ja jos se todistus, jonka kuulit, on perustettu, nosta ylös se kuninkaallinen käsi, joka koristi sen allekirjoituksellaan."  Lähellä valta-istuinta oleva eunukkien joukko teki tilaa; naishaamu, joka oli verhottu hunnulla jalkoihin saakka, astui esiin. Hän nosti ylös kätensä; koko kerääntynyt kansa tuskin hengitti mielenliikutuksesta; eunukkien rivit ummistuivat jälleen; huuto kuului ja hunnustettu haamu katosi.  "Minä odotan kidutuskoneitasi, kuningas", Alroy lausui raskaan surun äänellä. Hänen lujuutensa näytti luopuneen hänestä. Hänen silmänsä olivat luodut maahan. Hän oli nähtävästi vaipunut syvään miettimiseen taikka heittäynyt epätoivoon.  "Valmistakaat seipäät", käski Alp Arslan.  Koko kansan joukkoa värisytti vasten mieltäkin.  Yksi orja lähestyi ja tarjosi paperikääryä Alroy''lle. Hän tunsi Nubialaisen, joka oli Honainin palveluksessa. Hänen entinen ministerinsä ilmoitti hänelle, että hän oli saapuvilla; että ne ehdot, joita hän vankihuoneessa tarjosi, vielä myönnettäisiin; että jos Alroy, jota asiaa hän ei epäillyt ja jota hän rukoili, suostuisi niitä vastaan-ottamaan, hänen tuli pistää paperikäärö poveensa, mutta, jos hän yhä oli taipumaton, jos hänen yhä oli mieletön päätös kuolla hirveä ja häväisevä kuolema, hänen tuli repiä se rikki ja heittää se tanterelle. Silmänräpäyksellä Alroy otti paperikääryn ja repi sen kiivaasti tuhansiin palasiin. Tuulen puuska levitti kappaleet laajalle yliympäri. Alhaiso riiteli näistä David Alroy''n viimeisistä muistoista; ja tämä vähäinen tapaus tuotti paljon hämminkiä.  Tällä välin Neekerit varustivat kidutuksen ja kuoleman koneita.  "Tuon juutalaisen koiran itsepintaisuus tekee minun hulluksi", lausui Karamanian kuningas hovimiehillensä. "Minua haluttaa puhutella häntä vähän, ennenkuin hän kuolee." Lempiministeri pyysi hallitsiaansa olemaan levollisena; mutta kuninkaallinen parta kävi niin punaiseksi, ja kuninkaalliset silmät iskivät niin kauheata tulta, että lempiministerikin lopulta myöntyi.  Torvi kaikkui, kuuluttajat vaativat vaiti-oloa, ja Alp Arslanin ääni eroitettiin jälleen.  "Senkin koira, näetkö sinä, mikä on tarjonasi? Tiedätkö sinä, mikä vartoo sinua sinun herrasi Ebliin asunnoissa? Voiko väärä ylpeys viehättää Juutalaistakin? Eikö elämä ole suloista? Eikö olisi parempi olla minun varvaskenkieni kantaja kuin tulla seivästetyksi?"  "Jalomielinen Alp Arslan", vastasi Alroy ilmeisen ylenkatseen äänellä; "luuletko, että mikään kidutus rasittaa niin, kuin se muisto, että sinä olet voittanut minun?"  "Partani kautta, hän ivaa minua!" Karamanialaisten hallitsia huudahti; "hän tekee kiusaa minulle! Älkäät koskeko vaippaani. Minä tahdon puhua hänen kanssaan. Te ette näe kauemmaksi kuin hunnustettu haukka, te sokean äidin lapset. Se on noita; hänellä on vielä jälellä joku päätaika; hän pelastaa vielä henkensä. Hän lentää ilmaan taikka vaipuu maan sisään. Hän nauraa meidän kidutuksiamme." Karamanian kuningas astui tuota pikaa valta-istuimensa portaita alaspäin; häntä seurasivat hänen lempiministerinsä ja hänen neuvon-antajansa ja hänen etevimmät päällikkönsä ja kadit ja mollat ja imamit ja kaupungin päähenkilöt.  "Sinä noita!" Alp Arslan huudahti, "hävytön noita! halvan äidin halpa poika! koirien koira! niskotteletko sinä meitä vastaan? Kuiskaako herrasi Eblis toivoa sinun korviisi? Nauratko meidän rangaistuksiamme? Aiotko lentää ylös ilmaan? vai painua alas maahan? Niinkö, niinkö?" Hengästyneenä ja vihastansa uupuneena hallitsia vaikeni. Hän repi partaansa ja polki maata rajussa vimmassaan.  "Sinä olet viisaampi kuin neuvon-antajasi, kuningas Arslan; minä en nöyrry sinun edessäsi. Minun Herrani, vaikka hän ei ole Eblis, ei ole hylännyt minua. Minä nauran sinun rangaistuksiasi. Sinun kidutuksiasi minä ylenkatson. Minä sekä vaivun maan sisään että kohoan ilmaan. Tyydytkö nyt vastaukseeni?"  "Partani kautta", huudahti tulistunut Arslan, "minä tyydyn vastaukseesi. Pelastakoon Eblis sinut, jos hän voi;" ja Karamanian kuningas, Aasian mainioin miekan piteliä veti säilänsä, ikäänkuin salaman, tupesta ja silpaisi yhdellä säväyksellä Alroy''lta pään. Se kaatui, vaan, kun se kaatui, riemuitsevan pilkan hymy näytti vivahtelevan sankarin kylmenevillä kasvoilla ja kysyvän hänen vihollisiltansa: "missä kaikki teidän kidutuksenne nyt ovat?" Do Dzieci Gołąbki i Dziewczynka Dziecię i Koza Wróbel i Jaskółka Osieł i Chłopczyk Nieposłuszny Zajączek Kotek Brytan i Pudelek Egzamin Małego "Misia" Wilk i Owce Lis i Gąski Chłopczyk i Źrebię Gęsia Kapela Lew i Piesek Niedźwiedź i Pszczółka Śniadanie Artysta Z Zimowych Rozrywek Leniwy Chłopczyk Przygoda z Indykiem O hämmästyksissään. Leniwy НЕКУЦЙ'
#      );
#      
#      update test set long_descr = long_text;
#  	commit;
#  	
#  	
#  	
#      -- ###################################################
#  	-- ##############  C O R E    3 4 4 6   ##############
#  	-- ###################################################
#  	recreate table test( s varchar(8187) character set utf8 collate unicode_ci_ai, b blob sub_type 1 character set utf8 collate unicode_ci_ai);
#  	commit;
#  
#  	insert into test (s, b )
#  	values(
#  'Sur le boulevard Montmorency, au n° 53, s''élève une maison portant,
#  encastré dans son balcon, un profil lauré de Louis XV, en bronze
#  doré, qui a tout l''air d''être le médaillon, dont était décorée la
#  tribune de musique de la salle à manger de Luciennes, représenté dans
#  l''aquarelle de Moreau que l''on voit au Louvre. Cette tête, que quelques
#  promeneurs regardent d''un œil farouche, n''est point,--ai-je besoin de
#  le dire?--une affiche des opinions politiques du propriétaire, elle est
#  tout bonnement l''enseigne d''un des nids les plus pleins de choses du
#  XVIIIe siècle qui existent à Paris.
#  
#  La porte noire, que surmonte un élégant dessus de grille de chapelle
#  jésuite en fer forgé, la porte ouverte, du bas de l''escalier, de
#  l''entrée du vestibule, du seuil de la maison, le visiteur est accueilli
#  par des terres cuites, des bronzes, des dessins, des porcelaines du
#  siècle aimable par excellence, mêlés à des objets de l''Extrême-Orient,
#  qui se trouvaient faire si bon ménage dans les collections de Madame de
#  Pompadour et de tous les _curieux_ et les _curiolets_ du temps.
#  
#  La vie d''aujourd''hui est une vie de combattivité; elle demande dans
#  toutes les carrières une concentration, un effort, un travail, qui, en
#  son foyer enferment l''homme, dont l''existence n''est plus extérieure
#  comme au XVIIIe siècle, n''est plus papillonnante parmi la société
#  depuis ses dix-sept ans jusqu''à sa mort. De notre temps on va bien
#  encore dans le monde, mais toute la vie ne s''y dépense plus, et le
#  _chez-soi_ a cessé d''être l''hôtel garni où l''on ne faisait que coucher.
#  Dans cette vie assise au coin du feu, renfermée, sédentaire, la
#  créature humaine, et la première venue, a été poussée à vouloir les
#  quatre murs de son _home_ agréables, plaisants, amusants aux yeux; et
#  cet entour et ce décor de son intérieur, elle l''a cherché et trouvé
#  naturellement dans l''objet d''art pur ou dans l''objet d''art industriel,
#  plus accessible au goût de tous. Du même coup, ces habitudes moins
#  mondaines amenaient un amoindrissement du rôle de la femme dans la
#  pensée masculine; elle n''était plus pour nous l''occupation galante de
#  toute notre existence, cette occupation qui était autrefois la carrière
#  du plus grand nombre, et, à la suite de cette modification dans les
#  mœurs, il arrivait ceci: c''est que l''intérêt de l''homme, s''en allant
#  de l''être charmant, se reportait en grande partie sur les jolis objets
#  inanimés dont la passion revêt un peu de la nature et du caractère
#  de l''amour. Au XVIIIe siècle, il n''y a pas de _bibeloteurs_ jeunes:
#  c''est là la différence des deux siècles. Pour notre génération, la
#  _bricabracomanie_ n''est qu''un bouche-trou de la femme qui ne possède
#  plus l''imagination de l''homme, et j''ai fait à mon égard cette remarque,
#  que, lorsque par hasard mon cœur s''est trouvé occupé, l''objet d''art ne
#  m''était de rien.
#  
#  Oui, cette passion devenue générale, ce plaisir solitaire, auquel se
#  livre presque toute une nation, doit son développement au vide, à
#  l''ennui du cœur, et aussi, il faut le reconnaître, à la tristesse
#  des jours actuels, à l''incertitude des lendemains, à l''enfantement,
#  les pieds devant, de la société nouvelle, à des soucis et à des
#  préoccupations qui poussent, comme à la veille d''un déluge, les désirs
#  et les envies à se donner la jouissance immédiate de tout ce qui les
#  charme, les séduit, les tente: l''oubli du moment dans l''assouvissement
#  artistique.
#  
#  Ce sont ces causes, et incontestablement l''éducation de l''œil des
#  gens du XIXe siècle, et encore un sentiment tout nouveau, la tendresse
#  presque humaine pour les _choses_, qui font, à l''heure qu''il est, de
#  presque tout le monde, des collectionneurs et de moi en particulier le
#  plus passionné de tous les collectionneurs.
#  
#  Un riant pavé en marbre blanc et en marbre rouge du Languedoc, avec,
#  pour revêtement aux murs et au plafond, un cuir moderne peuplé de
#  perroquets fantastiques dorés et peints sur un fond vert d''eau.
#  
#  Sur ce cuir, dans un désordre cherché, dans un pittoresque
#  d''antichambre et d''atelier, toutes sortes de choses voyantes et
#  claquantes, de brillants cuivres découpés, des poteries dorées, des
#  broderies du Japon et encore des objets bizarres, inattendus, étonnant
#  par leur originalité, leur exotisme, et vis-à-vis d''un certain nombre
#  desquels je me fais un peu l''effet du bon Père Buffier quand il disait:
#  «Voilà des choses que je ne sais pas, il faut que je fasse un livre
#  dessus.»
#  
#  Ça, une petite jardinière à suspension, fabriquée d''une coloquinte
#  excentrique, dont la tige tournante et recroquevillée est une tige de
#  bronze qui a la flexibilité d''une liane; cette grande planchette fruste
#  de bois, toute parcourue des tortils d''un feuillage de lierre, exécuté
#  en nacre et en écaille: le porte-éventail qui tient dans l''appartement
#  l''éventail ouvert contre le mur; cette petite boule de porcelaine
#  jaune impérial si délicatement treillagée: la cage au grillon ou à
#  la mouche bourdonnante, que le Chinois aime suspendre au chevet de
#  son lit; et cette plaque de faïence figurant une branche de pêcher en
#  fleur, modelée à jour dans un cadre de bois en forme d''écran, vous
#  représente la décoration de l''angle religieux et mystique d''une chambre
#  de prostituée de maison de thé, l''espèce de tableau d''autel devant
#  lequel elle place une fleur dans un vase.
#  
#  Des broderies du Japon, ai-je dit plus haut, c''est là, dans leurs
#  cadres de bambous, la riche, la splendide, l''_éclairante_ décoration
#  des murs du vestibule et un peu de toute la maison. Ces carrés de soie
#  brodés appelés _fusha_ ou _foukousa_ font la chatoyante couverture
#  sous laquelle on a l''habitude, dans l''Empire du Lever du Soleil,
#  d''envoyer tout présent quelconque, et le plus minime, fût-il même de
#  deux œufs[1]. Les anciens _foukousas_ fabriqués à Kioto[2] sont des
#  produits d''un art tout particulier au Japon, et auxquels l''Europe
#  ne peut rien opposer: de la peinture, de vrais tableaux composés
#  et exécutés en soie par un brodeur, où sur les fonds aux adorables
#  nuances, et telles qu''en donne le satin ou le crêpe, un oiseau, un
#  poisson, une fleur se détache dans le haut relief d''une broderie.
#  Et rien là dedans du travail d''un art mécanique, du dessin bête de
#  vieille fille de nos broderies à nous, mais des silhouettes d''êtres
#  pleins de vie, avec leurs pattes d''oiseau d''un si grand style, avec
#  leurs nageoires de poisson d''un si puissant contournement. Quelquefois
#  des parties peintes, peintes à l''encre de Chine, s''associent de la
#  manière la plus heureuse à la broderie. Je connais, chez Mme Auguste
#  Sichel, une fusée de fleurs brodée dans un vase en sparterie peint ou
#  imprimé, qui est bien la plus harmonieuse chose qu''il soit possible
#  de voir. M. de Nittis a fait un écran, d''un admirable et singulier
#  carré, où deux grues, brodées en noir sur un fond rose saumoné, ont,
#  comme accompagnement et adoucissement de la broderie, des demi-teintes
#  doucement lavées d''encre de Chine sur l''étoffe enchanteresse. Et dans
#  ce vestibule, il y a, sur un fond lilas, des carpes nageant au milieu
#  de branchages de presle brodées en or, et dont le ventre apparaît comme
#  argenté par un reflet de bourbe: un effet obtenu par une réserve au
#  milieu du fond tout teinté et obscuré d''encre de Chine. Il est même un
#  certain nombre de foukousas absolument peints. J''ai coloriée, sur un
#  crêpe gris, dans l''orbe d''un soleil rouge comme du feu, l''échancrure
#  pittoresque d''un passage de sept grues, exécuté avec la science que les
#  Japonais possèdent du vol de l''échassier. J''ai encore, jetées sur un
#  fond maïs, sans aucun détail de terrain, deux grandes grues blanches,
#  à la petite crête rougie de vermillon, au cou, aux pattes, à la queue,
#  teintés d''encre de Chine. Et ne vous étonnez pas de rencontrer si
#  souvent sur les broderies la grue, cet oiseau qui apparaît dans le
#  haut du ciel aux Japonais comme un messager céleste, et qu''ils saluent
#  de l''appellation: _O Tsouri Sama_, Sa Seigneurie la Grue.
#  
#  [1] Il n''est guère besoin de dire que le carré est toujours
#  rapporté à son maître par le porteur du présent.
#  
#  [2] Les foukousas modernes seraient aujourd''hui fabriqués à
#  Togané, d''où on les expédierait à Yedo.
#  '
#  , -----------
#  'Sur le boulevard Montmorency, au n° 53, s''élève une maison portant,
#  encastré dans son balcon, un profil lauré de Louis XV, en bronze
#  doré, qui a tout l''air d''être le médaillon, dont était décorée la
#  tribune de musique de la salle à manger de Luciennes, représenté dans
#  l''aquarelle de Moreau que l''on voit au Louvre. Cette tête, que quelques
#  promeneurs regardent d''un œil farouche, n''est point,--ai-je besoin de
#  le dire?--une affiche des opinions politiques du propriétaire, elle est
#  tout bonnement l''enseigne d''un des nids les plus pleins de choses du
#  XVIIIe siècle qui existent à Paris.
#  
#  La porte noire, que surmonte un élégant dessus de grille de chapelle
#  jésuite en fer forgé, la porte ouverte, du bas de l''escalier, de
#  l''entrée du vestibule, du seuil de la maison, le visiteur est accueilli
#  par des terres cuites, des bronzes, des dessins, des porcelaines du
#  siècle aimable par excellence, mêlés à des objets de l''Extrême-Orient,
#  qui se trouvaient faire si bon ménage dans les collections de Madame de
#  Pompadour et de tous les _curieux_ et les _curiolets_ du temps.
#  
#  La vie d''aujourd''hui est une vie de combattivité; elle demande dans
#  toutes les carrières une concentration, un effort, un travail, qui, en
#  son foyer enferment l''homme, dont l''existence n''est plus extérieure
#  comme au XVIIIe siècle, n''est plus papillonnante parmi la société
#  depuis ses dix-sept ans jusqu''à sa mort. De notre temps on va bien
#  encore dans le monde, mais toute la vie ne s''y dépense plus, et le
#  _chez-soi_ a cessé d''être l''hôtel garni où l''on ne faisait que coucher.
#  Dans cette vie assise au coin du feu, renfermée, sédentaire, la
#  créature humaine, et la première venue, a été poussée à vouloir les
#  quatre murs de son _home_ agréables, plaisants, amusants aux yeux; et
#  cet entour et ce décor de son intérieur, elle l''a cherché et trouvé
#  naturellement dans l''objet d''art pur ou dans l''objet d''art industriel,
#  plus accessible au goût de tous. Du même coup, ces habitudes moins
#  mondaines amenaient un amoindrissement du rôle de la femme dans la
#  pensée masculine; elle n''était plus pour nous l''occupation galante de
#  toute notre existence, cette occupation qui était autrefois la carrière
#  du plus grand nombre, et, à la suite de cette modification dans les
#  mœurs, il arrivait ceci: c''est que l''intérêt de l''homme, s''en allant
#  de l''être charmant, se reportait en grande partie sur les jolis objets
#  inanimés dont la passion revêt un peu de la nature et du caractère
#  de l''amour. Au XVIIIe siècle, il n''y a pas de _bibeloteurs_ jeunes:
#  c''est là la différence des deux siècles. Pour notre génération, la
#  _bricabracomanie_ n''est qu''un bouche-trou de la femme qui ne possède
#  plus l''imagination de l''homme, et j''ai fait à mon égard cette remarque,
#  que, lorsque par hasard mon cœur s''est trouvé occupé, l''objet d''art ne
#  m''était de rien.
#  
#  Oui, cette passion devenue générale, ce plaisir solitaire, auquel se
#  livre presque toute une nation, doit son développement au vide, à
#  l''ennui du cœur, et aussi, il faut le reconnaître, à la tristesse
#  des jours actuels, à l''incertitude des lendemains, à l''enfantement,
#  les pieds devant, de la société nouvelle, à des soucis et à des
#  préoccupations qui poussent, comme à la veille d''un déluge, les désirs
#  et les envies à se donner la jouissance immédiate de tout ce qui les
#  charme, les séduit, les tente: l''oubli du moment dans l''assouvissement
#  artistique.
#  
#  Ce sont ces causes, et incontestablement l''éducation de l''œil des
#  gens du XIXe siècle, et encore un sentiment tout nouveau, la tendresse
#  presque humaine pour les _choses_, qui font, à l''heure qu''il est, de
#  presque tout le monde, des collectionneurs et de moi en particulier le
#  plus passionné de tous les collectionneurs.
#  
#  Un riant pavé en marbre blanc et en marbre rouge du Languedoc, avec,
#  pour revêtement aux murs et au plafond, un cuir moderne peuplé de
#  perroquets fantastiques dorés et peints sur un fond vert d''eau.
#  
#  Sur ce cuir, dans un désordre cherché, dans un pittoresque
#  d''antichambre et d''atelier, toutes sortes de choses voyantes et
#  claquantes, de brillants cuivres découpés, des poteries dorées, des
#  broderies du Japon et encore des objets bizarres, inattendus, étonnant
#  par leur originalité, leur exotisme, et vis-à-vis d''un certain nombre
#  desquels je me fais un peu l''effet du bon Père Buffier quand il disait:
#  «Voilà des choses que je ne sais pas, il faut que je fasse un livre
#  dessus.»
#  
#  Ça, une petite jardinière à suspension, fabriquée d''une coloquinte
#  excentrique, dont la tige tournante et recroquevillée est une tige de
#  bronze qui a la flexibilité d''une liane; cette grande planchette fruste
#  de bois, toute parcourue des tortils d''un feuillage de lierre, exécuté
#  en nacre et en écaille: le porte-éventail qui tient dans l''appartement
#  l''éventail ouvert contre le mur; cette petite boule de porcelaine
#  jaune impérial si délicatement treillagée: la cage au grillon ou à
#  la mouche bourdonnante, que le Chinois aime suspendre au chevet de
#  son lit; et cette plaque de faïence figurant une branche de pêcher en
#  fleur, modelée à jour dans un cadre de bois en forme d''écran, vous
#  représente la décoration de l''angle religieux et mystique d''une chambre
#  de prostituée de maison de thé, l''espèce de tableau d''autel devant
#  lequel elle place une fleur dans un vase.
#  
#  Des broderies du Japon, ai-je dit plus haut, c''est là, dans leurs
#  cadres de bambous, la riche, la splendide, l''_éclairante_ décoration
#  des murs du vestibule et un peu de toute la maison. Ces carrés de soie
#  brodés appelés _fusha_ ou _foukousa_ font la chatoyante couverture
#  sous laquelle on a l''habitude, dans l''Empire du Lever du Soleil,
#  d''envoyer tout présent quelconque, et le plus minime, fût-il même de
#  deux œufs[1]. Les anciens _foukousas_ fabriqués à Kioto[2] sont des
#  produits d''un art tout particulier au Japon, et auxquels l''Europe
#  ne peut rien opposer: de la peinture, de vrais tableaux composés
#  et exécutés en soie par un brodeur, où sur les fonds aux adorables
#  nuances, et telles qu''en donne le satin ou le crêpe, un oiseau, un
#  poisson, une fleur se détache dans le haut relief d''une broderie.
#  Et rien là dedans du travail d''un art mécanique, du dessin bête de
#  vieille fille de nos broderies à nous, mais des silhouettes d''êtres
#  pleins de vie, avec leurs pattes d''oiseau d''un si grand style, avec
#  leurs nageoires de poisson d''un si puissant contournement. Quelquefois
#  des parties peintes, peintes à l''encre de Chine, s''associent de la
#  manière la plus heureuse à la broderie. Je connais, chez Mme Auguste
#  Sichel, une fusée de fleurs brodée dans un vase en sparterie peint ou
#  imprimé, qui est bien la plus harmonieuse chose qu''il soit possible
#  de voir. M. de Nittis a fait un écran, d''un admirable et singulier
#  carré, où deux grues, brodées en noir sur un fond rose saumoné, ont,
#  comme accompagnement et adoucissement de la broderie, des demi-teintes
#  doucement lavées d''encre de Chine sur l''étoffe enchanteresse. Et dans
#  ce vestibule, il y a, sur un fond lilas, des carpes nageant au milieu
#  de branchages de presle brodées en or, et dont le ventre apparaît comme
#  argenté par un reflet de bourbe: un effet obtenu par une réserve au
#  milieu du fond tout teinté et obscuré d''encre de Chine. Il est même un
#  certain nombre de foukousas absolument peints. J''ai coloriée, sur un
#  crêpe gris, dans l''orbe d''un soleil rouge comme du feu, l''échancrure
#  pittoresque d''un passage de sept grues, exécuté avec la science que les
#  Japonais possèdent du vol de l''échassier. J''ai encore, jetées sur un
#  fond maïs, sans aucun détail de terrain, deux grandes grues blanches,
#  à la petite crête rougie de vermillon, au cou, aux pattes, à la queue,
#  teintés d''encre de Chine. Et ne vous étonnez pas de rencontrer si
#  souvent sur les broderies la grue, cet oiseau qui apparaît dans le
#  haut du ciel aux Japonais comme un messager céleste, et qu''ils saluent
#  de l''appellation: _O Tsouri Sama_, Sa Seigneurie la Grue.
#  
#  [1] Il n''est guère besoin de dire que le carré est toujours
#  rapporté à son maître par le porteur du présent.
#  
#  [2] Les foukousas modernes seraient aujourd''hui fabriqués à
#  Togané, d''où on les expédierait à Yedo.
#  '
#  	);
#  	commit;  	
#  	set count off;
#  	set heading off;
#      set list off;	
#  	select 'All OK.' from rdb$database;
#  '''
#  #-------------------------------------------
#  f_init_ddl=open( os.path.join(context['temp_directory'],'tmp_check_ddl.sql'), 'w')
#  f_init_ddl.write(sql_ddl)
#  flush_and_close( f_init_ddl )
#  
#  f_init_log = open( os.path.join(context['temp_directory'],'tmp_check_ddl.log'), 'w')
#  f_init_err = open( os.path.join(context['temp_directory'],'tmp_check_ddl.err'), 'w')
#  subprocess.call( [ context['isql_path'], dsn, '-ch', 'utf8', '-i', f_init_ddl.name ], stdout = f_init_log,stderr = f_init_err)
#  flush_and_close( f_init_log )
#  flush_and_close( f_init_err )
#  
#  f_meta_log1 = open( os.path.join(context['temp_directory'],'tmp_initial_meta.sql'), 'w')
#  f_meta_err1 = open( os.path.join(context['temp_directory'],'tmp_initial_meta.err'), 'w')
#  subprocess.call( [ context['isql_path'], dsn, '-x', '-ch', 'utf8' ], stdout = f_meta_log1, stderr = f_meta_err1)
#  flush_and_close( f_meta_log1 )
#  flush_and_close( f_meta_err1 )
#  
#  
#  # Backup with '-ZIP' command switch
#  ########
#  
#  f_backup_log = open( os.path.join(context['temp_directory'],'tmp_backup.log'), 'w')
#  f_backup_err = open( os.path.join(context['temp_directory'],'tmp_backup.err'), 'w')
#  subprocess.call( [ context['gbak_path'], '-b', '-zip', dsn, tmpfbk ], stdout = f_backup_log, stderr = f_backup_err)
#  flush_and_close( f_backup_log )
#  flush_and_close( f_backup_err )
#  
#  # Restore:
#  ##########
#  
#  f_restore_log = open( os.path.join(context['temp_directory'],'tmp_restore.log'), 'w')
#  f_restore_err = open( os.path.join(context['temp_directory'],'tmp_restore.err'), 'w')
#  subprocess.call( [ context['gbak_path'], '-rep', tmpfbk, 'localhost:' + tmpfdb ], stdout = f_restore_log, stderr = f_restore_err)
#  flush_and_close( f_restore_log )
#  flush_and_close( f_restore_err )
#  
#  # Validate restored database:
#  ##########
#  
#  f_validate_log = open( os.path.join(context['temp_directory'],'tmp_validate.log'), 'w')
#  f_validate_err = open( os.path.join(context['temp_directory'],'tmp_validate.err'), 'w')
#  subprocess.call( [ context['gfix_path'], '-v', '-full', 'localhost:' + tmpfdb ], stdout = f_validate_log, stderr = f_validate_err)
#  flush_and_close( f_validate_log )
#  flush_and_close( f_validate_err )
#  
#  f_meta_log2 = open( os.path.join(context['temp_directory'],'tmp_restored_meta.sql'), 'w')
#  f_meta_err2 = open( os.path.join(context['temp_directory'],'tmp_restored_meta.err'), 'w')
#  subprocess.call( [ context['isql_path'], dsn, '-x', '-ch', 'utf8' ], stdout = f_meta_log2, stderr = f_meta_err2)
#  flush_and_close( f_meta_log2 )
#  flush_and_close( f_meta_err2 )
#  
#  
#  # Compare extracted metadata:
#  #########
#  
#  f_meta_log1 = open( f_meta_log1.name,'r' )
#  f_meta_log2 = open( f_meta_log2.name,'r')
#  
#  f_diff_txt=open( os.path.join(context['temp_directory'],'tmp_meta_diff.txt'), 'w')
#  f_diff_txt.write( ''.join( difflib.unified_diff( f_meta_log1.readlines(), f_meta_log2.readlines() ) ) )
#  flush_and_close( f_diff_txt )
#  
#  flush_and_close( f_meta_log1 )
#  flush_and_close( f_meta_log2 )
#  
#  # Check: all files from following set must be EMPTY:
#  ########
#  
#  f_list = set( (f_init_err, f_meta_err1, f_meta_err2, f_backup_err, f_restore_err, f_validate_log, f_validate_err, f_diff_txt) )
#  for x in f_list:
#      with open(x.name, 'r') as f:
#  		for line in f:
#  			if line.split():
#  				print('UNEXPECTED CONTENT in '+ x.name + ': '+line)
#  
#  
#  ######################################################################
#  # Cleanup:
#  f_list |= set( ( f_init_ddl, f_init_log, f_meta_log1, f_meta_log2, f_backup_log, f_restore_log, tmpfbk, tmpfdb) )
#  cleanup( f_list )
#  
#---
act_1 = python_act('db_1', substitutions=substitutions_1)


@pytest.mark.version('>=4.0')
@pytest.mark.xfail
def test_1(act_1: Action):
    pytest.fail("Test not IMPLEMENTED")


