use SMS;

--  必须修改默认的mysql结束符；，否则mysql在遇到；时就会提交，自然会报错
DELIMITER //

-- 短信发送服务器状态更新
drop procedure if exists spSetServerInService//

create procedure spSetServerInService
(
  IN ServerIP varchar(15),
  OUT return_code int,
  OUT return_msg varchar(32) character set utf8
)
lable_exit:
begin
  declare vstrServerIP varchar(15);

  --  SQL错误代码捕获

  -- 除1048，1062之外的错误捕获陷阱
  declare exit handler for SQLEXCEPTION
  begin
    rollback;
    set return_code = '1';
    set return_msg = 'SQL执行异常，短信发送服务器状态更新失败';
  end;

  set return_code = '0';
  set return_msg = '短信发送服务器状态更新成功';

  --  1、有效性判断
  --    1）手机号码
  set vstrServerIP = trim(ServerIP);

  if vstrServerIP = '' then
    set return_code = '1';
    set return_msg = '服务器IP地址长度非法';
    leave lable_exit;
  end if;
  
  START TRANSACTION;

  update ServiceNow set in_service_flag = '1', server_in_service = vstrServerIP;
  
  update ServerList set online_flag = '1', updated_time = now()
   where server_ip = vstrServerIP;

  commit;


end //

set names utf8//
call spSetServerInService('10.158.36.9', @return_code, @return_msg)//
select @return_code, @return_msg//
show errors//

DELIMITER ;
