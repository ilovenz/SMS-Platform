use SMS;

--  必须修改默认的mysql结束符；，否则mysql在遇到；时就会提交，自然会报错
DELIMITER //

drop procedure if exists spServerRegistration//

create procedure spServerRegistration
(
  IN ServerIP varchar(15),
  IN StartFlag char(1),  # 系统初次启动标志，用于初始化quit_flag
  OUT return_code int,
  OUT return_msg varchar(32) character set utf8
)
lable_exit:
begin
  declare chOnlineFlag char(1);
  declare vstrServerIP varchar(15);
  
  declare exit handler for SQLEXCEPTION
  begin
    rollback;
    -- select @@error
    set return_code = 1;
    set return_msg = 'SQL执行异常，短信获取失败';
  end;

  set return_code = 0;
  set return_msg = '服务器注册成功';
  
  set vstrServerIP = trim(ServerIP);

  if vstrServerIP = '' then
    set return_code = 1;
    set return_msg = '服务器IP地址不能为空'; 
    leave lable_exit;  
  end if;

  -- select length(vstrServerIP);
  set chOnlineFlag = null;

  select online_flag into chOnlineFlag
    from ServerList
   where server_ip = vstrServerIP;

  START TRANSACTION;

  if chOnlineFlag is null then
    insert into ServerList(server_ip, online_flag, last_login, updated_time)
         values(vstrServerIP, '1', now(), now());
  else
    update ServerList set online_flag = '1', last_login = now(), updated_time = now(), quit_flag = case StartFlag when '1' then '0' else quit_flag end
     where server_ip = vstrServerIP;
  end if;  

  COMMIT;

  -- 一次性返回相应信息给发送程序使用，减少数据交互时间
  select traffic_light, in_service_flag, vendor_id, vendor_in_service, a.server_ip, server_in_service, b.online_flag, b.last_login, c.updated_time, b.quit_flag
    from ServiceNow a left join ServerList b on a.server_ip = b.server_ip left join ServerList c on a.server_in_service = c.server_ip; 

end//

set names utf8//
-- call spServerRegistration('', @return_code, @return_msg)//
-- select @return_code, @return_msg//
call spServerRegistration('10.158.36.79', '0', @return_code, @return_msg)//
select @return_code, @return_msg//
show errors//




DELIMITER ;
