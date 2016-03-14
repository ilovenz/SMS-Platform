use SMS;

--  定界符delimiter为默认的“；”

drop table if exists Logs;

create table Logs
       (id          varchar(4)   not null primary key,   -- 
        type        char(1)      not null,               -- 
        create_date datetime     not null,               --
        memo        varchar(200) not null
        ) default character set 'utf8';  # utf8兼容一切字符集

-- 通道信息表
drop table if exists Vendors;

create table Vendors
       (vendor_id  char(1)         not null primary key,  -- 通道服务商id，主键
        vendor_name varchar(10)    not null,              -- 通道服务商名称
        sp_address1 varchar(32)    not null,              -- 短信运营商1
        sp_address2 varchar(32)    not null,              -- 短信运营商2
        send_interface varchar(24) not null,              -- 发送接口
        user_id        varchar(8)  not null,              -- 用户代码
        user_pwd       varchar(12) not null,              -- 发送密码
        rep_interface  varchar(24) not null,              -- 发送状态接口
        sms_max_length int         not null,              -- 允许的最大字符长度，超过此长度的短信，将在发送时进行自动拆分
        standard_sms_length int    not null,              -- 标准短信字符长度, 用于发送短信条数的统计
        fee  float                 not null               -- 每条短信收费标准，单位元
       ) default character set 'utf8';

insert into Vendors (vendor_id, vendor_name, sp_address1, sp_address2, user_id,user_pwd,
                     send_interface, rep_interface, sms_max_length, standard_sms_length, fee) 
              values('0', '港澳', 'http://113.59.109.38:8050/', 'http://59.50.95.232:8050/', '102903', '102903DE',
                     'SendSms2014.aspx', 'GetReport2013.aspx', 210, 70, 0.04);
insert into Vendors (vendor_id, vendor_name, sp_address1, sp_address2, user_id,user_pwd,
                     send_interface, rep_interface, sms_max_length, standard_sms_length, fee) 
              values('1', '玄武', 'http://113.59.109.38:8050/', '', '102903', '102903DE',
                     'SendSms2014.aspx', 'GetReport2013.aspx', 210, 70, 0.04);

commit;

-- 应用系统信息表
drop table if exists App_Info;

create table App_Info
       (app_id        char(4)     not null primary key,   -- 应用id，主键
        app_name      varchar(20) not null,               -- 应用名称
        prefix_flag   char(1)     not null,               -- 是否需要在短信中添加前缀， 0 - 不允许， 1 - 允许
        prefix_detail varchar(24) null,                   -- 前缀内容
        suffix_flag   char(1)     not null,               -- 是否需要在短信中添加后缀， 0 - 不允许， 1 - 允许
        suffix_detail varchar(24) null,                   -- 后缀内容
        app_status    char(1)     not null                -- 应用开通状态， 0 - 未开通，不允许发送短信， 1 - 已开通，允许发送短信  
        ) default character set 'utf8';

insert into App_Info (app_id, app_name, prefix_flag, prefix_detail, suffix_flag, suffix_detail, app_status) 
                  values('10H1', 'OA系统', '0', '', '0', '', '1');
insert into App_Info (app_id, app_name, prefix_flag, prefix_detail, suffix_flag, suffix_detail, app_status) 
                  values('A0T2', '系统监控平台', '0', '', '0', '', '0');
insert into App_Info (app_id, app_name, prefix_flag, prefix_detail, suffix_flag, suffix_detail, app_status) 
                  values('B101', '远程接入平台','0', '', '0', '', '0');
insert into App_Info (app_id, app_name, prefix_flag, prefix_detail, suffix_flag, suffix_detail, app_status) 
                  values('9C99', '壹金所平台', '0', '', '0', '', '1');
insert into App_Info (app_id, app_name, prefix_flag, prefix_detail, suffix_flag, suffix_detail, app_status) 
                  values('0911', '短信平台', '1', '发自短信平台:', '0', '', '1');
commit;

-- 数据字典表
drop table if exists Sys_Dict;

create table Sys_Dict
       (dict_item_name  varchar(20) not null,  -- 字典项
        item_value      varchar(20) not null,  -- 取值
        item_desc       varchar(40) not null   -- 说明项
        ) default character set 'utf8';

insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '0', '短信发送成功'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '1', '流水号seq重复'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '-1', 'spid, pwd, mobiles, sms不能为空'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '-2', '禁用客户'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '-3', '试用客户条数不足或预付费客户条数不足'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '-4', '帐号或密码非法'); -- 港澳资讯短信发送时返回状态信息
insert into Sys_Dict(dict_item_name, item_value, item_desc) values('ga_send_status', '-12', '发生异常'); -- 港澳资讯短信发送时返回状态信息

commit;

-- 系统配置表
drop table if exists Configuration;

create table Configuration
       (conf_item  varchar(18) not null primary key,  -- 配置项，主键索引
        conf_value varchar(6)  not null,              -- 配置项的值
        conf_memo  varchar(50) not null               -- 配置项的含义
        ) default character set 'utf8';

insert into Configuration (conf_item, conf_value, conf_memo) values('service_interval', '3', '往服务信息表中更新记录的时间间隔，单位为秒');
insert into Configuration (conf_item, conf_value, conf_memo) values('sms_max_length', '1000', '最多允许的短信字符长度');
insert into Configuration (conf_item, conf_value, conf_memo) values('sms_max_number', '10', '一次最多允许发送的短信条数');

commit;

-- 短信序号表
drop table if exists SMSSequence;

create table SMSSequence
      (
        sequence_no        int           not null,     -- 短信序号中的后六位当天序号，每次增一, 可能不连续
        work_day           char(8)       not null      -- 当前工作日期, 格式'YYYYMMDD'，如果系统日期与该日期不等，则代表新的一天，将此字段更新为当前系统日期，sequence_no置为1
      ) default character set 'utf8';

insert into SMSSequence(sequence_no, work_day) values('000001', '20150101');
commit;

-- 当前服务信息表
drop table if exists ServiceNow;

create table ServiceNow
       (traffic_light      char(1)       not null,     -- 是否允许短信发送标志  0 - 不允许发送， 1 - 允许发送，由GUI设置
        in_service_flag    char(1)       not null,     -- 短信发送服务是否已启动标志    0 - 未启动， 1 - 已启动，由发送服务回填
        vendor_id          char(1)       not null,     -- 指定短信通道服务商，由GUI设置
        vendor_in_service  char(1)       not null,     -- 当前短信通道服务商，由发送服务回填
        server_ip          varchar(15)   not null,     -- 指定提供服务的机器ip，由GUI设置
        server_in_service  varchar(15)   not null,     -- 当前提供服务的机器ip，由发送服务回填
        last_sending_time  datetime      null,         -- 上次短信成功发送的时间，默认是3s更新一次，超过这个时间则可以判断是服务出现了问题。如果ip是本机，则延迟30s（10倍service_interval的时间）等待另外的机器，看是否接管
                                          -- 如果ip不是本机，则在15s(5倍service_interval的时间)后再判断一次，如仍未被刷新则直接接管
        updated_time       datetime      not null      -- 上次更新时间
        ) default character set 'utf8';

insert into ServiceNow(traffic_light, in_service_flag, vendor_id, vendor_in_service, server_ip, server_in_service, updated_time)
                      values('0', '0', '0', '', '10.158.36.7', '', now());
commit;

-- 本地可用短信发送服务器信息表
drop table if exists ServerList;

create table ServerList
       (server_ip     varchar(15)    not null primary key,     -- 服务器IP
        online_flag   char(1)        not null,                 -- 服务在线标志，表示随时可以提供发送短信服务    0 - 离线， 1 - 在线
        last_login    datetime       not null,                 -- 上次登入时间（程序启动时更新）
        updated_time  datetime       null,                     -- 上次更新时间，用于判断服务是否正常（如果更新时间距离提太长，则守护进程可能已经被异常退出）
        last_logout   datetime       null                      -- 上次登出时间（程序退出时更新）
        ) default character set 'utf8';

insert into ServerList(server_ip, online_flag, last_login, updated_time, last_logout)
     values('10.158.35.9', '0', now(), now(), null);
commit;

-- 系统用户表
drop table if exists Sys_Users;

create table Sys_Users 
       (user_id   char(8)      not null primary key,   -- 用户id，主键
        user_name varchar(10)  not null,               -- 用户名称
        user_pwd  varchar(128) not null,               -- 用户密码
        user_status char(1)    not null                -- 用户状态   '0' - 冻结 '1' - 正常  '2' - 注销
       ) default character set 'utf8';

insert into Sys_Users (user_id, user_name, user_pwd, user_status) values('ebzc0100', 'Alex Li', PASSWORD('welCome3378-'), '1');
commit;

-- 短信原始信息表，存放app的所有短信
drop table if exists SMSRecords;

create table SMSRecords
       (sms_id         char(14)         not null primary key,  -- 短信序号，格式'YYYYMMDD000001'，如20151201000002，后6位由序列产生并组装完成
        mobile_number  char(11)         not null,              -- 手机号码
        app_id         char(4)          not null,              -- 应用程序
        sms_detail     varchar(1000)    not null,              -- 短信内容
        create_date    datetime         not null,              -- 短信创建时间
        sms_status     char(1)          not null default '0',  -- 短信状态 '0' - 新短信，未发送 '1' - 已发送  'X' - 等待发送中间状态 '2' - 发送失败 'D' - 丢弃短信
        sent_date      datetime         null,                  -- 
        sent_status    varchar(4)       not null default '',   -- 通道供应商返回的状态
        error_msg      varchar(50)      not null default '',   -- 返回的错误消息
        sent_ip        varchar(15)      not null default '',   -- 发送给短信的服务器IP
        vendor_id      char(1)          not null default ''    -- 发送该短信的通道供应商
        ) default character set 'utf8';

-- 历史短信表

 

