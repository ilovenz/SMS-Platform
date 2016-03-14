use SMS;

--  必须修改默认的mysql结束符；，否则mysql在遇到；时就会提交，会报错
DELIMITER //

drop procedure if exists spGenerateSMS//

create procedure spGenerateSMS
       (
        IN mobile_number char(11),
        IN application_id char(4),
        IN sms_detail varchar(1000) character set utf8,
        OUT return_code char(1),
        OUT return_msg varchar(40) character set utf8
       )
lable_exit:
begin
  declare sms_msg varchar(1500) character set 'utf8' default null;
  declare sms_mobile char(11) default null;
  declare str_len int;
  declare chAppStatus char(1) default null;
  declare chPrefixFlag char(1) default null;
  declare chSuffixFlag char(1) default null;
  declare strPrefix varchar(24) character set 'utf8' default null;
  declare strSuffix varchar(24) character set 'utf8' default null;
  declare strWorkDay, strNow char(8) default null;
  declare intSequence, iRecCount int;
  declare strSMSID  char(16);

  --  SQL错误代码捕获
  declare exit handler for 1062
  begin
    rollback;
    set return_code = '1';
    set return_msg = '短信序号重复，该短信生成失败';
  end;

  declare exit handler for 1048
  begin
    rollback;
    set return_code = '1';
    set return_msg = '插入字段不能为空值，该短信生成失败';
  end;

  -- 除1048，1062之外的错误捕获陷阱
  declare exit handler for SQLEXCEPTION
  begin
    rollback;
    set return_code = '1';
    set return_msg = 'SQL执行异常，该短信生成失败';
  end;

  set return_code = '0';
  set return_msg = '短信生成成功';

  --  1、有效性判断
  --    1）手机号码
  set sms_mobile = trim(mobile_number);
  if length(sms_mobile) <> 11 then
    set return_code = '1';
    set return_msg = '手机号码长度非法';
    leave lable_exit;
  end if;

  set str_len = 1;
  while str_len <= 11 do
    if substring(sms_mobile, str_len, 1) not in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9') then
      set return_code = '1';
      set return_msg = '手机号码必须全部都是数字';  
      --  有非法字符，不再接着判断，直接退出
      leave lable_exit;
    end if;
    
    set str_len = str_len + 1;
  end while;

  --    2）应用id合法性
  select app_status, prefix_flag, suffix_flag, prefix_detail, suffix_detail
    into chAppStatus, chPrefixFlag, chSuffixFlag, strPrefix, strSuffix
    from App_Info where app_id = application_id;
  select application_id, chAppStatus;
  if chAppStatus is null or chAppStatus = '0' then
    set return_code = '1';
    set return_msg = '未知应用或者该应用尚未开通短信发送功能，请核实';   
    leave lable_exit;  
  end if; 
  
  --    3）短信内容检查，不能为空
  set sms_msg = trim(sms_detail);
  if sms_msg = '' or sms_msg is null then
    set return_code = '1';
    set return_msg = '短信内容不能为空';     
    leave lable_exit;
  end if;  

  --   添加前后缀，放在这里做可以减少发送时的处理时间

  if chPrefixFlag = '1' then
    set sms_msg = concat(strPrefix, sms_msg);
  end if;
  if chsuffixFlag = '1' then
    set sms_msg = concat(sms_msg, strSuffix);
  end if;

  --  短信内容长度，1000以下
  if length(sms_msg) > 1000 then 
    set return_code = '1';
    set return_msg = '短信内容总长度超过1000个字符的限制';
    leave lable_exit;
  end if;

  --  2、产生序号 
  select count(*) into iRecCount from SMSSequence;
  if iRecCount <> 1 then 
    set return_code = '1';
    set return_msg = '表ServiceNow记录异常';
    leave lable_exit;
  end if;

  # 可以将ServiceNow的SequenceNo一起回滚，避免出现不连续的情况
  START TRANSACTION;

  update SMSSequence set sequence_no = sequence_no + 1;
  select work_day, sequence_no into strWorkDay, intSequence
    from SMSSequence;
 
  set strNow = date_format(now(), '%Y%m%d');

  -- select strWorkDay;

  if strWorkDay <> strNow then  --  YYYYMMDD
    --  新的一天，重置序号从1开始, 重置工作日期为新的一天
    update SMSSequence set sequence_no = 1, work_day = strNow;
       set intSequence = 1, strWorkDay = strNow;
  end if;   

  -- 3、将短信写入表中，状态置为“等待发送”
  set strSMSID = concat(strWorkDay, lpad(cast(intSequence as char), 6, '0'));
  -- set strSMSID = 20151224000001; 
  select strSMSID, strWorkDay, intSequence;

  insert into SMSRecords(sms_id, mobile_number, app_id, 
                         sms_detail, create_date, sms_status)
         values(strSMSID, sms_mobile, application_id,
                sms_msg, now(), '0');

  commit;


end //

set names utf8//
call spGenerateSMS('13911591219', '0911', '我想要自由自在', @return_code, @return_msg);
select @return_code, @return_msg//
show errors//

DELIMITER ;
