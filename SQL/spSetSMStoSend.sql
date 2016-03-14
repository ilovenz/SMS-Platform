use SMS;

--  必须修改默认的mysql结束符；，否则mysql在遇到；时就会提交，自然会报错
DELIMITER //

drop procedure if exists spSetSMStoSend//

create procedure spSetSMStoSend
(
  IN ServerIP varchar(15),
  OUT return_code int,
  OUT return_msg varchar(32) character set utf8
)
lable_exit:
begin
  declare iMaxSMS int;
  declare vstrServerIP varchar(15);
  
  declare exit handler for SQLEXCEPTION
  begin
    rollback;
    -- select @@error
    set return_code = 1;
    set return_msg = 'SQL执行异常，短信获取失败';
  end;


  set return_code = 0;
  set return_msg = '获取短信成功';
  
  set vstrServerIP = trim(ServerIP);

  if vstrServerIP = '' then
    set return_code = 1;
    set return_msg = '服务器IP地址不能为空'; 
    leave lable_exit;  
  end if;

  START TRANSACTION;

  update SMSRecords set sms_status = 'X'
         where sms_status = '0';  -- 只有未发送和发送中的才需要处理，后者是异常情况
         
  COMMIT;

end//

set names utf8//

call spSetSMStoSend('10.158.36.9', @return_code, @return_msg)//
select @return_code, @return_msg//
show errors//




DELIMITER ;
