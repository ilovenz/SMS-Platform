use SMS;

--  必须修改默认的mysql结束符；，否则mysql在遇到；时就会提交，自然会报错
DELIMITER //

drop procedure if exists spSetSendingStatus//

create procedure spSetSendingStatus
(
  IN ServerIP varchar(15),
  IN SMSID char(14),
  IN SentStatus varchar(4),
  IN ErrorMsg varchar(50) character set utf8,
  IN VendorID char(1),
  OUT return_code int,
  OUT return_msg varchar(32) character set utf8
)
lable_exit:
begin
  declare vstrServerIP varchar(15);
  declare chSMSStatus char(1);
  
  declare exit handler for SQLEXCEPTION
  begin
    rollback;
    -- select @@error
    set return_code = 1;
    set return_msg = 'SQL执行异常，短信发送状态更新失败';
  end;

  set return_code = 0;
  set return_msg = '短信发送状态更新成功';
  
  set vstrServerIP = trim(ServerIP);

  if vstrServerIP = '' then
    set return_code = 1;
    set return_msg = '服务器IP地址不能为空'; 
    leave lable_exit;  
  end if;

  START TRANSACTION;

  if SentStatus = '0' then
    set chSMSStatus = '1';
  else
    set chSMSStatus = '2';
  end if;

  update SMSRecords
     set sms_status = chSMSStatus, sent_date = now(), sent_status = SentStatus, error_msg = ErrorMsg, vendor_id = VendorID
   where sms_id = SMSID;

   commit;

end//

set names utf8//

call spSetSendingStatus('10.158.36.79', '20160125000001', '0', '成功', '0', @return_code, @return_msg);
select @return_code, @return_msg//
show errors//

DELIMITER ;
