# -*- coding:utf-8 -*-

import httplib2
import base64
#import re
#urllib2 -> urllib.request in python3.x
from urllib.request import quote
from xml.etree import ElementTree
import sys 
import os 
import time
import atexit
import datetime
from signal import SIGTERM
import mysql.connector
from mysql.connector import RefreshOption
import socket
import struct 
import logging
from configobj import ConfigObj
#import fcntl

global vstrSPAddress1, vstrSPAddress2, vstrSendInterface, vstrRepInterface
global vstrUserID, vstrUserPwd, iSMSMaxLength, vstrVendorName
global chGetVendorInfoError

# 拼装url, 这里拿港澳做demo，将来可以根据需要改写此函数
def generateURL(channelurl, sendinterface, seqid, userid, userpwd, mobiles, sms):
    # 按要求进行base64和url编码
    a = base64.b64encode(bytes(sms, encoding='gbk'))
    msg = quote(a)    

    urlstring = channelurl + sendinterface + '?spid=' + userid + '&pwd=' + userpwd
    urlstring += '&id=' + seqid + '&mobiles=' + mobiles + '&sms=' + msg
   
    return urlstring

def SendMessage(urlstring):
    # 要考虑超时
    h = httplib2.Http(".cache", timeout = 0.3)
    # h = httplib2.Http(".cache")
    global vstrMSGResultCode, vstrMSGRetMsg
    global bSuccess
    
    iRetry = 0
    bSuccess = False
    while iRetry < 3: # 3次重试机会
        try:
            resp, content = h.request(urlstring, "POST")
            # 对返回的内容，用GBK进行解码
            content = content.decode('GBK')
            root = ElementTree.fromstring(content)
            reResult = root.getchildren()[0]  # 第一个节点是Result
            vstrMSGResultCode = reResult.text
            reMsg = root.getchildren()[1].text  # 返回的Desc部分，可以回填或丢弃
            vstrMSGRetMsg = base64.b64decode(reMsg).decode('gbk') # 解码
            bSuccess = True
            break
        except socket.timeout:
            iRetry += 1
            bSuccess = False
            time.sleep(0.1)

def get_ip_address(ifname='eth0'):
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return (socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,  
                struct.pack('256s',ifname[:15]))[20:24])).strip('\n')
    except:
        ips = os.popen("LANG=C ifconfig | grep \"inet addr\" | grep -v 
                       \"127.0.0.1\" | awk -F \":\" '{print $2}' 
                       | awk '{print $1}'").readlines()
        if len(ips) > 0:
            # 去掉后面的换行符
            return ips[0].strip('\n')
    return ''
    # PyDev for Eclipse不能识别fcntl
    """
    ips = os.popen("LANG=C ifconfig | grep \"inet addr\" | grep -v \"127.0.0.1\" \
                   | awk -F \":\" '{print $2}' | awk '{print $1}'").readlines()
    if len(ips) > 0:
        # 去掉后面的换行符
        return ips[0].strip('\n')

class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run method   
    """

    def __init__(self, pidfile, stdin = '/dev/null', stdout = '/dev/null', 
                 stderr = 'dev/null'):
        # 重定向标准文件描述符（默认情况下定向到/dev/null）  
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        
        # 获取本地IP
        global localIP
        localIP = get_ip_address() 
 
        global strSourcePath
        strSourcePath = sys.path[0]  
        
        global strDBhost, strDBdatabase, strDBuser, strDBpassword

        try:
            strFileName = strSourcePath + "/SMS.ini"
            if not (os.path.exists(strFileName)):
                sys.stdout.write("配置文件[%s]不存在\n" % strFileName)
                exit(0)
            strConfigFile = ConfigObj(strFileName) 
            strDBhost = strConfigFile['dbserver']['host']
            strDBdatabase = strConfigFile['dbserver']['database']
            strDBuser = strConfigFile['dbserver']['user']
            strDBpassword = strConfigFile['dbserver']['password']
        except KeyError:
            sys.stdout.write("配置文件缺失某些键值，请核实！\n")
            exit(0)
         
    def daemonize(self):
        """
        do the Unix double fork magic, see Stevens' 
        "Advanced Programming in the Unix Enironmnet" for Details
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
      
        try:
            """
            为当前进程产生一个子进程，相当于完全复制一份自己，并返回两个值(两次返回值)，为父进
            程返回子进程的进程ID，为子进程返回0。在Windows下面不能用fork
            """
            pid = os.fork() # 
            if pid > 0:
                #exit first parent, 父进程(会话组头领进程)退出，这意味着一个非会话组头领
                #进程永远不能重新获得控制终端
                #无错误退出
                sys.exit(0)  
        except Exception as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            #有错误退出，由解释器或操作系统进行错误捕获，执行清理工作
            sys.exit(1)  

        # decouple from parent environment
        """ 
            chdir确认进程不保持任何目录于使用状态，否则不能umount一个文件系统。
            也可以改变到对于守护程序运行重要的文件所在目录
        """
        # os.chdir("/home/alex/SourceCode/SMS/Python")   
        # chdir确认进程不保持任何目录于使用状态，否则不能umount一个文件系统。也可以改变到
        # 对于守护程序运行重要的文件所在目录 
        global strSourcePath
        os.chdir(strSourcePath)  
        # setsid用于创建一个新的会话，并担任该调用成功后，进程成为新的会话组长和新的进程组长，
        # 并与原来的登录会话、进程组及控制终端完全脱离
        os.setsid()   
        # 调用umask(0)以便拥有对于写的任何东西的完全控制，因为有时不知道继承了什么样的umask 
        os.umask(0)    
 
        #do second fork?
        try:
            pid = os.fork()  
            if pid > 0:
                #第二个父进程退出 
                sys.exit(0)
        except OSError as e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # 此时，进程已经是守护进程了，重定向标准文件描述符 
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        # 注册程序正常结束时的回调函数callback func
        atexit.register(self.delpid)

        # write pidfile
        pid = str(os.getpid())
        open(self.pidfile, 'w+').write("%s\n" % pid)

        # 连接数据库

    # 程序正常结束时的资源清理工作，这里只有移除pid文件的操作，还可以增加别的代码
    def delpid(self):
        os.remove(self.pidfile)
        sys.stdout.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                         + ': 系统已停止......\n')

    def GetVendorInfo(self, cur, VendorID, Flag):
        """
        系统需要1-2个通道供应商，其它数量皆为异常
        """
        global vstrSPAddress1, vstrSPAddress2, vstrSendInterface, vstrRepInterface
        global vstrUserID, vstrUserPwd, iSMSMaxLength, vstrVendorName
        global chGetVendorInfoError, chVendorID
                  
        chFlag = Flag
        chGetVendorInfoError = '0'
        
        if chFlag == '0':
            # 获取当前供应商信息
            vstrSQL = 'select sp_address1, sp_address2, send_interface, \
                              rep_interface, user_id, user_pwd, \
                              sms_max_length, vendor_name, vendor_id \
                         from Vendors \
                        where vendor_id = %s' % VendorID
        else:
            # 适用于切换供应商的情况
            vstrSQL = 'select sp_address1, sp_address2, send_interface, \
                              rep_interface, user_id, user_pwd, \
                              sms_max_length, vendor_name, vendor_id \
                         from Vendors \
                        where vendor_id != %s' % VendorID
        cur.execute(vstrSQL)
        row = cur.fetchall()
        iRowCount = cur.rowcount
        if iRowCount != 1:
            # 数据异常
            chGetVendorInfoError = '1'
        else:
            vstrSPAddress1 = row[0][0] # 短信运营商1（发送IP地址1）
            vstrSPAddress2 = row[0][1] # 短信运营商2（发送IP地址1）
            vstrSendInterface = row[0][2] # 发送接口
            vstrRepInterface = row[0][3] # 发送状态接口
            vstrUserID = row[0][4]  # 用户ID
            vstrUserPwd = row[0][5] # 用户密码
            # 允许的最大字符长度，超过此长度的短信，将在发送时进行自动拆分
            iSMSMaxLength = row[0][6] 
            # 短信通道供应商名称
            vstrVendorName = row[0][7]
            chVendorID = row[0][8]
                    
    def start(self):
        """
        start the daemon
        """
        # check for a pidfile to see if the daemon already runs
        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if pid:
            print(pid)
            message = "pidfile %s already exist. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # start the daemon
        self.daemonize()
        self.run()


    def stop(self):
        """
        stop the daemon
        """
        #Get the pid from the pidfile

        try:
            pf = open(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)        
            return # not an error in a restart

        #try killing the daemon process
        try:
            # 发出结束短信发送标志，等待发送线程停止
            # sys.stdout.write(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #                  + ": 正在停止服务......\n")
            # sys.stdout.flush()

            # 创建数据库连接？
            # 需要改成读取配置文件
            global strDBhost, strDBdatabase, strDBuser, strDBpassword
            cnx = mysql.connector.connect(user=strDBuser, password=strDBpassword, 
                                          host=strDBhost, database=strDBdatabase)
            cursor = cnx.cursor()

            # 判断本机守护进程是否是当前的短信发送进程，如是，需要先停止短信发送服务
            try:
                strSQL = 'select online_flag from ServiceNow a, ServerList b \
                           where a.server_in_service = b.server_ip \
                                 and a.server_in_service = "%s"' % localIP
                # global localIP
                now = datetime.datetime.now()
                sys.stdout.write(now.strftime("%Y-%m-%d %H:%M:%S")  
                                  + "正在停止服务，服务器地址为%s......\n" % localIP)
                cursor.execute(strSQL)
                row = cursor.fetchall()
                chOnlineFlag = row[0][0]
            except:
                # 可能没有任何结果返回
                chOnlineFlag = '0'
                  
            if chOnlineFlag == '1':
                # 将ServiceNow的quit_light字段置为1，通知服务程序停止运行，为退出做准备
                sys.stdout.write(now.strftime("%Y-%m-%d %H:%M:%S") 
                                 + "将ServerList的退出标志quit_flag置为1，通知服 \
                                 务程序停止运行，为退出做准备......\n")
                strSQL = 'update ServerList set quit_flag = "1" \
                           where server_ip = "%s"' % localIP
                # global localIP
                cursor.execute(strSQL)
                cnx.commit()
                  
                # 去除cache，确保获取的是最新的值
                cnx.cmd_refresh(RefreshOption.TABLES)
                time.sleep(2) 
                strSQL = 'select online_flag from ServerList \
                           where server_ip = "%s"' % localIP
                # global localIP
                cursor.execute(strSQL)
                row = cursor.fetchall()
                chOnlineFlag = row[0][0]
                    
                iTimeout = 0
                # 最多循环15次, 约15秒之后强行退出
                while chOnlineFlag != '0' and iTimeout < 15:
                    # 判断发送服务是否已经停止
                    iTimeout += 1
                    cnx.cmd_refresh(RefreshOption.TABLES)
                    time.sleep(1) 
                    strSQL = 'select online_flag from ServerList \
                               where server_ip = "%s"' % localIP
                    # global localIP
                    cursor.execute(strSQL)
                    row = cursor.fetchall()
                    chOnlineFlag = row[0][0]
                if chOnlineFlag != '0':
                    strSQL = 'update ServerList \
                                 set online_flag = "0", updated_time = now() \
                               where server_ip = "%s"' % localIP
                    # global localIP
                    cursor.execute(strSQL)
                    cnx.commit()
            
            while 1:
                # 发SIGTERM信号终止进程，并调用回调函数delpid来删除pid文件
                os.kill(pid, SIGTERM)
                time.sleep(0.1)
                
                # 关闭数据库连接
                cnx.commit()
                cursor.close()
                cnx.close()
                
                # 将提示信息打印在屏幕上
                now = datetime.datetime.now()
                sys.stdout.write(now.strftime("%Y-%m-%d %H:%M:%S")
                                  + ": 服务已被停止......\n")
                
                sys.stdout.flush()
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
                now = datetime.datetime.now()
                sys.stdout.write(now.strftime("%Y-%m-%d %H:%M:%S") 
                                 + ": 服务已被守护进程停止，移除pid文件......\n")
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def run(self):
        """
        You should overrid this method when you subclass Daemon. It will be 
        called after the process has been daemonized by start() or restart().
        """
        global vstrMSGResultCode, vstrMSGRetMsg
        global bSuccess
        global vstrSPAddress1, vstrSPAddress2, vstrSendInterface, vstrRepInterface
        global vstrUserID, vstrUserPwd, iSMSMaxLength, vstrVendorName
        global chGetVendorInfoError, chVendorID
        
        # 创建数据库连接
        global strDBhost, strDBdatabase, strDBuser, strDBpassword
        cnx = mysql.connector.connect(user=strDBuser, password=strDBpassword, 
                                      host=strDBhost, database=strDBdatabase)
        cursor = cnx.cursor()

        chFatalError = '0'
        chVendorID = ''
        
        # 程序初次启动标志
        chStartFlag = '1'
        while 1:
            # 向ServerList注册服务IP，标明在线，可以提供服务              
            args = (localIP, chStartFlag, 0, 0)
            # 获取日志文件的路径和名字
            global strSourcePath
            now = datetime.datetime.now()
            strDay = now.strftime("%Y%m%d")
            # 日志文件名中增加日期关键字
            logfile = strSourcePath + '/log/SMS' + strDay + '.log'            
            logging.basicConfig(filename=logfile, 
                                level=logging.DEBUG, 
                                # appending
                                filemode = 'a', 
                                format='%(asctime)s: -- %(levelname)s -- %(message)s')

            logging.info('注册服务和刷新本服务器状态，IP地址为%s\n' % localIP)     
            # logging.info('注册服务和刷新本服务器状态，IP地址')
            result_args = cursor.callproc('spServerRegistration', args)
            chStartFlag = '0'
            if result_args[2] != 0:
                # 出错，记录日志
                message = "服务器[%s]注册失败: %s\n"
                # global localIP
                logging.critical(message % (localIP, result_args[3])) 
                chFatalError = '1'
                # 退出循环，关闭服务
                break
        
            # 获取返回的服务状态，用于后续判断            
            for result in cursor.stored_results():
                row = result.fetchall()
            if len(row) != 1:
                logging.critical('表ServiceNow中记录数异常！')
                # 退出循环，关闭服务
                chFatalError = '1'
                break
            # row = cursor.fetchone()
            
            chTrafficLight = row[0][0]
            chInService = row[0][1]
            chNewVendorID = row[0][2]
            chVendorInService = row[0][3]
            vstrServerIP = row[0][4]
            vstrServerInService = row[0][5]
            chOnlineFlag = row[0][6]
            dtLastLogin = row[0][7]
            dtUpdatedTime = row[0][8]
            chQuitFlag = row[0][9]
        
            if chQuitFlag == '1':
                # 需要退出的情况
                break
            
            if chTrafficLight == '0' \
                or chTrafficLight == '1' \
                    and chInService == '1' \
                    and vstrServerInService != localIP \
                    and (datetime.datetime.now() - dtUpdatedTime).seconds < 30 \
                or chTrafficLight == '1' \
                    and chInService != '1' \
                    and vstrServerIP != localIP and chOnlineFlag == '1' \
                    and (datetime.datetime.now() - dtLastLogin).seconds < 10:
                # 等待3s，再去循环判断Traffic light                
                time.sleep(3)
                continue

            # 除上述情形外，则由本守护进程执行短信发送任务
            # 向系统中写日志
            # global strSourcePath
            now = datetime.datetime.now()
            strDay = now.strftime("%Y%m%d")
            logfile = strSourcePath + '/SMS' + strDay + '.log'
            # 没能由程序本身捕获到的异常，也输出到同一文件中
            self.stderr = logfile
            logging.basicConfig(filename=logfile, 
                                level=logging.DEBUG, 
                                filemode = 'a', 
                                format='%(asctime)s: -- %(levelname)s -- \
                                        %(message)s')
            logging.info('服务器%s正在执行短信发送任务，检查短信发送配置......\n' % localIP) 
                
            while True:
                # ***********************************************************
                # 设置本机为发送服务器，更新状态
                args = (localIP, 0, 0)
                result_args = cursor.callproc('spSetServerInService', args)
                if result_args[1] != 0:
                    # 出错，记录日志
                    message = "短信发送服务器[%s]状态更新失败: %s，发送服务将停止\n"
                    logging.critical(message % (localIP, result_args[2])) 
                    chFatalError = '1'
                    # 退出循环，关闭服务
                    break    
                                
                # *************************************************************
                # 开始发送短信
                # 1, 获取通道供应商信息
                # vstrSPAddress1 = ''
                if chVendorID != chNewVendorID:
                    """ 
                    说明已经切换了通道供应商，重新获取该供应商的相关配置信息
                    初始运行时，chVendorID = ''，所以同样视为需要获取该供应商信息的情况
                    """
                    # 准备下一次比较用，看是否切换了供应商
                    chVendorID = chNewVendorID
                    
                    # 调用函数，获取通道供应商信息
                    # 这里是获取本身信息
                    self.GetVendorInfo(cursor, chVendorID, '0') 
                    if chGetVendorInfoError == '1':
                        # 由于有主键索引，这种情况不可能出现
                        logging.critical('表Vendors中供应商ID为[%s]的记录条数异常' \
                                          % chVendorID)
                        # 当前供应商记录异常，尝试切换
                        self.GetVendorInfo(cursor, chVendorID, '1') 
                        if chGetVendorInfoError == '1':
                            logging.critical('表Vendors中供应商记录数异常......\n') 
                    logging.info('目前短信供应商为[%s]的http服务器[%s]......\n' 
                                  % (vstrVendorName, vstrSPAddress1)) 
                                                                      
                # 2，设置待发送短信为“正在发送中”
                args = (localIP, 0, 0)
                result_args = cursor.callproc('spSetSMStoSend', args)
                if result_args[1] != 0:
                    # 出错，记录日志
                    message = '设置短信[%s]状态更新失败: %s，发送服务将停止\n'
                    logging.critical(message % (localIP, result_args[2])) 
                    chFatalError = '1'
                    # 退出循环，关闭服务
                    break                 
                    
                # 3，读取待发送短信，一条一条地发送
                # while 1:
                args = (localIP, 0, 0)
                result_args = cursor.callproc('spGetSMStoSend', args)
                for result in cursor.stored_results():
                    row = result.fetchone()
                    while row is not None:
                        # 4, 组包，发送
                        # sys.stdout.write(','.join(row) + '\n')
                        strSMSID = row[0]
                        strMobileNumber = row[1]
                        strAppID = row[2]
                        vstrSMSDetail = row[3].strip()
                        """
                        sys.stdout.write(strSMSID + '-smsid\n')
                        sys.stdout.write(strMobileNumber + '-phonenumber\n')
                        sys.stdout.write(strAppID + '-appid\n')
                        sys.stdout.write(vstrSMSDetail + '-detail\n')
                        """
                        # 组包, 要考虑拆分的可能
                        iSplitCount = len(vstrSMSDetail) // iSMSMaxLength + 1
                        vstrSPAddress = vstrSPAddress1
                        for y in range(iSplitCount):
                            # 拆分后的短信依次发送，如果短信不用拆分，这里也只循环
                            vstrSMS = vstrSMSDetail[iSMSMaxLength * y:
                                                    iSMSMaxLength * (y + 1)]
                            """
                            考虑同一短信通道服务商提供了两个http服务IP的情况，在3次超时
                            的情况下切换到另外一个IP。
                            第一次优先使用第一个IP服务器
                            """                                                   
                            while 1:
                                # 组包 
                                # 必须放在这里，因为当发送IP服务器切换了，需要重新组包 
                                urlstring = generateURL(vstrSPAddress, 
                                                        vstrSendInterface, 
                                                        strSMSID, 
                                                        vstrUserID, 
                                                        vstrUserPwd, 
                                                        strMobileNumber, 
                                                        vstrSMS)
                                logging.info('当前短信串[%s]......\n' % urlstring)    

                                # 调用http服务，发送拆分后的短信, 3次超时机会
                                SendMessage(urlstring) 
                                if bSuccess:
                                    # 成功发送，不需要再次发送
                                    break
                                # 发送失败，记录日志
                                logging.error('短信供应商[%s]的http服务器[%s]异常, ' \
                                              '短信发送失败......\n' 
                                              % (vstrVendorName, vstrSPAddress))
                                
                                if vstrSPAddress == vstrSPAddress2 \
                                   or vstrSPAddress2 == '':
                                    # 已经切换了或者根本没有提供第二个ip服务器，则跳过
                                    # 换到另一个vendor，并重新发送
                                    # 调用存储过程spVendorFailover(chVendorID)
                                    self.GetVendorInfo(cursor, chVendorID, '1') 
                                    vstrSPAddress = vstrSPAddress1
                                    logging.info('切换到供应商[%s]的http服务器[%s]......\n' 
                                                  % (vstrVendorName, vstrSPAddress)) 
                                else:
                                    # 切换到第二个http服务器
                                    vstrSPAddress = vstrSPAddress2
                                    # 需要记录切换日志
                                    logging.info('切换到http服务器[%s]......\n' 
                                                 % vstrSPAddress) 
                                # time.sleep(2)    
                            # 5, 发送状态回填
                            
                            args = (localIP, strSMSID, vstrMSGResultCode, 
                                    vstrMSGRetMsg, chVendorID, 0, 0)
                            result_args = cursor.callproc('spSetSendingStatus', args)
                                
                            if vstrMSGResultCode != '0':
                                # 如有一条发送报错，则不再发送剩余的拆分后短信
                                logging.error('序号为%s的短信发送失败, 原因为%s\n' 
                                              % (strSMSID, vstrMSGRetMsg))
                                break
                                  
                            """
                            需要切换到另一短信供应商的情况：
                                1、致命的错误信息，如发送的ID或密码配置错误，可用条数不足
                                  等导致后续发送都将失败的情况
                                2、所有该供应商提供的http服务器均超时
                             本次发送失败的短信在以后的发送过程中重发
                            """
                            # 6, 循环发送下一条
                        row = result.fetchone()               
                    # 
                    
                # *************************************************************
                # 执行完一轮短信发送后的状态检查工作，以确定是继续发送还是退出当前发送进程
                # 接收到退出守护进程信号，停止发送，关闭数据库连接
                time.sleep(0.2) 
                strSQL = 'select a.traffic_light, a.in_service_flag, a.vendor_id,\
                                 b.online_flag, a.server_ip, b.quit_flag \
                            from ServiceNow a, ServerList b \
                           where a.server_in_service = b.server_ip \
                                 and b.server_ip = "%s"' % localIP
                # logging.info('服务器[%s]正在执行短信发送任务，检查短信发送配置......\n' % localIP)            
                     
                cursor.execute(strSQL)
                row = cursor.fetchall()
                iRowCount = cursor.rowcount
                if iRowCount != 1:
                    # 数据异常
                    chFatalError = '1'
                    message = '表ServiceNow中记录条数异常，当前记录数为{}条......\n'
                    logging.critical(message.format(str(iRowCount)))
                    break
                
                chTrafficFlag = ''
                # 由于前面用的fetchall，因此，虽然只有一条返回结果，还是要用[0]来代表第一条记录
                chTrafficFlag = row[0][0]
                chNewVendorID = row[0][2]
                chOnlineFlag = row[0][3]
                vstrServerIP = row[0][4]
                chQuitFlag = row[0][5]
                
                if chQuitFlag == '1' or chTrafficFlag == '0':
                    # 停止发送短信
                    break
       
                if vstrServerIP != localIP:
                    """
                     指定发送服务器不是本机并且在线，且上次登录时间不早于10s之前，需要把发送任务移交
                     给给该服务器
                    """
                    strSQL = 'select b.online_flag, b.last_login \
                                from ServiceNow a, ServerList b \
                               where a.server_ip = b.server_ip'
                    cursor.execute(strSQL)
                    row = cursor.fetchall()
                    if cursor.rowcount != 0:
                        # 
                        dtLastLogin = row[0][1]
                        if row[0][0] == '1' \
                           and (datetime.datetime.now() - dtLastLogin).seconds < 10:
                            logging.info('指定发送服务器不是本机并且在线，且上次登录时间不早\
                                         于10s之前，需要把发送任务移交给给该服务器......\n')  
                            break
                    
                # 其余情况，继续由本守护进程发送短信
                # time.sleep(0.2)
                time.sleep(5)
            if chQuitFlag == '1':
                # 需要退出daemon
                logging.info('检测到需要退出守护进程的信号，退出准备中:\n')
                strSQL = 'update ServerList \
                             set online_flag = "0", updated_time = now(), \
                                 last_logout = now() \
                           where server_ip = "%s"' % localIP
                cursor.execute(strSQL)   
                cnx.commit()       
                break
            if chFatalError == '1':
                logging.critical('系统发生异常，退出准备中:\n')
                break    
            # 其余情况，本守护进程standby，循环判断traffic light，伺机接管发送服务        
            logging.info('本进程standby...:\n')        
        
        # 退出进程
        # 关闭数据库连接
        cnx.commit()
        cursor.close()
        cnx.close()

        sys.stdout.flush()
        sys.stderr.flush()


if __name__ == "__main__":
    # 实例化
    # 请确保运行此程序的用户对/user/local/sms-pid有读写权限
    sms_daemon = Daemon('/usr/local/sms-pid/sms.pid', '/dev/null', '/dev/null', 
                        './log/SMS.log')

    try:
        """
        调用方式 python daemon.py start|stop|restart，是否增加一个标志，只停短信发送
        服务，并不退出守护进程？
        """
        fundction_code = sys.argv[1]  
    except Exception as e:
        fundction_code = ''

    if (fundction_code == 'start'):
        sms_daemon.start()
    if (fundction_code == 'stop'):
        sms_daemon.stop()        
    if (fundction_code == 'restart'):
        sms_daemon.restart()


