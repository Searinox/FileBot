__version__="1.95"
__author__=u"Searinox Navras"


"""
INIT
"""


import base64
import time
import datetime
import json
import threading
import sys
import os
import mmap
import shutil
import ssl
import urllib3
import ctypes
import win32con
import win32process
from PyQt5.QtCore import (PYQT_VERSION_STR,QObject,pyqtSignal,QByteArray,Qt,QEvent,QTimer,QCoreApplication,qInstallMessageHandler)
from PyQt5.QtWidgets import (QApplication,QLabel,QListView,QWidget,QSystemTrayIcon,QMenu,QLineEdit,QMainWindow,QFrame,QAbstractItemView,QGroupBox)
from PyQt5.QtGui import (QIcon,QImage,QPixmap,QFont,QColor,QStandardItemModel,QStandardItem)

def Get_B64_Resource(input_path):
    import resources_base64
    return resources_base64.Get_Resource(input_path)

PYQT5_MAX_SUPPORTED_COMPILE_VERSION="5.12.2"

MAX_BOT_USERS_BY_CPU_ARCHITECTURE={"32":36,"64":100}

TELEGRAM_API_REQUEST_TIMEOUT_SECONDS=4
TELEGRAM_API_MAX_GLOBAL_IMS=30
TELEGRAM_API_MAX_GLOBAL_TIME_INTERVAL_SECONDS=1
TELEGRAM_API_UPLOAD_TIMEOUT_SECONDS=60*60
TELEGRAM_API_DOWNLOAD_CHUNK_BYTES=256*256
TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES=1024*1024*50
TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES=1024*1024*20
TELEGRAM_API_MAX_IM_SIZE_BYTES=4096

BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS=30
BOT_LOCK_PASSWORD_CHARACTERS_MIN=4
BOT_LOCK_PASSWORD_CHARACTERS_MAX=32

WEB_REQUEST_CONNECT_TIMEOUT_SECONDS=5
MAX_7ZIP_TASKS_PER_USER=3

UI_COMMAND_HISTORY_MAX=50
UI_OUTPUT_ENTRIES_MAX=5000

MAINTHREAD_HEARTBEAT_SECONDS=0.1
PENDING_ACTIVITY_HEARTBEAT_SECONDS=0.05
MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS=60
COMMAND_CHECK_INTERVAL_ACTIVE_SECONDS=0.18
COMMAND_CHECK_INTERVAL_MINIMIZED_SECONDS=0.4
SERVER_TIME_RESYNC_INTERVAL_SECONDS=60*60*8
BOT_LISTENER_THREAD_HEARTBEAT_SECONDS=0.8
FILE_READ_ATTEMPTS_MAX=5
FILE_READ_ATTEMPT_FAIL_RETRY_DELAY_SECONDS=0.25
USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS=0.1
USER_MESSAGE_HANDLER_SENDMSG_WAIT_POLLING_SECONDS=0.1
UI_CLIPBOARD_COPY_TIMEOUT_SECONDS=1
UI_CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS=0.1
TASKS_7ZIP_THREAD_HEARTBEAT_SECONDS=0.2
TASKS_7ZIP_UPDATE_INTERVAL_SECONDS=1.25
TASKS_7ZIP_DELETE_TIMEOUT_SECONDS=1.5
UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS=0.055

UI_SCALE_MODIFIER=1.125

FONTS={"<reference_point_size>":8,
       "general":{"type":"Monospace","scale":1,"properties":[]},
       "status":{"type":"Arial","scale":1,"properties":["bold"]},
       "log":{"type":"Consolas","scale":1,"properties":["bold"]}}
COLOR_SCHEME={"window_text":"000000",
              "window_background":"FFFFF0",
              "selection_text":"FFFFF0",
              "selection_background":"3B3BFF",
              "background_IO":"000000",
              "background_IO_disabled":"3D3D3D",
              "input_text":"00FF00",
              "scrollbar_text":"000000",
              "scrollbar_background":"CFCFA4",
              "scrollarea_background":"E8E8BB",
              "status_username":"000090",
              "status_ok":"009000",
              "status_warn":"908F00",
              "status_error":"900000",
              "output_border":"282828",
              "output":{"<DEFAULT>":"FFFFFF",
                        "MAINTHRD":"A0FFFF",
                        "BOTLSTNR":"FFA0FF",
                        "MSGHNDLR":"FFFFA0",
                        "7ZTSKHND":"FFC85A",
                        "UCONSOLE":"A0FFA0"}}

STARTUP_MESSAGE_ADDITIONAL_TEXT=u"COMMAND LINE:\n"+\
    u"/minimized: starts the application minimized to system tray\n"+\
    u"/stdout: output log to stdout in addition to window"


"""
DEFS
"""


GetTickCount64=ctypes.windll.kernel32.GetTickCount64
GetTickCount64.restype=ctypes.c_uint64
GetTickCount64.argtypes=()

def Versions_Str_Equal_Or_Less(version_expected,version_actual):
    version_compliant=False
    compared_versions=[]
    for compared_version in [version_expected,version_actual]:
        compared_versions+=[[int(number.strip()) for number in compared_version.split(".")]]
    if compared_versions[1][0]<=compared_versions[0][0]:
        if compared_versions[1][0]<compared_versions[0][0]:
            version_compliant=True
        elif compared_versions[1][1]<=compared_versions[0][1]:
            if compared_versions[1][1]<compared_versions[0][1]:
                version_compliant=True
            elif compared_versions[1][2]<=compared_versions[0][2]:
                version_compliant=True
    return version_compliant

def Get_Runtime_Environment():
    retval={"working_dir":u"","running_from_source":False,"arguments":[]}

    sys_exe=sys.executable

    retval["arguments"]=sys.argv
    retval["working_dir"]=os.path.realpath(os.path.dirname(sys_exe))
    retval["system32"]=os.path.join(os.environ["WINDIR"],u"System32")

    if os.path.basename(sys_exe).lower()==u"python.exe":
        if len(retval["arguments"])>0:
            if retval["arguments"][0].replace(u"\"",u"").lower().strip().endswith(u".py"):
                retval["working_dir"]=os.path.realpath(os.path.dirname(retval["arguments"][0]))
                retval["arguments"]=retval["arguments"][1:]
                retval["running_from_source"]=True

    return retval

def Make_TLS_Connection_Pool(input_allowed_TLS_algorithms):
    ssl_cert_context=ssl.create_default_context()
    ssl_cert_context.check_hostname=True
    ssl_cert_context.set_ciphers(input_allowed_TLS_algorithms)
    ssl_cert_context.verify_mode=ssl.CERT_REQUIRED
    ssl_cert_context.options|=ssl.OP_NO_SSLv2
    ssl_cert_context.options|=ssl.OP_NO_SSLv3
    ssl_cert_context.options|=ssl.OP_NO_TLSv1
    ssl_cert_context.options|=ssl.OP_NO_TLSv1_1
    return urllib3.PoolManager(cert_reqs="CERT_REQUIRED",ssl_context=ssl_cert_context)

def terminate_with_backslash(input_string):
    if input_string.endswith(u"\\")==False:
        return input_string+u"\\"
    return input_string

def sanitize_path(input_path):
    for bad_pattern in [u"\\\\",u"\\.\\",u"\\.\\",u"?",u"*",u"|",u"<",u">",u"\""]:
        if bad_pattern in input_path:
            return u"<BAD PATH>"
    if len(input_path)-1>len(input_path.replace(u":",u"")):
        return u"<BAD PATH>"
    return input_path

def OS_Uptime_Seconds():
    return GetTickCount64()/1000.0

def readable_size(input_size):
    if input_size<1024:
        return str(input_size)+" Bytes"
    if input_size<1024**2:
        return str(round(input_size/1024.0,2))+" KB"
    if input_size<1024**3:
        return str(round(input_size/1024.0**2,2))+" MB"
    return str(round(input_size/1024.0**3,2))+" GB"


"""
OBJS
"""


class ShellProcess(object):
    def __init__(self,input_path_system32,input_command):
        input_path_system32=input_path_system32

        result=win32process.CreateProcess(None,u"\""+input_path_system32+u"cmd.exe\" /c \""+input_command+u" \"",None,None,0,win32process.CREATE_NO_WINDOW|win32process.CREATE_UNICODE_ENVIRONMENT,None,None,win32process.STARTUPINFO())
        if result:
            self.process_handle=result[0]
            self.process_ID=result[2]
        return

    def IS_RUNNING(self): 
        return win32process.GetExitCodeProcess(self.process_handle)==win32con.STILL_ACTIVE

    def PID(self):
        return self.process_ID

    def WAIT(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        return


class Logger(object):
    def __init__(self,input_path_system32,input_log_path=u""):
        self.logging_path=input_log_path
        self.log_file_handle=None
        self.log_lock=threading.Lock()
        self.output_stdout=threading.Event()
        self.output_stdout.clear()
        self.active_signaller=None
        if self.logging_path!=u"":
            ShellProcess(input_path_system32,u"\""+input_path_system32+u"compact.exe\" /a /c \""+input_log_path+u"\"").WAIT()
        self.is_active=threading.Event()
        self.is_active.clear()
        return

    def ACTIVATE(self):
        try:
            self.log_file_handle=open(self.logging_path,"a")
        except:
            try:
                self.log_file_handle.close()
            except:
                pass
            self.log_file_handle=None

        self.is_active.set()

        if self.log_file_handle is None:
            self.LOG(u"WARNING: Default target log file could not be written to. Logging will not save to file.")
        return

    def LOG_TO_STDOUT(self,input_state):
        if input_state==True:
            self.output_stdout.set()
        else:
            self.output_stdout.clear()
        return

    def DEACTIVATE(self):
        self.log_lock.acquire()
        self.is_active.clear()
        try:
            if self.log_file_handle is not None:
                try:
                    self.log_file_handle.close()
                except:
                    pass
                self.log_file_handle=None
        except:
            pass
        self.log_lock.release()
        return

    def ATTACH_SIGNALLER(self,input_signaller):
        self.log_lock.acquire()
        self.active_signaller=input_signaller
        self.log_lock.release()
        return

    def DETACH_SIGNALLER(self):
        self.log_lock.acquire()
        self.active_signaller=None
        self.log_lock.release()
        return

    def LOG(self,source,input_data=u""):
        if self.is_active.is_set()==False:
            return

        if input_data!=u"":
            source_literal=str(source)
            input_literal=str(input_data)
        else:
            source_literal=u""
            input_literal=str(source)
            source=""
        if source!="":
            source_literal=u" ["+source_literal+u"] "
        else:
            source_literal=u" "

        msg=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+source_literal+input_literal+u"\n"

        self.log_lock.acquire()

        if self.is_active.is_set()==False:
            self.log_lock.release()
            return

        if self.log_file_handle is not None:
            try:
                self.log_file_handle.write(msg)
                self.log_file_handle.flush()
            except:
                pass

        if self.output_stdout.is_set()==True:
            try:
                sys.stdout.write(msg)
            except:
                pass

        if self.active_signaller is not None:
            try:
                self.active_signaller.SEND_EVENT("logger_new_entry",msg)
            except:
                pass

        self.log_lock.release()
        return


class Time_Provider(object):
    def __init__(self,input_allowed_TLS_algorithms):
        global WEB_REQUEST_CONNECT_TIMEOUT_SECONDS

        self.request_pool=Make_TLS_Connection_Pool(input_allowed_TLS_algorithms)
        self.request_timeout=urllib3.Timeout(connect=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS,read=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS)
        self.origin_time=datetime.datetime(1970,1,1)
        self.lock_time_delta=threading.Lock()
        self.lock_subscribers=threading.Lock()
        self.lock_sync=threading.Lock()
        self.time_delta=0
        self.signal_subscribers=[]
        return

    def ADD_SUBSCRIBER(self,input_subscriber):
        self.lock_subscribers.acquire()
        if input_subscriber not in self.signal_subscribers:
            self.signal_subscribers+=[input_subscriber]
        self.lock_subscribers.release()
        return

    def REMOVE_SUBSCRIBER(self,input_subscriber):
        self.lock_subscribers.acquire()
        for i in range(len(self.signal_subscribers)):
            if self.signal_subscribers[i]==input_subscriber:
                del self.signal_subscribers[i]
                break
        self.lock_subscribers.release()
        return

    def CURRENT_SERVER_TIME(self):
        self.lock_time_delta.acquire()
        get_delta=self.time_delta
        self.lock_time_delta.release()
        return round(OS_Uptime_Seconds()+get_delta,3)

    def SYNC(self):
        time_difference=0

        self.lock_sync.acquire()

        success=self.update_server_time_from_internet()
        if success==True:
            time_difference=self.current_local_machine_time_delta_str()

            self.lock_subscribers.acquire()
            for subscriber in self.signal_subscribers:
                subscriber.SEND_EVENT("report_timesync_clock_bias",time_difference)
            self.lock_subscribers.release()

        self.lock_sync.release()
        return {"success":success,"time_difference":time_difference}

    def retrieve_current_UTC_internet_time(self):
        response=self.request_pool.request(method="GET",url="https://worldtimeapi.org/api/timezone/Etc/UTC.txt",preload_content=True,chunked=False,timeout=self.request_timeout)
        if response.status==200:
            timestr=str(response.data,"utf8")
        else:
            raise Exception(u"Could not get time.")
        quot1=timestr.find("\ndatetime: ")
        quot1+=len("\ndatetime: ")
        quot2=quot1+timestr[quot1+1:].find("+")
        quot2+=1
        timestr=timestr[quot1:quot2-3]
        return (datetime.datetime.strptime(timestr,"%Y-%m-%dT%H:%M:%S.%f")-self.origin_time).total_seconds()

    def update_server_time_from_internet(self):
        update_success=False

        try:
            get_new_delta=self.retrieve_current_UTC_internet_time()-OS_Uptime_Seconds()
            update_success=True
        except:
            pass

        if update_success==True:
            self.lock_time_delta.acquire()
            self.time_delta=get_new_delta
            self.lock_time_delta.release()

        return update_success

    def current_local_machine_time_delta_str(self):
        time_difference=round(float((datetime.datetime.utcnow()-self.origin_time).total_seconds())-self.CURRENT_SERVER_TIME(),3)
        if time_difference>0:
            retval="+"+str(time_difference)
        else:
            retval=str(time_difference)
        return retval


class Task_Handler_7ZIP(object):
    def __init__(self,input_path_system32,input_path_7zip,input_7zip_binary_base64,input_max_per_user,input_logger=None):
        global TASKS_7ZIP_DELETE_TIMEOUT_SECONDS

        self.path_system32=input_path_system32
        self.instances_7zip=[]
        self.lock_instances_7zip=threading.Lock()
        self.lock_list_end_tasks=threading.Lock()
        self.active_logger=input_logger
        self.working_thread=threading.Thread(target=self.work_loop)
        self.working_thread.daemon=True
        self.binary_7zip_read=None
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.max_tasks_per_user=input_max_per_user
        self.list_end_tasks_PIDs=[]
        self.list_end_tasks_users=[]
        self.task_delete_timeout_milliseconds=TASKS_7ZIP_DELETE_TIMEOUT_SECONDS*1000
        
        self.path_7zip_bin=os.path.join(input_path_7zip,u"7z.exe")
        write_7z_binary=None

        try:
            write_7z_binary=open(self.path_7zip_bin,"w+b")
            write_7z_binary.write(base64.decodebytes(input_7zip_binary_base64))
            self.binary_7zip_read=open(self.path_7zip_bin,"rb")
            write_7z_binary.close()
        except:
            for close_binary in [write_7z_binary,self.binary_7z_read]:
                if close_binary is not None:
                    try:
                        close_binary.close()
                    except:
                        pass

            write_7z_binary=None
            self.binary_7zip_read=None
            raise Exception(u"The 7-ZIP binary could not be written. Make sure you have write permissions to the application folder.")

        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("7ZTSKHND",input_text)
        return

    def START(self):
        self.working_thread.start()
        return

    def REQUEST_STOP(self):
        self.request_exit.set()
        return

    def CONCLUDE(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        self.working_thread.join()
        try:
            self.binary_7zip_read.close()
        except:
            self.binary_7zip_read=None
        return
    
    def IS_RUNNING(self):
        return self.has_quit.is_set()==False    

    def GET_MAX_TASKS_PER_USER(self):
        return self.max_tasks_per_user

    def NEW_TASK(self,target_path,originating_user):
        if self.request_exit.is_set()==True:
            return {"result":"ERROR","full_target":u""}

        if os.path.isfile(target_path)==True:
            folder_path=target_path[:target_path.rfind(u"\\")+1]
        else:
            folder_path=target_path[:target_path[:-1].rfind(u"\\")+1]
            if folder_path==u"":
                folder_path=target_path[:target_path[:-1].rfind(u":")+1]

        archive_filename=target_path[target_path.rfind(u"\\")+1:]
        if archive_filename==u"":
            archive_filename=target_path[target_path[:-1].rfind(u"\\")+1:]
            if archive_filename[-1].endswith(u"\\")==True:
                archive_filename=archive_filename[:-1]
        archive_filename_path=archive_filename
        archive_filename=archive_filename.replace(u":",u"")

        zip_command=u"\""+self.path_7zip_bin+u"\" a -mx9 -t7z \""+archive_filename+u".7z.TMP\" \""+archive_filename_path+u"\""
        folder_command=u"cd/ & cd /d \""+folder_path+u"\""
        rename_command=u"ren \""+archive_filename+u".7z.TMP\" \""+archive_filename+u".7z\""
        prompt_commands=folder_command+u" & "+zip_command+u" & "+rename_command
        folder_path=terminate_with_backslash(folder_path)
        full_target=folder_path+archive_filename.lower()

        if os.path.exists(full_target+u".7z")==False:
            self.lock_instances_7zip.acquire()
            user_task_total=0
            for instance in self.instances_7zip:
                if instance["user"]==originating_user:
                    user_task_total+=1
            if user_task_total==self.max_tasks_per_user:
                self.lock_instances_7zip.release()
                return {"result":"MAXREACHED","full_target":u""}
            if self.request_exit.is_set()==True:
                self.lock_instances_7zip.release()
                return {"result":"ERROR","full_target":u""}
            try:
                new_process=ShellProcess(self.path_system32,prompt_commands)
                self.instances_7zip+=[{"process":new_process,"temp_file":full_target+u".7z.TMP","user":originating_user,"new":True}]
                self.lock_instances_7zip.release()

                return {"result":"CREATED","full_target":full_target}
            except:
                self.lock_instances_7zip.release()
                return {"result":"ERROR","full_target":u""}
        else:
            return {"result":"EXISTS","full_target":full_target}

    def GET_TASKS(self):
        retval=[]

        self.lock_instances_7zip.acquire()
        for instance in self.instances_7zip:
            target_location=instance["temp_file"]
            if target_location.lower().endswith(u".7z.tmp"):
                target_location=target_location[:-len(u".7z.tmp")]
            retval+=[{"pid":instance["process"].PID(),"target":target_location,"user":instance["user"]}]
        self.lock_instances_7zip.release()

        return retval

    def END_TASKS(self,input_users,input_PIDs=[]):
        self.lock_list_end_tasks.acquire()
        self.list_end_tasks_users+=input_users
        self.list_end_tasks_PIDs+=input_PIDs
        self.lock_list_end_tasks.release()
        return

    def work_loop(self):
        global TASKS_7ZIP_THREAD_HEARTBEAT_SECONDS
        global TASKS_7ZIP_UPDATE_INTERVAL_SECONDS

        get_end_task_list_PIDs=[]
        get_end_task_list_users=[]
        update_interval_milliseconds=TASKS_7ZIP_UPDATE_INTERVAL_SECONDS*1000

        self.log(u"7-ZIP Task Handler started.")
        last_update=GetTickCount64()-update_interval_milliseconds
        while self.request_exit.is_set()==False:
            time.sleep(TASKS_7ZIP_THREAD_HEARTBEAT_SECONDS)

            if GetTickCount64()-last_update>=update_interval_milliseconds:
                self.update_7zip_tasks()
                last_update=GetTickCount64()

            self.lock_list_end_tasks.acquire()
            if len(self.list_end_tasks_PIDs)+len(self.list_end_tasks_users)>0:
                get_end_task_list_PIDs=self.list_end_tasks_PIDs[:]
                self.list_end_tasks_PIDs=[]
                get_end_task_list_users=self.list_end_tasks_users[:]
                self.list_end_tasks_users=[]
            self.lock_list_end_tasks.release()

            if len(get_end_task_list_PIDs)+len(get_end_task_list_users)>0:
                self.end_7zip_tasks(get_end_task_list_users,get_end_task_list_PIDs)
                get_end_task_list_PIDs=[]
                get_end_task_list_users=[]

        self.update_7zip_tasks()
        self.end_7zip_tasks([u"*"])

        self.log(u"7-ZIP Task Handler has exited.")
        self.has_quit.set()
        return

    def update_7zip_tasks(self):
        self.lock_instances_7zip.acquire()

        for i in reversed(range(len(self.instances_7zip))):
            if self.instances_7zip[i]["new"]==True:
                self.instances_7zip[i]["new"]=False
                self.log(u"Task with PID="+str(self.instances_7zip[i]["process"].PID())+u" TEMP=\""+self.instances_7zip[i]["temp_file"]+u"\" has been added.")
            still_running=True
            try:
                still_running=self.instances_7zip[i]["process"].IS_RUNNING()
            except:
                pass
            if still_running==False:
                self.log(u"Task with PID="+str(self.instances_7zip[i]["process"].PID())+u" TEMP=\""+self.instances_7zip[i]["temp_file"]+u"\" has finished.")
                del self.instances_7zip[i]

        self.lock_instances_7zip.release()
        return

    def end_7zip_tasks(self,list_users,list_PIDs=[]):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        taskkill_list=[]
        terminate_all=False
        terminated_total=0

        if len(list_users)==1:
            if list_users[0]==u"*":
                terminate_all=True

        self.lock_instances_7zip.acquire()

        for i in reversed(range(len(self.instances_7zip))):
            get_PID=self.instances_7zip[i]["process"].PID()
            get_user=self.instances_7zip[i]["user"].lower()
            terminate=False

            if terminate_all==True:
                terminate=True
            elif any(username.lower()==get_user for username in list_users):
                terminate=True
            else:
                for i in range(len(list_PIDs)):
                    if list_PIDs[i]==get_PID:
                        terminate=True
                        del list_PIDs[i]
                        break

            if terminate==True:
                self.log(u"Terminating ongoing 7-ZIP batch with PID="+str(get_PID)+u" and temporary file \""+self.instances_7zip[i]["temp_file"].lower()+u"\".")
                taskkill_list+=[{"process":ShellProcess(self.path_system32,u"\""+self.path_system32+u"taskkill.exe\" /f /t /pid "+str(get_PID)),"file":self.instances_7zip[i]["temp_file"]}]
                del self.instances_7zip[i]
                terminated_total+=1

        self.lock_instances_7zip.release()

        for taskkill in taskkill_list:
            taskkill["process"].WAIT()

        for taskkill in taskkill_list:
            delete_attempt_made=False
            start_time=GetTickCount64()
            while (os.path.isfile(taskkill["file"])==True and GetTickCount64()-start_time<self.task_delete_timeout_milliseconds) or delete_attempt_made==False:
                try:
                    delete_attempt_made=True
                    os.remove(taskkill["file"])
                except:
                    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

        if terminated_total==0:
            self.log(u"No 7-ZIP tasks were terminated.")

        return


class Telegram_Message_Rate_Limiter(object):
    def __init__(self,input_max_messages,input_time_interval_seconds):
        self.timer_list=[]
        self.max_messages=input_max_messages
        self.time_interval_milliseconds=input_time_interval_seconds*1000
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.lock_timerlist=threading.Lock()
        return

    def timer_list_size_and_cleanup(self):
        for i in reversed(range(len(self.timer_list))):
            if self.timer_list[i]<GetTickCount64()-self.time_interval_milliseconds:
                del self.timer_list[i]
            else:
                break
        return len(self.timer_list)

    def WAIT_FOR_CLEAR_AND_SEND(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        if self.request_exit.is_set()==True:
            return

        send_ok=False
        while send_ok==False and self.request_exit.is_set()==False:
            self.lock_timerlist.acquire()
            if self.timer_list_size_and_cleanup()>=self.max_messages-1:
                self.lock_timerlist.release()
                time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS/1000)
            else:
                self.timer_list+=[GetTickCount64()]
                self.lock_timerlist.release()
                send_ok=True

        return

    def DEACTIVATE(self):
        self.request_exit.set()
        return


class Telegram_Bot(object):
    def __init__(self,input_token,input_allowed_TLS_algorithms):
        global WEB_REQUEST_CONNECT_TIMEOUT_SECONDS
        global TELEGRAM_API_REQUEST_TIMEOUT_SECONDS
        global TELEGRAM_API_UPLOAD_TIMEOUT_SECONDS

        self.request_pool=Make_TLS_Connection_Pool(input_allowed_TLS_algorithms)
        self.timeout_web=urllib3.Timeout(connect=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS,read=TELEGRAM_API_REQUEST_TIMEOUT_SECONDS)
        self.timeout_download=urllib3.Timeout(connect=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS,read=TELEGRAM_API_REQUEST_TIMEOUT_SECONDS)
        self.timeout_upload=urllib3.Timeout(connect=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS,read=TELEGRAM_API_UPLOAD_TIMEOUT_SECONDS)
        self.bot_token=input_token
        self.is_stopped=threading.Event()
        self.is_stopped.clear()
        self.active_rate_limiter=None
        self.base_web_url="https://api.telegram.org/bot"+self.bot_token+"/"
        self.base_file_url="https://api.telegram.org/file/bot"+self.bot_token+"/"
        return

    def perform_web_request(self,input_method,input_url,input_args):
        if self.active_rate_limiter is not None:
            if input_method=="POST":
                self.active_rate_limiter.WAIT_FOR_CLEAR_AND_SEND()
        if self.is_stopped.is_set()==True:
            return {"ok":False,"result":None}

        response=None
        try:
            response=self.request_pool.request(method=input_method,fields=input_args,url=input_url,preload_content=True,chunked=False,timeout=self.timeout_web)
            response=json.loads(response.data)
        except:
            pass

        if response is not None:
            if "ok" in response:
                if "description" in response:
                    return {"ok":response["ok"],"result":response["description"]}
                elif "result" in response:
                    return {"ok":response["ok"],"result":response["result"]}

        return {"ok":False,"result":None}

    def file_download_get_stream(self,input_id,input_args=None):
        if self.is_stopped.is_set()==True:
            return None

        response=None
        try:
            response=self.request_pool.request(method="GET",fields=input_args,url=self.base_file_url+input_id,preload_content=False,chunked=False,timeout=self.timeout_download)
        except:
            pass
        if response is not None:
            if response.status in [200,201]:
                return response

        return None

    def file_upload_from_handle(self,input_chat_id,input_file_handle):
        if self.is_stopped.is_set()==True:
            return "Bot is stopped."
        if self.active_rate_limiter is not None:
            self.active_rate_limiter.WAIT_FOR_CLEAR_AND_SEND()
        if self.is_stopped.is_set()==True:
            return "Bot is stopped."

        try:
            input_file_handle.seek(0,2)
            file_size=input_file_handle.tell()
            if file_size==0:
                return "Empty file."
            if file_size>TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES:
                return "File too big."
            input_file_handle.seek(0,0)
            file_name=os.path.basename(input_file_handle.name)
            response=self.request_pool.request(method="POST",fields={"chat_id":input_chat_id,"document":(file_name,input_file_handle.read())},url=self.base_web_url+"sendDocument",preload_content=True,chunked=True,timeout=self.timeout_upload)
            if response is None or response.status not in [200,201]:
                return "Upload error."
        except:
            return "Upload error."

        return ""

    def Get_Bot_Info(self):
        if self.is_stopped.is_set()==True:
            raise Exception("Bot is stopped.")

        response=self.perform_web_request("GET",self.base_web_url+"getMe",None)
        if response["ok"]==True:
            return response["result"]
        else:
            if response["result"] is not None:
                if type(response["result"])==str:
                    if response["result"].lower().strip()=="not found":
                        raise Exception("Invalid token.")

        raise Exception("Response error.")

    def Get_Messages(self,input_id):
        if self.is_stopped.is_set()==True:
            raise Exception("Bot is stopped.")

        response=self.perform_web_request("GET",self.base_web_url+"getUpdates",{"offset":input_id,"allowed_updates":["message"]})
        if response["ok"]==True:
            return response["result"]

        raise Exception("Response error.")

    def Send_Message(self,input_chat_id,input_message):
        if self.is_stopped.is_set()==True:
            raise Exception("Bot is stopped.")

        response=self.perform_web_request("POST",self.base_web_url+"sendMessage",{"chat_id":input_chat_id,"text":input_message})
        if response["ok"]==True:
            return response["result"]

        raise Exception("Response error.")

    def Send_File(self,input_chat_id,input_file_path):
        global FILE_READ_ATTEMPT_FAIL_RETRY_DELAY_SECONDS
        global FILE_READ_ATTEMPTS_MAX

        if self.is_stopped.is_set()==True:
            return "Bot is stopped."

        file_open_attempts=0
        file_handle=None

        while file_handle is None and file_open_attempts<FILE_READ_ATTEMPTS_MAX and self.is_stopped.is_set()==False:
            try:
                file_handle=open(input_file_path,"rb",buffering=0)
            except:
                file_handle=None
                file_open_attempts+=1
                if file_open_attempts<FILE_READ_ATTEMPTS_MAX and self.is_stopped.is_set()==False:
                    time.sleep(FILE_READ_ATTEMPT_FAIL_RETRY_DELAY_SECONDS)

        if self.is_stopped.is_set()==True or file_handle is None:
            return "Access error."

        result=self.file_upload_from_handle(input_chat_id,file_handle)
        try:
            if file_handle is not None:
                file_handle.close()
        except:
            pass
        return result

    def Get_File_Info(self,input_id):
        if self.is_stopped.is_set()==True:
            return None

        response=self.perform_web_request("GET",self.base_web_url+"getFile",{"file_id":input_id})
        if response["ok"]==True:
            return response["result"]

        raise Exception("Response error.")

    def Get_File(self,input_id,input_path):
        global TELEGRAM_API_DOWNLOAD_CHUNK_BYTES

        if self.is_stopped.is_set()==True:
            return "Bot is stopped."

        if "/" not in input_id and "\\" not in input_id:
            try:
                input_id=self.Get_File_Info(input_id)[u"file_path"]
            except:
                return "Request error."

        file_contents=self.file_download_get_stream(input_id)

        if file_contents is not None:
            file_handle=None
            try:
                file_handle=open(input_path,"wb")
                for chunk in file_contents.stream(TELEGRAM_API_DOWNLOAD_CHUNK_BYTES):
                    if self.is_stopped.is_set()==True:
                        raise Exception("Bot is stopped.")
                    file_handle.write(chunk)
                file_handle.close()
                return ""
            except:
                if file_handle is not None:
                    try:
                        file_handle.close()
                    except:
                        pass
                try:
                    os.remove(input_path)
                except:
                    pass
                return "Download error."
        else:
            return "Response error."

    def ATTACH_MESSAGE_RATE_LIMITER(self,input_ratelimiter):
        self.active_rate_limiter=input_ratelimiter
        return

    def DEACTIVATE(self):
        self.is_stopped.set()
        try:
            self.request_pool.clear()
            self.request_pool.pools=None
        except:
            pass
        self.request_pool=None
        return


class Bot_Listener(object):
    def __init__(self,input_token,input_allowed_TLS_algorithms,username_list,input_timeprovider,input_signaller,input_logger=None):
        self.active_logger=input_logger
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.is_ready=threading.Event()
        self.is_ready.clear()
        self.last_ID_checked=-1
        self.start_time=0
        self.active_time_provider=input_timeprovider
        self.active_UI_signaller=input_signaller
        self.working_thread=threading.Thread(target=self.work_loop)
        self.working_thread.daemon=True
        self.listen_users=username_list
        self.name=u""
        self.messagelist_lock={}
        for username in self.listen_users:
            self.messagelist_lock[username]=threading.Lock()
        self.user_messages={}
        for username in self.listen_users:
            self.user_messages[username]=[]
        self.bot_handle=Telegram_Bot(input_token,input_allowed_TLS_algorithms)
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("BOTLSTNR",input_text)
        return

    def START(self):
        self.working_thread.start()

    def REQUEST_STOP(self):
        self.bot_handle.DEACTIVATE()
        self.request_exit.set()
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def CONCLUDE(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        self.working_thread.join()
        return

    def IS_READY(self):
        return self.is_ready.is_set()==True

    def work_loop(self):
        bot_bind_ok=False
        activation_fail_announce=False
        last_check_status=False
        while bot_bind_ok==False and self.request_exit.is_set()==False:
            try:
                self.name=self.bot_handle.Get_Bot_Info()[u"username"]
                bot_bind_ok=True
            except Exception as ex:
                if str(ex)=="Invalid token.":
                    self.log(u"ERROR: The provided bot token is invalid. Startup cannot proceed.")
                    self.REQUEST_STOP()
                else:
                    if activation_fail_announce==False:
                        self.log(u"Bot Listener activation error. Will keep trying...")
                        activation_fail_announce=True
                    time.sleep(BOT_LISTENER_THREAD_HEARTBEAT_SECONDS)

        if self.request_exit.is_set()==False:
            self.catch_up_IDs()
            self.log(u"Bot Listener for \""+self.name+u"\" is now active.")
            self.active_UI_signaller.SEND_EVENT("set_bot_name",self.name)
            self.is_ready.set()

        while self.request_exit.is_set()==False:
            time.sleep(BOT_LISTENER_THREAD_HEARTBEAT_SECONDS)
            response=[]

            try:
                response=self.bot_handle.Get_Messages(self.last_ID_checked+1)
                check_status=True
            except:
                check_status=False

            if check_status!=last_check_status:
                last_check_status=check_status
                if check_status==True:
                    self.log(u"Message retrieval is now online.")
                    self.active_UI_signaller.SEND_EVENT("set_status",u"ONLINE")
                else:
                    self.log(u"Stopped being able to retrieve messages.")
                    self.active_UI_signaller.SEND_EVENT("set_status",u"OFFLINE")

            self.group_messages(response)

        self.is_ready.clear()
        self.log(u"Bot Listener has exited.")
        self.has_quit.set()
        return

    def catch_up_IDs(self):
        global BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS

        retrieved=False
        responses=[]
        announced_fail=False
        while retrieved==False and self.request_exit.is_set()==False:
            try:
                responses=self.bot_handle.Get_Messages(self.last_ID_checked+1)
                retrieved=True
                self.log(u"Caught up with messages.")
            except:
                if announced_fail==False:
                    self.log(u"Failed to catch up with messages. Will keep trying...")
                    announced_fail=True
                time.sleep(BOT_LISTENER_THREAD_HEARTBEAT_SECONDS)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=self.active_time_provider.CURRENT_SERVER_TIME()
        return

    def group_messages(self,input_msglist):
        global BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS

        collect_new_messages={}
        for username in self.listen_users:
            collect_new_messages[username]=[]

        newest_ID=self.last_ID_checked
        for i in reversed(range(len(input_msglist))):
            if self.request_exit.is_set()==True:
                break
            this_msg_ID=input_msglist[i][u"update_id"]
            if this_msg_ID>self.last_ID_checked:
                if newest_ID<this_msg_ID:
                    newest_ID=this_msg_ID
                try:
                    msg_send_time=input_msglist[i][u"message"][u"date"]
                except:
                    msg_send_time=0
                if msg_send_time>=self.start_time:
                    if self.active_time_provider.CURRENT_SERVER_TIME()-msg_send_time<=BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
                        if u"username" in input_msglist[i][u"message"][u"from"]:
                            msg_user=input_msglist[i][u"message"][u"from"][u"username"]
                        else:
                            msg_user="#"
                            if u"first_name" in input_msglist[i][u"message"][u"from"]:
                                msg_user+=input_msglist[i][u"message"][u"from"][u"first_name"]
                            msg_user+="#"
                            if u"last_name" in input_msglist[i][u"message"][u"from"]:
                                msg_user+=input_msglist[i][u"message"][u"from"][u"last_name"]
                        if msg_user in self.listen_users:
                            if input_msglist[i][u"message"][u"chat"][u"type"]=="private":
                                collect_new_messages[msg_user].insert(0,input_msglist[i][u"message"])
            else:
                break
        self.last_ID_checked=newest_ID

        for message in collect_new_messages:
            if self.request_exit.is_set()==True:
                break
            self.messagelist_lock[message].acquire()
            if len(collect_new_messages[message])>0:
                self.user_messages[message]+=collect_new_messages[message]
            for i in reversed(range(len(self.user_messages[message]))):
                if self.active_time_provider.CURRENT_SERVER_TIME()-self.user_messages[message][i][u"date"]>BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
                    del self.user_messages[message][i]
            self.messagelist_lock[message].release()
        return

    def GET_NEW_USER_MESSAGES(self,input_username):
        self.messagelist_lock[input_username].acquire()
        get_messages=self.user_messages[input_username][:]
        self.user_messages[input_username]=[]
        self.messagelist_lock[input_username].release()
        return get_messages


class User_Message_Handler(object):
    def __init__(self,input_path_system32,input_token,input_allowed_TLS_algorithms,input_root,input_user,input_write,input_blacklisted_paths,input_listener_service,input_timeprovider,input_7zip_task_handler,input_logger=None):
        input_path_system32=input_path_system32
        self.active_logger=input_logger
        self.active_7zip_task_handler=input_7zip_task_handler
        self.working_thread=threading.Thread(target=self.work_loop)
        self.working_thread.daemon=True
        self.listener=input_listener_service
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.lock_last_folder=threading.Lock()
        self.last_folder=u""
        self.allow_writing=input_write
        self.listen_flag=threading.Event()
        self.listen_flag.clear()
        self.last_send_time=0
        self.account_username=input_user
        self.lastsent_timers=[]
        self.blacklisted_paths=[]
        self.bot_lock_pass=u""
        self.allowed_root=input_root
        self.pending_lockclear=threading.Event()
        self.pending_lockclear.clear()
        self.lock_status=threading.Event()
        self.lock_status.clear()
        self.active_time_provider=input_timeprovider
        self.processing_messages=threading.Event()
        self.processing_messages.clear()
        self.bot_handle=Telegram_Bot(input_token,input_allowed_TLS_algorithms)

        if self.allowed_root==u"*":
            self.set_last_folder(input_path_system32[0].upper()+u":\\")
        else:
            self.set_last_folder(self.allowed_root)
            self.blacklisted_paths=input_blacklisted_paths

        for i in range(len(self.blacklisted_paths)):
            self.blacklisted_paths[i]=self.blacklisted_paths[i].lower()

        self.supported_commands={u"cd":{"write_only":False,"call":self.performcommand_cd},
                                 u"dir":{"write_only":False,"call":self.performcommand_dir},
                                 u"get":{"write_only":False,"call":self.performcommand_get},
                                 u"help":{"write_only":False,"call":self.performcommand_help},
                                 u"lock":{"write_only":False,"call":self.performcommand_lock},
                                 u"root":{"write_only":False,"call":self.performcommand_root},
                                 u"start":{"write_only":False,"call":self.performcommand_start},
                                 u"stop":{"write_only":False,"call":self.performcommand_stop},
                                 u"unlock":{"write_only":False,"call":self.performcommand_unlock},
                                 u"up":{"write_only":False,"call":self.performcommand_up},
                                 u"del":{"write_only":True,"call":self.performcommand_del},
                                 u"eat":{"write_only":True,"call":self.performcommand_eat},
                                 u"listzips":{"write_only":True,"call":self.performcommand_listzips},
                                 u"mkdir":{"write_only":True,"call":self.performcommand_mkdir},
                                 u"ren":{"write_only":True,"call":self.performcommand_ren},
                                 u"rmdir":{"write_only":True,"call":self.performcommand_rmdir},
                                 u"stopzips":{"write_only":True,"call":self.performcommand_stopzips},
                                 u"zip":{"write_only":True,"call":self.performcommand_zip}}
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("MSGHNDLR",u"<"+self.account_username+u"> "+input_text)
        return

    def sendmsg(self,sender_id,message_text):
        global USER_MESSAGE_HANDLER_SENDMSG_WAIT_POLLING_SECONDS

        if self.request_exit.is_set()==True:
            return True

        for i in reversed(range(len(self.lastsent_timers))):
            if OS_Uptime_Seconds()-self.lastsent_timers[i]>=60:
                del self.lastsent_timers[i]
        second_delay=OS_Uptime_Seconds()-self.last_send_time
        if second_delay<1:
            second_delay=1-second_delay
        else:
            second_delay=0
        if len(self.lastsent_timers)>0:
            extra_sleep=(len(self.lastsent_timers)**1.82)/60
        else:
            extra_sleep=0
        throttle_time=(second_delay+max(extra_sleep-second_delay,0))*1000
        start_time=GetTickCount64()
        while GetTickCount64()-start_time<throttle_time and self.request_exit.is_set()==False:
            time.sleep(USER_MESSAGE_HANDLER_SENDMSG_WAIT_POLLING_SECONDS)
        if self.request_exit.is_set()==True:
            return True
        self.last_send_time=OS_Uptime_Seconds()

        try:
            self.bot_handle.Send_Message(sender_id,message_text)
            self.lastsent_timers+=[self.last_send_time]
            excess_entries=max(0,len(self.lastsent_timers)-40)
            for _ in range(excess_entries):
                del self.lastsent_timers[0]
            return True
        except:
            self.log(u"User Message Handler was unable to respond.")
            return False

    def allowed_path(self,input_path):
        test_path=input_path.lower().strip()
        if u"\\.\\" in test_path or u"\\..\\" in test_path:
            return False
        if self.allowed_root!=u"*":
            if test_path.startswith(self.allowed_root.lower())==False:
                return False
            for check_path in self.blacklisted_paths:
                if test_path.startswith(check_path):
                    return False
        return True

    def usable_dir(self,newpath):
        if self.allowed_path(newpath)==True:
            if os.path.isdir(newpath)==True:
                if os.access(newpath,os.R_OK)==True:
                    return True
        return False

    def proper_caps_path(self,input_path):
        try:
            retval=os.path._getfinalpathname(input_path).lstrip("\\?")
        except:
            return input_path
        if len(retval)>2 and len(input_path)>1 and input_path[1]==":" and retval.lower().startswith("unc\\")==True:
            retval=retval[-len(input_path):]
            retval=input_path[0].upper()+":"+retval[2:]
        return retval

    def usable_path(self,newpath):
        if self.allowed_path(newpath)==True:
            if os.path.exists(newpath)==True:
                try:
                    newpath=self.proper_caps_path(newpath)
                    return True
                except:
                    return False
        return False

    def relative_to_absolute_path(self,raw_command_args,isfile=False):
        command_args=raw_command_args.replace(u"/",u"\\")
        if u":" in command_args:
            newpath=command_args
        else:
            try:
                newpath=os.path.join(self.last_folder,command_args)
            except:
                return u"<BAD PATH>"
        if newpath.endswith(u"\\")==False and isfile==False:
            newpath=terminate_with_backslash(newpath)
        return sanitize_path(newpath)

    def check_pending_tasks(self):
        if self.pending_lockclear.is_set()==True:
            self.pending_lockclear.clear()
            if self.bot_lock_pass!=u"":
                self.bot_lock_pass=u""
                self.log(u"User Message Handler unlocked by console.")
            else:
                self.log(u"User Message Handler unlock was requested, but it is not locked.")
            self.listener.GET_NEW_USER_MESSAGES(self.account_username)
        return

    def work_loop(self):
        global BOT_LISTENER_THREAD_HEARTBEAT_SECONDS
        global USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS

        self.log(u"User Message Handler started, home path is \""+self.allowed_root+u"\", allow writing: "+str(self.allow_writing).upper()+u".")

        while self.request_exit.is_set()==False:
            time.sleep(USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS)
            self.check_pending_tasks()
            if self.listen_flag.is_set()==True:
                new_messages=self.listener.GET_NEW_USER_MESSAGES(self.account_username)
                total_new_messages=len(new_messages)
                if total_new_messages>0:
                    self.processing_messages.set()
                    self.log(str(total_new_messages)+u" new message(s) received.")
                    self.process_messages(new_messages)
                    self.processing_messages.clear()

        self.log(u"User Message Handler has exited.")
        self.has_quit.set()
        return

    def get_last_folder(self):
        self.lock_last_folder.acquire()
        retval=self.last_folder
        self.lock_last_folder.release()
        return retval

    def set_last_folder(self,input_folder):
        self.lock_last_folder.acquire()
        self.last_folder=input_folder
        self.lock_last_folder.release()
        return

    def START(self):
        self.working_thread.start()
        return

    def LISTEN(self,new_state):
        if new_state==True:
            if self.listen_flag.is_set()==False:
                self.log(u"Listen started.")
                self.listener.GET_NEW_USER_MESSAGES(self.account_username)
                self.listen_flag.set()
            else:
                self.log(u"Listen start was requested, but it is already listening.")
        else:
            if self.listen_flag.is_set()==True:
                self.log(u"Listen stopped.")
                self.listen_flag.clear()
            else:
                self.log(u"Listen stop was requested, but it is not currently listening.")
        return

    def ATTACH_MESSAGE_RATE_LIMITER(self,input_ratelimiter):
        self.bot_handle.ATTACH_MESSAGE_RATE_LIMITER(input_ratelimiter)
        return

    def UNLOCK(self):
        self.pending_lockclear.set()
        return

    def REQUEST_STOP(self):
        self.listen_flag.clear()
        self.bot_handle.DEACTIVATE()
        self.request_exit.set()
        return

    def CONCLUDE(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        self.working_thread.join()
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def process_messages(self,input_msglist):
        global BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS
        global TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES

        for m in input_msglist:
            if self.request_exit.is_set()==True:
                break
            if self.active_time_provider.CURRENT_SERVER_TIME()-m[u"date"]<=BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
                if u"from" in m and u"id" in m["from"]:
                    sender_id=m[u"from"][u"id"]
                    if u"text" in m:
                        self.process_bot_command(sender_id,m[u"chat"][u"id"],m[u"text"])
                    else:
                        if u"document" in m:
                            self.process_bot_file(sender_id,m[u"document"][u"file_id"],m[u"document"][u"file_name"],m[u"document"][u"file_size"])
                        elif u"audio" in m:
                            newname=u""
                            fileext=u""

                            try:
                                file_name=self.bot_handle.Get_File_Info(m[u"audio"][u"file_id"])[u"file_path"]
                                file_name=file_name[file_name.rfind(u"/")+1:]
                                fileext=file_name[file_name.rfind(u".")+1:]
                                filetitle=u""
                                fileperformer=u""
                                if u"title" in m[u"audio"]:
                                    filetitle=m[u"audio"][u"title"]
                                if u"performer" in m[u"audio"]:
                                    fileperformer=m[u"audio"][u"performer"]
                                if len(filetitle)>32:
                                    filetitle=filetitle[:32]
                                if len(fileperformer)>32:
                                    fileperformer=fileperformer[:32]
                                filetitle=filetitle.replace(u"/",u"").replace(u"\\",u"").replace(u"?",u"").replace(u"*",u"").replace(u":",u"").replace(u"|",u"").replace(u"<",u"").replace(u">",u"")
                                fileperformer=fileperformer.replace(u"/",u"").replace(u"\\",u"").replace(u"?",u"").replace(u"*",u"").replace(u":",u"").replace(u"|",u"").replace(u"<",u"").replace(u">",u"")
                                if filetitle!=u"" or fileperformer!=u"":
                                    if fileperformer!=u"" and filetitle==u"":
                                        newname=fileperformer
                                    if fileperformer!=u"" and filetitle!=u"":
                                        newname=fileperformer+u" - "+filetitle
                                    if fileperformer==u"" and filetitle!=u"":
                                        newname=filetitle
                            except:
                                pass

                            if fileext==u"":
                                fileext=u"unknown"
                            if newname!=u"":
                                newname+=u"-"
                            newname+=str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))+u"."+fileext
                            file_name=newname
                            self.process_bot_file(sender_id,m[u"audio"][u"file_id"],file_name,m[u"audio"][u"file_size"])
                        else:
                            self.sendmsg(sender_id,u"Media type unsupported. Send as regular file or the file name will not carry over.")
        return

    def process_bot_file(self,sender_id,file_id,filename,filesize):
        global TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES

        if self.bot_lock_pass!=u"" or self.allow_writing==False or self.request_exit.is_set()==True:
            return

        if filesize<=TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES:
            foldername=self.get_last_folder()
            complete_put_path=foldername+filename
            self.sendmsg(sender_id,u"Putting file \""+filename+u"\" at \""+foldername+u"\"...")
            self.log(u"Receiving file \""+complete_put_path+u"\"...")
            if os.path.exists(complete_put_path)==False:
                result=self.bot_handle.Get_File(file_id,complete_put_path)
                if result=="":
                    self.sendmsg(sender_id,u"Finished putting file \""+complete_put_path+u"\".")
                    self.log(u"File download complete.")
                elif result=="Bot is stopped.":
                    return
                else:
                    self.sendmsg(sender_id,u"File \""+filename+u"\" could not be placed.")
                    self.log(u"File download aborted due to unknown issue.")
            else:
                if os.path.isfile(complete_put_path)==True:
                    self.sendmsg(sender_id,u"File \""+filename+u"\" already exists at the location.")
                    self.log(u"File download aborted due to existing instance.")
                else:
                    self.sendmsg(sender_id,u"A folder with the name \""+filename+u"\" already exists at the location.")
                    self.log(u"File download aborted due to conflict with existing folder.")
        else:
            self.sendmsg(sender_id,u"File \""+filename+u"\" could not be obtained because bots are limited to file downloads of max. "+readable_size(TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES)+u".")
            self.log(u"File download aborted due to size exceeding limit.")
        return

    def segment_file_list_string(self,input_string):
        global TELEGRAM_API_MAX_IM_SIZE_BYTES

        retval=[]
        input_list=input_string.split(u"\n")
        current_message=u""

        for file_listing in input_list:
            new_entry=file_listing.strip()+u"\n"
            if len(new_entry)+len(current_message)<=TELEGRAM_API_MAX_IM_SIZE_BYTES+1:
                current_message+=new_entry
            else:
                current_message=current_message[:-1]
                retval+=[current_message]
                current_message=u""

        if current_message!=u"":
            retval+=[current_message[:-1]]

        if len(retval)==1:
            if retval[0]==u"":
                retval=[]

        return retval

    def folder_list_string(self,input_folder,search_in,folders_only):
        search=search_in.lower()
        foldername=input_folder.lower().strip()
        if foldername==u"":
            return u"<No path.>"

        response=u""
        filelist=[]
        folderlist=[]

        foldername=terminate_with_backslash(foldername)

        try:
            for name in os.listdir(foldername):
                path=os.path.join(foldername,name)
    
                if os.path.isfile(path):
                    if folders_only==False:
                        if name.lower().find(search)!=-1 or search==u"":
                            filelist+=[name+u" [Size: "+readable_size(os.path.getsize(path))+u"]"]
                else:
                    if name.lower().find(search)!=-1 or search==u"":
                        folderlist+=[name]

            if len(folderlist)>0:
                response+=u"<FOLDERS:>\n"

            for folder in folderlist:
                response+=u"\n"+folder

            if len(folderlist)>0:
                response+=u"\n\n"

            if len(filelist)>0:
                response+=u"<FILES:>\n"

            for filename in filelist:
                response+=u"\n"+filename
        except:
            response=u"<BAD_PATH>"

        return response

    def performcommand_start(self,command_context):
        self.log(u"User has sent a start request.")

        return u""

    def performcommand_stop(self,command_context):
        self.log(u"User has sent a stop request.")

        return u""

    def performcommand_root(self,command_context):
        response=u""

        if self.allowed_root!=u"*":
            response=u"Root folder path is \""+self.allowed_root+u"\"."
        else:
            response=u"This user is allowed to access all host system drives."
        self.log(u"Root folder path requested, which is \""+self.allowed_root+u"\".")

        return response

    def performcommand_dir(self,command_context):
        response=u""

        extra_search=u""

        if u"?f:" in command_context["args"].lower():
            start=command_context["args"].lower().find(u"?f:")
            end=command_context["args"][start:].find(u" ")
            if end==-1:
                end=len(command_context["args"])
            else:
                end+=start
            extra_search=command_context["args"][start+len(u"?f:"):end]
            if command_context["args"][:start].strip()!=u"":
                command_context["args"]=command_context["args"][:start].strip()
            else:
                command_context["args"]=command_context["args"][end:].strip()

        if u"?d" in command_context["args"].lower():
            folders_only=True
            start=command_context["args"].lower().find(u"?d")
            end=start+len(u"?d")
            if command_context["args"][:start].strip()!=u"":
                command_context["args"]=command_context["args"][:start].strip()
            else:
                command_context["args"]=command_context["args"][end:].strip()
        else:
            folders_only=False

        self.log(u"Listing requested for path \""+command_context["args"]+u"\" with search string \""+extra_search+u"\", folders only="+str(folders_only).upper()+u"...")

        if command_context["args"]==u"":
            use_folder=self.get_last_folder()
        else:
            use_folder=command_context["args"]
        use_folder=self.relative_to_absolute_path(use_folder)
        if self.allowed_path(use_folder)==True:
            dirlist=self.folder_list_string(use_folder,extra_search,folders_only)
        else:
            dirlist=u""
            response=u"<Path is inaccessible.>"
            self.log(u"Folder path \""+command_context["args"]+u"\" was inaccessible for listing.")

        if dirlist!=u"<BAD_PATH>":
            segment_list=self.segment_file_list_string(dirlist)
            if len(segment_list)>0:
                for segment in segment_list:
                    if self.sendmsg(command_context["sender_id"],segment)==False:
                        response=u"<Listing interrupted.>"
                        self.log(u"Listing for folder path \""+command_context["args"]+u"\" was interrupted.")
                        break
                    if self.request_exit.is_set()==True:
                        break
            else:
                response=u"<Folder is empty.>"
                self.log(u"Folder path \""+command_context["args"]+u"\" was empty.")
            if response==u"":
                response=u"<Listing finished.>"
                self.log(u"Folder path \""+command_context["args"]+u"\" listing completed.")
        else:
            response=u"<Path is inaccessible.>"
            self.log(u"Folder path \""+command_context["args"]+u"\" was inaccessible for listing.")

        return response

    def performcommand_cd(self,command_context):
        response=u""

        if command_context["args"]!=u"":
            newpath=self.relative_to_absolute_path(command_context["args"])
            if self.usable_dir(newpath)==True:
                newpath=self.proper_caps_path(newpath)
                newpath=terminate_with_backslash(newpath)
                self.set_last_folder(newpath)
                response=u"Current folder changed to \""+newpath+u"\"."
                self.log(u"Current folder was changed to \""+newpath+u"\".")
            else:
                response=u"Path could not be accessed."
                self.log(u"Path provided \""+newpath+u"\" could not be accessed.")
        else:
            newpath=self.get_last_folder()
            response=u"Current folder is \""+newpath+u"\"."
            self.log(u"Queried current folder, which is \""+newpath+u"\".")

        return response

    def performcommand_get(self,command_context):
        global TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES

        response=u""

        if command_context["args"]!=u"":
            newpath=self.relative_to_absolute_path(command_context["args"],True)
            if self.usable_path(newpath)==True:
                newpath=self.proper_caps_path(newpath)
                self.log(u"Requested get file \""+newpath+u"\". Sending...")
                self.sendmsg(command_context["sender_id"],u"Getting file, please wait...")
                result=self.bot_handle.Send_File(command_context["chat_id"],newpath)
                if result=="":
                    self.log(u"File \""+newpath+u"\" sent.")
                elif result=="Bot is stopped.":
                    return u""
                elif result=="File too big.":
                    response=u"Bots cannot upload files larger than "+str(readable_size(TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES))+u" to the chat."
                    self.log(u"Requested file \""+newpath+u"\" too large to get.")
                elif result=="Empty file.":
                    response=u"File is empty."
                    self.log(u"Get file \""+newpath+u"\" failed because the file is empty.")
                elif result=="Upload error.":
                    response=u"Problem getting file."
                    self.log(u"Get File upload error for \""+newpath+u"\".")
                elif result=="Access error.":
                    response=u"Problem reading the file."
                    self.log(u"Get File access error for \""+newpath+u"\".")
            else:
                response=u"File not found or inaccessible."
                self.log(u"Get file \""+newpath+u"\" was not found.")
        else:
            response=u"A file name or path must be provided."
            self.log(u"Attempted to use get without a file name or path.")

        return response

    def performcommand_ren(self,command_context):
        response=u""

        newname=u""
        if u"?to:" in command_context["args"].lower():
            end=command_context["args"].lower().find(u"?to:")
            newname=command_context["args"][end+len(u"?to:"):].strip()
            command_args=command_context["args"][:end].strip()

        if command_context["args"]!=u"" and newname!=u"":
            newname_ok=True
            for c in newname:
                if c in u"|<>\":\\/*?":
                    newname_ok=False
                    break
            if newname_ok==True:
                newpath=self.relative_to_absolute_path(command_args,True)
                if self.usable_path(newpath)==True:
                    newpath=self.proper_caps_path(newpath)
                    end=newpath.rfind(u"\\")
                    if end!=-1:
                        foldername=terminate_with_backslash(newpath[:end])
                        self.log(u"Requested rename \""+newpath+u"\" to \""+newname+u"\".")
                        newtarget=foldername+newname
                        if os.path.exists(newtarget)==False:
                            try:
                                os.rename(newpath,newtarget)
                                response=u"Renamed \""+newpath+u"\" to \""+newname+u"\"."
                                self.log(u"Renamed \""+newpath+u"\" to \""+newname+u"\".")
                            except:
                                response=u"Problem renaming."
                                self.log(u"File/folder \""+newpath+u"\" rename error.")
                        else:
                            response=u"A file or folder with the new name already exists."
                            self.log(u"File/folder rename of \""+newpath+u"\" failed because the new target \""+newtarget+u"\" already exists.")
                    else:
                        response=u"Problem with path."
                        self.log(u"File/folder rename \""+newpath+u"\" path error.")
                else:
                    response=u"File/folder not found or inaccessible."
                    self.log(u"File/folder to rename \""+newpath+u"\" not found.")
            else:
                response=u"The new name must not be a path or contain invalid characters."
                self.log(u"Attempted to rename \""+command_args+u"\" to a new name containing invalid characters.")
        else:
            response=u"A name or path and a new name preceded by \"?to:\" must be provided."
            self.log(u"Attempted to rename without specifying a name or path.")

        return response

    def performcommand_eat(self,command_context):
        global TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES

        response=u""

        if command_context["args"].endswith(u" ?confirm")==True:
            command_context["args"]=command_context["args"][:-len(u" ?confirm")].strip()
            if command_context["args"]!=u"":
                newpath=self.relative_to_absolute_path(command_context["args"],True)
                if self.usable_path(newpath)==True:
                    newpath=self.proper_caps_path(newpath)
                    self.log(u"Requested eat file \""+newpath+u"\". Sending...")
                    self.sendmsg(command_context["sender_id"],u"Eating file, please wait...")
                    result=self.bot_handle.Send_File(command_context["chat_id"],newpath)
                    if result=="":
                        self.log(u"File \""+newpath+u"\" sent. Deleting...")
                        try:
                            os.remove(newpath)
                            response=u"File deleted."
                            self.log(u"File \""+newpath+u"\" deleted.")
                        except:
                            response=u"Problem deleting file."
                            self.log(u"File delete error for \""+newpath+u"\".")
                    elif result=="Bot is stopped.":
                        return u""
                    elif result=="File too big.":
                        response=u"Bots cannot upload files larger than "+str(readable_size(TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES))+u" to the chat."
                        self.log(u"Requested file \""+newpath+u"\" too large to get.")
                    elif result=="Empty file.":
                        response=u"File is empty."
                        self.log(u"Get file \""+newpath+u"\" failed because the file is empty.")
                    elif result=="Upload error.":
                        response=u"Problem getting file."
                        self.log(u"Get File upload error for \""+newpath+u"\".")
                    elif result=="Access error.":
                        response=u"Problem reading the file."
                        self.log(u"Get File access error for \""+newpath+u"\".")
                else:
                    response=u"File not found or inaccessible."
                    self.log(u"File to eat at \""+newpath+u"\" not found.")
            else:
                response=u"A file name or path must be provided."
                self.log(u"Attempted to eat file without specifying a name or path.")
        else:
            response=u"This command must end in \" ?confirm\"."
            self.log(u"Attempted to delete file without confirmation.")

        return response

    def performcommand_del(self,command_context):
        response=u""

        if command_context["args"].endswith(u" ?confirm")==True:
            command_context["args"]=command_context["args"][:-len(u" ?confirm")].strip()
            if command_context["args"]!=u"":
                newpath=self.relative_to_absolute_path(command_context["args"],True)
                if self.usable_path(newpath)==True:
                    newpath=self.proper_caps_path(newpath)
                    self.log(u"Requested delete file \""+newpath+u"\".")
                    try:
                        self.sendmsg(command_context["sender_id"],"Deleting file...")
                        os.remove(newpath)
                        response=u"File deleted."
                        self.log(u"File \""+newpath+u"\" deleted.")
                    except:
                        if os.path.isdir(newpath)==True:
                            response=u"Item at location is a folder, not a file."
                            self.log(u"File delete requested at \""+newpath+u"\" but item is a directory.")
                        else:
                            response=u"Problem deleting file."
                            self.log(u"File \""+newpath+u"\" delete error.")
                else:
                    response=u"File not found or inaccessible."
                    self.log(u"File to delete \""+newpath+u"\" not found.")
            else:
                response=u"A file name or path must be provided."
                self.log(u"Attempted to delete file without specifying a name or path.")
        else:
            response=u"This command must end in \" ?confirm\"."
            self.log(u"Attempted to delete file without confirmation.")

        return response

    def performcommand_mkdir(self,command_context):
        response=u""

        if command_context["args"]!=u"":
            newpath=self.relative_to_absolute_path(command_context["args"],True)
            upper_folder=newpath
            if upper_folder.endswith(u"\\")==True:
                upper_folder=upper_folder[:-1]
            if upper_folder.count(u"\\")>0:
                upper_folder=upper_folder[:upper_folder.rfind(u"\\")+1]
            if self.usable_dir(upper_folder)==True:
                if os.path.isdir(newpath)==False:
                    try:
                        os.mkdir(newpath)
                        response=u"Folder created."
                        self.log(u"Folder created at \""+newpath+u"\".")
                    except:
                        response=u"Problem creating folder."
                        self.log(u"Folder create error at \""+newpath+u"\".")
                else:
                    response=u"Folder already exists."
                    self.log(u"Attempted to create already existing folder at \""+newpath+u"\".")
            else:
                response=u"Path is not usable."
                self.log(u"Attempted to create folder at unusable path \""+newpath+u"\".")
        else:
            response=u"A folder name or path must be provided."
            self.log(u"Attempted to create folder without specifying a name or path.")

        return response

    def performcommand_rmdir(self,command_context):
        response=u""

        if command_context["args"].endswith(u" ?confirm")==True:
            command_context["args"]=command_context["args"][:-len(u" ?confirm")].strip()
            if command_context["args"]!=u"":
                newpath=self.relative_to_absolute_path(command_context["args"],True)
                if self.usable_dir(newpath)==True:
                    upper_folder=newpath
                    if upper_folder.endswith(u"\\")==True:
                        upper_folder=upper_folder[:-1]
                    if upper_folder.count(u"\\")>0:
                        upper_folder=upper_folder[:upper_folder.rfind(u"\\")+1]
                    if self.usable_dir(upper_folder)==True:
                        newpath=self.proper_caps_path(newpath)
                        self.log(u"Requested delete folder \""+newpath+u"\"...")
                        try:
                            self.sendmsg(command_context["sender_id"],u"Deleting folder...")
                            shutil.rmtree(newpath)
                            moved_up=u""
                            newpath=terminate_with_backslash(newpath)
                            if self.get_last_folder().lower().endswith(newpath.lower())==True:
                                self.set_last_folder(upper_folder)
                                moved_up=u" Current folder is now \""+self.proper_caps_path(upper_folder)+u"\"."
                            response=u"Folder deleted."+moved_up
                            self.log(u"Folder deleted at \""+newpath+u"\"."+moved_up)
                        except:
                            response=u"Problem deleting folder."
                            self.log(u"Folder delete error at \""+newpath+u"\".")
                    else:
                        response=u"No upper folder to switch to after removal."
                        self.log(u"Attempted to delete \""+newpath+u"\" at top folder.")
                else:
                    response=u"Folder \""+newpath+u"\" not found or inaccessible."
                    self.log(u"Folder to delete not found at \""+newpath+u"\".")
            else:
                response=u"A folder name or path must be provided."
                self.log(u"No folder name or path provided for deletion.")
        else:
            response=u"This command must end in \" ?confirm\"."
            self.log(u"Attempted to delete folder without confirmation.")

        return response

    def performcommand_up(self,command_context):
        response=u""

        if self.last_folder.count(u"\\")>1:
            newpath=self.get_last_folder()
            newpath=newpath[:-1]
            newpath=newpath[:newpath.rfind(u"\\")+1]
            if self.allowed_path(newpath)==True:
                self.set_last_folder(newpath)
                response=u"Current folder is now \""+newpath+u"\"."
                self.log(u"Current folder changed to \""+newpath+u"\".")
            else:
                response=u"Already at top folder."
                self.log(u"Attempted to go up while at top folder.")
        else:
            response=u"Already at top folder."
            self.log(u"Attempted to go up while at top folder.")

        return response

    def performcommand_zip(self,command_context):
        response=u""

        if command_context["args"]!=u"":
            newpath=self.relative_to_absolute_path(command_context["args"])
            if os.path.isfile(newpath)==True or (os.path.exists(newpath)==False and newpath.endswith(u"\\")==True):
                newpath=newpath[:-1]
            if self.usable_path(newpath)==True:
                zip_response=self.active_7zip_task_handler.NEW_TASK(newpath,self.account_username)
                if zip_response["result"]=="CREATED":
                    response=u"Issued zip command."
                    self.log(u"Zip command launched on \""+zip_response["full_target"]+u"\".")
                elif zip_response["result"]=="EXISTS":
                    response=u"An archive \""+zip_response["full_target"]+u".7z\" already exists."
                    self.log(u"Zip \""+command_context["args"]+u"\" failed because target archive \""+zip_response["full_target"]+u".7z\" already exists.")
                elif zip_response["result"]=="ERROR":
                    response=u"Problem running command."
                    self.log(u"Zip \""+command_context["args"]+u"\" command could not be run.")
                elif zip_response["result"]=="MAXREACHED":
                    response=u"Maximum concurrent archival tasks reached."
                    self.log(u"Zip \""+command_context["args"]+u"\" rejected due to max concurrent tasks per user limit.")
            else:
                response=u"File not found or inaccessible."
                self.log(u"Zip \""+command_context["args"]+u"\" file not found or inaccessible.")
        else:
            response=u"A file or folder name or path must be provided."
            self.log(u"Attempted to zip without a name or path.")

        return response

    def performcommand_listzips(self,command_context):
        response=u""

        tasks_7zip=self.active_7zip_task_handler.GET_TASKS()

        for taskdata in tasks_7zip:
            if taskdata["user"]==self.account_username:
                response+=u">ARCHIVING \""+self.proper_caps_path(taskdata["target"])+u"\"\n"

        if response==u"":
            response=u"No archival tasks running."
        else:
            response=u"Ongoing archival tasks:\n\n"+response

        self.log(u"Requested list of running 7-ZIP archival tasks for user.")

        return response

    def performcommand_stopzips(self,command_context):
        response=u"All running archival tasks will be stopped."
        self.active_7zip_task_handler.END_TASKS([self.account_username])
        self.log(u"Requested stop of any running 7-ZIP archival tasks.")

        return response

    def performcommand_lock(self,command_context):
        global BOT_LOCK_PASSWORD_CHARACTERS_MIN
        global BOT_LOCK_PASSWORD_CHARACTERS_MAX

        response=u""

        cmdlen=len(command_context["args"])
        if cmdlen>=BOT_LOCK_PASSWORD_CHARACTERS_MIN and cmdlen<=BOT_LOCK_PASSWORD_CHARACTERS_MAX:
            self.bot_lock_pass=command_context["args"]
            response=u"Bot locked."
            self.lock_status.set()
            self.log(u"User Message Handler was locked with a password.")
        else:
            response=u"Lock password must be between "+str(BOT_LOCK_PASSWORD_CHARACTERS_MIN)+u" and "+str(BOT_LOCK_PASSWORD_CHARACTERS_MAX)+u" characters long."
            self.log(u"Attempted to lock the bot with a password of invalid length.")

        return response

    def performcommand_unlock(self,command_context):
        return u"The bot is already unlocked."

    def performcommand_help(self,command_context):
        global BOT_LOCK_PASSWORD_CHARACTERS_MIN
        global BOT_LOCK_PASSWORD_CHARACTERS_MAX

        response=u"AVAILABLE BOT COMMANDS:\n\n"
        response+=u"/help: display this help screen\n"
        response+=u"/root: display the root access folder\n"
        response+=u"/cd [PATH]: change path(eg: /cd c:\windows); no argument returns current path\n"
        response+=u"/dir [PATH] [?f:<filter>] [?d]: list files/folders; filter results(/dir c:\windows ?f:.exe); use ?d for listing directories only; no arguments lists current folder\n"
        if self.allow_writing==True:
            response+=u"/zip <PATH[FILE]>: make a 7-ZIP archive of a file or folder; extension will be .7z.TMP until finished; max. "+str(self.active_7zip_task_handler.GET_MAX_TASKS_PER_USER())+u" simultaneous tasks\n"
            response+=u"/listzips: list all running 7-ZIP archival tasks\n"
            response+=u"/stopzips: stop all running 7-ZIP archival tasks\n"
            response+=u"/ren [FILE | FOLDER] ?to:[NEWNAME]: rename a file or folder\n"
        response+=u"/up: move up one folder from current path\n"
        response+=u"/get <[PATH]FILE>: retrieve the file at the location to Telegram chat\n"
        if self.allow_writing==True:
            response+=u"/eat <[PATH]FILE>: upload the file at the location to Telegram, then delete it from its original location\n"
            response+=u"/del <[PATH]FILE>: delete the file at the location\n"
            response+=u"/mkdir <[PATH]FOLDER>: create the folder at the location\n"
            response+=u"/rmdir <[PATH]FOLDER>: delete the folder at the location\n"
        response+=u"/lock <PASSWORD>: lock the bot from responding to messages using a password between "+str(BOT_LOCK_PASSWORD_CHARACTERS_MIN)+u" and "+str(BOT_LOCK_PASSWORD_CHARACTERS_MAX)+u" characters long\n"
        response+=u"/unlock <PASSWORD>: unlock the bot\n"
        response+=u"\nSlashes work both ways in paths (/cd c:/windows, /cd c:\windows)\n\n"
        response+=u"File size limit for getting files from host system: "+readable_size(TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES)+u"."
        if self.allow_writing==True:
            response+=u"\nFile size limit for putting files on host system: "+readable_size(TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES)+u".\n"
            response+=u"\nNOTE: All commands that delete files or folders must end with \" ?confirm\"."
        self.log(u"Help requested.")

        return response

    def process_bot_command(self,sender_id,chat_id,message_text):
        global TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES
        global TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES

        if self.bot_lock_pass!=u"":
            if message_text.lower().startswith(u"/unlock ")==True:
                attempted_pass=message_text[len(u"/unlock "):].strip()
                attempted_pass_len=len(attempted_pass)
                if attempted_pass_len>=BOT_LOCK_PASSWORD_CHARACTERS_MIN and attempted_pass_len<=BOT_LOCK_PASSWORD_CHARACTERS_MAX:
                    if attempted_pass==self.bot_lock_pass:
                        self.bot_lock_pass=u""
                        self.lock_status.clear()
                        self.sendmsg(sender_id,u"Bot unlocked.")
                        self.log(u"User Message Handler unlocked by user.")
                        return
                    else:
                        return
                else:
                    return
            else:
                return

        if message_text.startswith(u"/")==False:
            return
        cmd_end=message_text.find(u" ")
        if cmd_end==-1:
            cmd_end=len(message_text)
        command_type=message_text[1:cmd_end].strip().lower()
        command_args=message_text[cmd_end+1:].strip()
        response=u""

        command_not_supported=False

        if command_type in self.supported_commands:
            command_info=self.supported_commands[command_type]
            if self.request_exit.is_set()==True:
                return
            if command_info["write_only"]==False or self.allow_writing==True:
                response=command_info["call"]({"args":command_args,"sender_id":sender_id,"chat_id":chat_id})
            else:
                command_not_supported=True
        else:
            command_not_supported=True

        if command_not_supported==True:
            response=u"Unrecognized command. Type \"/help\" for a list of commands."

        if response!=u"":
            self.sendmsg(sender_id,response)
        return


class User_Console(object):
    def __init__(self,input_user_handler_list,input_signaller,input_7zip_taskhandler,input_time_sync,input_logger=None):
        global TELEGRAM_API_MAX_GLOBAL_IMS
        global TELEGRAM_API_MAX_GLOBAL_TIME_INTERVAL_SECONDS

        self.active_logger=input_logger
        self.working_thread=threading.Thread(target=self.work_loop)
        self.message_rate_limiter=Telegram_Message_Rate_Limiter(TELEGRAM_API_MAX_GLOBAL_IMS,TELEGRAM_API_MAX_GLOBAL_TIME_INTERVAL_SECONDS)
        self.working_thread.daemon=True
        self.active_UI_signaller=input_signaller
        self.is_exiting=threading.Event()
        self.is_exiting.clear()
        self.user_handler_list=input_user_handler_list
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.minimized_state=threading.Event()
        self.minimized_state.set()
        self.lock_command=threading.Lock()
        self.request_time_sync=input_time_sync
        self.active_7zip_task_handler=input_7zip_taskhandler
        self.pending_command=u""
        self.supported_commands={u"help":self.performcommand_help,
                                 u"listusers":self.performcommand_listusers,
                                 u"listzips":self.performcommand_listzips,
                                 u"startlisten":self.performcommand_startlisten,
                                 u"stoplisten":self.performcommand_stoplisten,
                                 u"stopzips":self.performcommand_stopzips,
                                 u"synctime":self.performcommand_synctime,
                                 u"unlockusers":self.performcommand_unlockusers,
                                 u"userstats":self.performcommand_userstats}
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("UCONSOLE",input_text)
        return

    def START(self):
        self.working_thread.start()
        return

    def REQUEST_STOP(self):
        self.message_rate_limiter.DEACTIVATE()
        self.request_exit.set()
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def CONCLUDE(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        self.working_thread.join()
        return

    def SEND_COMMAND(self,input_command):
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            self.pending_command=input_command
            self.lock_command.release()
        return

    def NOTIFY_MINIMIZED_STATE(self,input_state):
        if input_state:
            self.minimized_state.set()
        else:
            self.minimized_state.clear()
        return

    def user_handlers_running(self):
        total=0
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.IS_RUNNING()==True:
                total+=1
        return total

    def any_user_handlers_busy(self):
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.processing_messages.is_set()==True:
                return True
        return False

    def performcommand_startlisten(self,input_arguments):
        has_acted=False
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                user_handler_instance.LISTEN(True)
                has_acted=True
        if has_acted==False:
            self.log(u"No matching users were found.")
        return True

    def performcommand_stoplisten(self,input_arguments):
        has_acted=False
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                user_handler_instance.LISTEN(False)
                has_acted=True
        if has_acted==False:
            self.log(u"No matching users were found.")
        return True

    def performcommand_userstats(self,input_arguments):
        stats_out=u""
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                stats_out+=u"\nMessage handler for user \""+user_handler_instance.account_username+u"\":\n"+\
                         u"Home path=\""+user_handler_instance.allowed_root+u"\"\n"+\
                         u"Write permissions: "+str(user_handler_instance.allow_writing).upper()+u"\n"+\
                         u"Current folder=\""+user_handler_instance.get_last_folder()+u"\"\n"+\
                         u"Locked: "+str(user_handler_instance.lock_status.is_set()).upper()+u"\n"+\
                         u"Listening: "+str(user_handler_instance.listen_flag.is_set()).upper()+u"\n"
        if stats_out!=u"":
            stats_out=u"USER STATS:\n"+stats_out
            self.log(stats_out)
        else:
            self.log(u"No matching users were found.")
        return True

    def performcommand_listusers(self,input_arguments):
        list_out=u""
        for user_handler_instance in self.user_handler_list:
            list_out+=user_handler_instance.account_username+u", "
        list_out=list_out[:-2]+u"."
        self.log(u"Allowed user(s): "+list_out)
        return True

    def performcommand_unlockusers(self,input_arguments):
        has_acted=False
        for user_handler_instance in self.user_handler_list:
            if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                user_handler_instance.UNLOCK()
                has_acted=True
        if has_acted==False:
            self.log(u"No matching users were found.")
        return True

    def performcommand_synctime(self,input_arguments):
        if self.request_time_sync.is_set()==False:
            self.log(u"Manual Internet time synchronization requested...")
            self.request_time_sync.set()
        else:
            self.log(u"Manual Internet time synchronization is already in progress.")
        return True

    def performcommand_listzips(self,input_arguments):
        tasklist=self.active_7zip_task_handler.GET_TASKS()
        user_task_dict={}
        for entry in tasklist:
            if entry["user"] not in user_task_dict.keys():
                user_task_dict[entry["user"]]=[]
            user_task_dict[entry["user"]]+=[{"target":entry["target"],"pid":entry["pid"]}]
        task_data_out=u""
        for username in user_task_dict:
            if username.lower() in input_arguments or input_arguments==[]:
                task_data_out+=u"USER \""+username+u"\":\n"
                for entry in user_task_dict[username]:
                    task_data_out+=u">TARGET: \""+entry["target"]+u"\" BATCH PID: "+str(entry["pid"])+u"\n"
                task_data_out+=u"\n"
        if task_data_out==u"":
            self.log(u"Found no 7-ZIP tasks running.")
        else:
            if task_data_out.endswith(u"\n")==True:
                task_data_out=task_data_out[:-1]
            task_data_out=u"RUNNING 7-ZIP ARCHIVAL TASK(S):\n"+task_data_out
            self.log(task_data_out)
        return True

    def performcommand_stopzips(self,input_arguments):
        usernames=[]
        pids=[]

        for arg in input_arguments:
            arg=arg.strip()
            if arg!=u"":
                new_pid=-1
                new_username=u""

                try:
                    new_pid=int(arg)
                    if new_pid<=4 or new_pid>2**32:
                        new_pid=-1
                except:
                    invalid=False
                    if len(arg)>=5 and len(arg)<=32:
                        if arg[0] in u"0123456789_":
                            invalid=True
                        else:
                            for c in arg:
                                if c.lower() not in u"0123456789_abcdefghijklmnopqrstuvwxyz#":
                                    invalid=True
                                    break
                    else:
                        invalid=True

                    if invalid==False:
                        new_username=arg

                if new_username!=u"":
                    usernames+=[new_username]
                elif new_pid!=-1:
                    pids+=[new_pid]
                else:
                    self.log(u"One or more PIDs or users were incorrect.")
                    return False

        if len(pids)+len(usernames)>0:
            self.active_7zip_task_handler.END_TASKS(usernames,pids)
        else:
            self.active_7zip_task_handler.END_TASKS([u"*"])
        return True

    def performcommand_help(self,input_arguments):
        self.log(u"AVAILABLE CONSOLE COMMANDS:\n"+\
        u"listusers: lists all allowed users\n"+\
        u"startlisten [USERS]: start listening to messages for listed users; leave blank to apply to all instances\n"+\
        u"stoplisten [USERS]: stop listening to messages for listed users; leave blank to apply to all instances\n"+\
        u"unlockusers [USERS]: unlock the bot for listed users; leave blank to apply to all instances\n"+\
        u"userstats [USERS]: list stats for listed users; leave blank to list all instances\n"+\
        u"listzips [USERS]: list running 7-ZIP archival tasks for listed users; leave blank to list all instances\n"+\
        u"stopzips [PID | USERS]: stop running 7-ZIP archival tasks by listed userss or PID; leave blank to apply to all instances\n"+\
        u"synctime: manually re-synchronize bot time with Internet time\n"+\
        u"help: display help\n"+\
        u"exit: close the program\n")
        return True

    def process_console_command(self,user_input):
        user_data=user_input.split(u" ")
        input_command=user_data[0].lower().strip()
        input_arguments=[]
        if len(user_data)>1:
            for i in range(1,len(user_data)):
                new_arg=user_data[i].lower().strip()
                if new_arg!=u"":
                    input_arguments+=[new_arg]

        if input_command in self.supported_commands:
            if self.request_exit.is_set()==True:
                return False
            return self.supported_commands[input_command](input_arguments)
        else:
            self.log(u"Unrecognized command. Type \"help\" for a list of commands.")
            return False

    def retrieve_command(self):
        retval=u""
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            retval=self.pending_command
            self.pending_command=u""
            self.lock_command.release()
        return retval

    def work_loop(self):
        global COMMAND_CHECK_INTERVAL_ACTIVE_SECONDS
        global COMMAND_CHECK_INTERVAL_MINIMIZED_SECONDS
        global UI_COMMAND_HISTORY_MAX

        self.log(u"Starting User Message Handler(s)...")
        for user_handler_instance in self.user_handler_list:
            user_handler_instance.ATTACH_MESSAGE_RATE_LIMITER(self.message_rate_limiter)
            user_handler_instance.START()
            user_handler_instance.LISTEN(True)

        self.log(u"User Console activated.\nType \"help\" in the console for available commands.\nUse the up and down arrows to scroll through previous successful commands(max. "+str(UI_COMMAND_HISTORY_MAX)+u" history).")
        self.active_UI_signaller.SEND_EVENT("attach_console",self)

        if self.user_handlers_running()==0:
            self.is_exiting.set()

        continue_processing=True
        last_busy_state=False

        while continue_processing==True:
            if self.minimized_state.is_set()==False:
                time.sleep(COMMAND_CHECK_INTERVAL_ACTIVE_SECONDS)
            else:
                time.sleep(COMMAND_CHECK_INTERVAL_MINIMIZED_SECONDS)

            if last_busy_state!=self.any_user_handlers_busy():
                last_busy_state=not last_busy_state
                self.active_UI_signaller.SEND_EVENT("report_processing_messages_state",last_busy_state)

            command=self.retrieve_command()

            if command!=u"":
                result=False

                if command.lower()==u"exit":
                    self.log(u"Exit requested. Closing...")
                    self.REQUEST_STOP()
                else:
                    result=self.process_console_command(command)

                if result==True:
                    self.active_UI_signaller.SEND_EVENT("commandfield_accepted")

            if self.request_exit.is_set()==True:
                self.is_exiting.set()

            if self.is_exiting.is_set()==False:
                if command!=u"":
                    self.active_UI_signaller.SEND_EVENT("commandfield_failed")
            else:
                continue_processing=False

                self.log(u"Requesting stop to Message Handler(s)...")
                for user_handler_instance in self.user_handler_list:
                    user_handler_instance.REQUEST_STOP()

                for user_handler_instance in self.user_handler_list:
                    user_handler_instance.CONCLUDE()
                self.log(u"Confirmed User Message Handler(s) exit.")

        self.log(u"User Console exiting...")
        self.active_UI_signaller.SEND_EVENT("detach_console")
        self.active_UI_signaller.SEND_EVENT("close")
        self.has_quit.set()
        return


class UI(object):
    qtmsg_blacklist_startswith=["WARNING: QApplication was not created in the main()","QSystemTrayIcon::setVisible: No Icon set","OleSetClipboard: Failed to set mime data (text/plain) on clipboard: COM error"]

    def __init__(self,input_colorscheme,input_fonts,input_UI_scaling_modifier,input_icons_b64,input_signaller,input_minimized,input_logger=None):
        self.colorscheme=json.loads(json.dumps(input_colorscheme))
        self.fonts=json.loads(json.dumps(input_fonts))
        self.UI_scaling_modifier=input_UI_scaling_modifier
        self.icons_b64=input_icons_b64
        self.active_logger=input_logger
        self.start_minimized=input_minimized
        qInstallMessageHandler(self.qtmsg_handler)
        self.is_ready=threading.Event()
        self.is_ready.clear()
        self.is_exiting=threading.Event()
        self.is_exiting.clear()
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.UI_signaller=input_signaller
        self.working_thread=threading.Thread(target=self.run_UI)
        self.working_thread.daemon=True
        self.working_thread.start()
        return

    def __del__(self):
        qInstallMessageHandler(None)
        return

    @staticmethod
    def qtmsg_handler(msg_type,msg_log_context,msg_string):
        for entry in UI.qtmsg_blacklist_startswith:
            if msg_string.startswith(entry):
                return

        sys.stderr.write(msg_string+u"\n")
        return

    def run_UI(self):
        self.UI_app=QApplication([])
        self.UI_app.setStyle("fusion")
        self.UI_window=Main_Window(self.colorscheme,self.fonts,self.UI_scaling_modifier,self.icons_b64,self.is_ready,self.is_exiting,self.has_quit,self.UI_signaller,self.start_minimized,self.active_logger)
        self.UI_window.show()
        self.UI_app.aboutToQuit.connect(self.UI_app.deleteLater)
        if self.start_minimized==False:
            self.UI_window.raise_()
            self.UI_window.activateWindow()
        sys.exit(self.UI_app.exec_())
        del self.UI_window
        del self.UI_app
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def IS_READY(self):
        return self.is_ready.is_set()==True

    def CONCLUDE(self):
        self.working_thread.join()
        return


class UI_Signaller(QObject):
    active_signal=pyqtSignal(object)

    def __init__(self):
        super(UI_Signaller,self).__init__(None)
        return

    def SEND_EVENT(self,input_type,input_data={}):
        output_signal_info={"type":input_type,"data":input_data}
        try:
            self.active_signal.emit(output_signal_info)
            return True
        except:
            return False


"""
WINS
"""


class Main_Window(QMainWindow):
    def __init__(self,input_colorscheme,input_fonts,input_UI_scaling_modifier,input_icons_b64,input_is_ready,input_is_exiting,input_has_quit,input_signaller,start_minimized,input_logger=None):
        global __author__
        global __version__
        global UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS

        super(Main_Window,self).__init__(None)

        self.active_logger=input_logger
        self.is_exiting=input_is_exiting
        self.has_quit=input_has_quit

        self.UI_scale=self.logicalDpiX()/96.0
        self.UI_scale*=input_UI_scaling_modifier
        font_point_size=input_fonts["<reference_point_size>"]
        input_fonts.pop("<reference_point_size>",None)
        
        self.font_cache={}
        for fontname in input_fonts:
            self.font_cache[fontname]=QFont(input_fonts[fontname]["type"])
            self.font_cache[fontname].setPointSize(font_point_size*input_fonts[fontname]["scale"]*input_UI_scaling_modifier)
            for fontproperty in input_fonts[fontname]["properties"]:
                if fontproperty=="bold":
                    self.font_cache[fontname].setBold(True)
                elif fontproperty=="italic":
                    self.font_cache[fontname].setItalic(True)
                elif fontproperty=="underline":
                    self.font_cache[fontname].setUnderline(True)
                elif fontproperty=="strikeout":
                    self.font_cache[fontname].setStrikeOut(True)

        self.setFixedSize(940*self.UI_scale,598*self.UI_scale)
        self.setWindowTitle(u"FileBot   v"+str(__version__)+u"   by "+str(__author__))
        self.setWindowFlags(self.windowFlags()|Qt.MSWindowsFixedSizeDialogHint)

        self.signal_response_calls={"logger_new_entry":self.signal_logger_new_entry,
                                    "attach_console":self.signal_attach_console,
                                    "detach_console":self.signal_detach_console,
                                    "close":self.signal_close,
                                    "report_processing_messages_state":self.signal_report_processing_messages_state,
                                    "set_bot_name":self.signal_set_bot_name,
                                    "set_status":self.signal_set_status,
                                    "report_timesync_clock_bias":self.signal_report_timesync_clock_bias,
                                    "commandfield_failed":self.signal_commandfield_failed,
                                    "commandfield_accepted":self.signal_commandfield_accepted,
                                    "close_standby":self.signal_close_standby}

        self.lock_log_queue=threading.Lock()
        self.lock_output_update=threading.Lock()
        self.lock_clipboard=threading.Lock()
        self.active_clipboard=QApplication.clipboard()
        self.UI_signaller=input_signaller
        self.UI_signaller.active_signal.connect(self.signal_response_handler)

        self.minimum_log_update_interval_milliseconds=UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS*1000.0
        self.close_standby=False
        self.is_minimized=False
        self.disable_hide=False
        self.command_history=[]
        self.output_queue=[]
        self.UI_lockstate=False
        self.app_state_is_online=False
        self.app_state_is_processing_messages=False
        self.command_history_index=-1
        self.console=None
        self.update_log_on_restore=False
        self.clipboard_queue=u""
        self.log_is_updating=False
        self.last_log_update_duration=0
        self.last_clipboard_selection_time=GetTickCount64()
        self.last_log_update_time=GetTickCount64()

        self.icon_cache={}
        for iconname in input_icons_b64:
            icon_qba=QByteArray.fromBase64(input_icons_b64[iconname],QByteArray.Base64Encoding)
            icon_qimg=QImage.fromData(icon_qba,"PNG")
            icon_qpix=QPixmap.fromImage(icon_qimg)
            self.icon_cache[iconname]=QIcon(icon_qpix)
        del input_icons_b64
        input_icons_b64=None

        self.setWindowIcon(self.icon_cache["default"])

        colors_window_text=input_colorscheme["window_text"]
        colors_window_background=input_colorscheme["window_background"]
        colors_selection_text=input_colorscheme["selection_text"]
        colors_selection_background=input_colorscheme["selection_background"]
        colors_input_text=input_colorscheme["input_text"]
        colors_background_IO=input_colorscheme["background_IO"]
        colors_background_IO_disabled=input_colorscheme["background_IO_disabled"]
        colors_scrollbar_text=input_colorscheme["scrollbar_text"]
        colors_scrollbar_background=input_colorscheme["scrollbar_background"]
        colors_scrollarea_background=input_colorscheme["scrollarea_background"]
        colors_output_border=input_colorscheme["output_border"]
        self.colors_status_username=input_colorscheme["status_username"]
        self.colors_status_ok=input_colorscheme["status_ok"]
        self.colors_status_warn=input_colorscheme["status_warn"]
        self.colors_status_error=input_colorscheme["status_error"]
        self.output_colors=input_colorscheme["output"]

        self.tray_current_state="deactivated"
        self.tray_current_text=u"FileBot"
        self.tray_icon=QSystemTrayIcon(self)
        self.tray_icon.setVisible(True)
        self.tray_icon.show()
        self.tray_icon.setIcon(self.icon_cache[self.tray_current_state])

        self.timer_update_output=QTimer(self)
        self.timer_update_output.timeout.connect(self.update_output)
        self.timer_update_output.setSingleShot(True)

        self.timer_queue_minimize_window=QTimer(self)
        self.timer_queue_minimize_window.timeout.connect(self.minimize_window)
        self.timer_queue_minimize_window.setSingleShot(True)

        self.timer_close=QTimer(self)
        self.timer_close.timeout.connect(self.close)
        self.timer_close.setSingleShot(True)

        self.timer_clipboard=QTimer(self)
        self.timer_clipboard.timeout.connect(self.clipboard_insert)
        self.timer_clipboard.setSingleShot(True)

        selection_colors="selection-color:#"+colors_selection_text+"; selection-background-color:#"+colors_selection_background+";"
        window_colors="color:#"+colors_window_text+"; background-color:#"+colors_window_background+";"

        self.options_macros={}
        self.tray_menu=QMenu(self)
        self.tray_menu.setStyleSheet("QMenu {"+window_colors+"} QMenu::item:selected {color:#"+colors_selection_text+"; background-color:#"+colors_selection_background+";}")
        self.options_macros["restore"]=self.tray_menu.addAction(u"Restore")
        self.options_macros["restore"].triggered.connect(self.traymenu_restore_onselect)
        self.options_macros["restore"].setFont(self.font_cache["general"])
        self.tray_menu.addSeparator()
        self.options_macros["exit"]=self.tray_menu.addAction(u"Exit")
        self.options_macros["exit"].triggered.connect(self.traymenu_exit_onselect)
        self.options_macros["exit"].setFont(self.font_cache["general"])
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_onactivate)

        self.options_macros["restore"].setVisible(False)

        self.label_botname=QGroupBox(self)
        self.label_botname.setGeometry(-10*self.UI_scale,-100*self.UI_scale,self.width()+10*self.UI_scale,self.height()+100*self.UI_scale)
        self.label_botname.setStyleSheet("QGroupBox {"+window_colors+"}")

        self.label_botname=QLabel(self)
        self.label_botname.setText(u"Bot name:")
        self.label_botname.setGeometry(12*self.UI_scale,6*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_botname.setFont(self.font_cache["general"])
        self.label_botname.setAlignment(Qt.AlignLeft)
        self.label_botname.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botname_value=QLabel(self)
        self.label_botname_value.setGeometry(65*self.UI_scale,6*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_botname_value.setFont(self.font_cache["status"])
        self.label_botname_value.setText("<not retrieved>")
        self.label_botname_value.setAlignment(Qt.AlignLeft)
        self.label_botname_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botstatus=QLabel(self)
        self.label_botstatus.setText(u"Status:")
        self.label_botstatus.setGeometry(384*self.UI_scale,6*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_botstatus.setFont(self.font_cache["general"])
        self.label_botstatus.setAlignment(Qt.AlignLeft)
        self.label_botstatus.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botstatus_value=QLabel(self)
        self.label_botstatus_value.setGeometry(422*self.UI_scale,6*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_botstatus_value.setFont(self.font_cache["status"])
        self.label_botstatus_value.setText(u"NOT STARTED")
        self.label_botstatus_value.setAlignment(Qt.AlignLeft)
        self.label_botstatus_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_clock_bias=QLabel(self)
        self.label_clock_bias.setText(u"Local machine clock bias(seconds):")
        self.label_clock_bias.setGeometry(625*self.UI_scale,6*self.UI_scale,300*self.UI_scale,26*self.UI_scale)
        self.label_clock_bias.setFont(self.font_cache["general"])
        self.label_clock_bias.setAlignment(Qt.AlignLeft)
        self.label_clock_bias.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_clock_bias_value=QLabel(self)
        self.label_clock_bias_value.setGeometry(796*self.UI_scale,6*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_clock_bias_value.setFont(self.font_cache["status"])
        self.label_clock_bias_value.setText(u"UNKNOWN")
        self.label_clock_bias_value.setAlignment(Qt.AlignLeft)
        self.label_clock_bias_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.textbox_output_model=QStandardItemModel(self)
        self.textbox_output=QListView(self)
        self.textbox_output.setModel(self.textbox_output_model)
        self.textbox_output.setFont(self.font_cache["log"])
        self.textbox_output.setGeometry(9*self.UI_scale,24*self.UI_scale,922*self.UI_scale,524*self.UI_scale)
        self.textbox_output.setStyleSheet("QListView::item:selected {border-top:"+str(int(1*self.UI_scale))+"px solid #"+colors_output_border+"; color:#"+colors_selection_text+"; background-color:#"+colors_selection_background+";} QListView::item {border-top:"+str(int(1*self.UI_scale))+"px solid #"+colors_output_border+";} QListView::enabled {background-color:#"+colors_background_IO+"; "+selection_colors+"} QListView::disabled {background-color:#"+colors_background_IO_disabled+"; "+selection_colors+"}")
        self.textbox_output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.textbox_output.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.textbox_output.setAcceptDrops(False)
        self.textbox_output.setToolTip(None)
        self.textbox_output.setWordWrap(True)
        self.textbox_output.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.textbox_output.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.textbox_output.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.textbox_output.setFrameStyle(QFrame.NoFrame)
        self.textbox_output.setToolTipDuration(0)
        self.textbox_output.setDragEnabled(False)
        self.textbox_output.verticalScrollBar().setStyleSheet("QScrollBar:vertical {border:"+str(int(1*self.UI_scale))+"px solid #"+colors_scrollbar_background+"; color:#"+colors_scrollbar_text+"; background-color:#"+colors_scrollbar_background+"; width:"+str(int(15*self.UI_scale))+"px;} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {color:#"+colors_scrollbar_text+"; background-color:#"+colors_scrollarea_background+"}")
        self.textbox_output.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.textbox_output.installEventFilter(self)

        self.label_commands=QLabel(self)
        self.label_commands.setText(u"INPUT COMMANDS:")
        self.label_commands.setGeometry(410*self.UI_scale,552*self.UI_scale,120*self.UI_scale,26*self.UI_scale)
        self.label_commands.setFont(self.font_cache["general"])
        self.label_commands.setAlignment(Qt.AlignLeft)
        self.label_commands.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.input_commandfield=QLineEdit(self)
        self.input_commandfield.setGeometry(9*self.UI_scale,566*self.UI_scale,922*self.UI_scale,22*self.UI_scale)
        self.input_commandfield.setFont(self.font_cache["log"])
        self.input_commandfield.setMaxLength(147)
        self.input_commandfield.setAcceptDrops(False)
        self.input_commandfield.returnPressed.connect(self.input_commandfield_onsend)
        self.input_commandfield.installEventFilter(self)
        self.input_commandfield.setStyleSheet("QLineEdit::enabled {background-color:#"+colors_background_IO+"; color:#"+colors_input_text+"; "+selection_colors+"} QLineEdit::disabled {background-color:#"+colors_background_IO_disabled+"; color:#"+colors_input_text+"; "+selection_colors+"}")

        for element in self.output_colors:
            newcolor=QColor()
            newcolor.setNamedColor("#"+self.output_colors[element])
            self.output_colors[element]=newcolor

        self.set_UI_lock(True)
        self.update_UI_usability()
        self.update_tray_icon()

        if start_minimized==True:
            self.timer_queue_minimize_window.start(0)

        input_is_ready.set()
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("GUINTRFC",input_text)
        return

    def minimize_window(self):
        self.options_macros["restore"].setVisible(True)
        self.update_minimized_state(True)
        self.setWindowState(Qt.WindowMinimized)
        self.hide()
        return

    def clipboard_insert(self):
        global UI_CLIPBOARD_COPY_TIMEOUT_SECONDS

        if self.is_exiting.is_set()==True:
            return

        self.lock_clipboard.acquire()
        start_time=GetTickCount64()
        while self.active_clipboard.text()!=self.clipboard_queue and (GetTickCount64()-start_time)/1000.0<UI_CLIPBOARD_COPY_TIMEOUT_SECONDS:
            self.active_clipboard.setText(self.clipboard_queue)
            QCoreApplication.processEvents()
        self.clipboard_queue=u""
        self.lock_clipboard.release()
        return

    def queue_clipboard_insert(self,input_text):
        if input_text==u"":
            return

        self.lock_clipboard.acquire()
        self.clipboard_queue=input_text
        self.lock_clipboard.release()
        self.timer_clipboard.start(0)
        return

    def queue_close_event(self):
        if self.is_exiting.is_set()==True:
            return

        self.timer_close.start(0)
        return

    def eventFilter(self,widget,event):
        global UI_CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS

        if widget==self.input_commandfield:
            if self.input_commandfield.isEnabled()==True:
                if event.type()==QEvent.KeyPress:
                    key_pressed=event.key()
                    change_index=0
                    if key_pressed==Qt.Key_Up:
                        change_index=-1
                    elif key_pressed==Qt.Key_Down:
                        change_index=1

                    if change_index!=0:
                        new_index=self.command_history_index+change_index
                        if new_index>=0 and new_index<=len(self.command_history):
                            self.command_history_index=new_index
                            if self.command_history_index!=len(self.command_history):
                                self.input_commandfield.setText(self.command_history[self.command_history_index])
                                self.input_commandfield.selectAll()
                            else:
                                self.input_commandfield.setText(u"")
                        return True

        elif widget==self.textbox_output:
            if event.type()==QEvent.KeyPress:
                key_pressed=event.key()
                if key_pressed==Qt.Key_Escape:
                    rows=self.textbox_output.selectionModel().clearSelection()
                elif key_pressed==Qt.Key_C or key_pressed==Qt.Key_Insert:
                    if event.modifiers()&Qt.ControlModifier:
                        if (GetTickCount64()-self.last_clipboard_selection_time)/1000.0>UI_CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS:
                            self.last_clipboard_selection_time=GetTickCount64()
                            rows=self.textbox_output.selectionModel().selectedRows()
                            if len(rows)>0:
                                clipboard_data=u""
                                cache_model=self.textbox_output.model()
                                for row in rows:
                                    clipboard_data+=cache_model.itemData(row)[0]+u"\n"
                                self.queue_clipboard_insert(clipboard_data)
                        return True

        return QWidget.eventFilter(self,widget,event)

    def queue_log_update(self):
        if self.log_is_updating==False:
            self.log_is_updating=True
            extra_timer=max(self.last_log_update_duration-GetTickCount64()+self.last_log_update_time,0)*1.1
            self.timer_update_output.start(max(0,self.last_log_update_time+self.minimum_log_update_interval_milliseconds+extra_timer-GetTickCount64()))
        return

    def update_output(self):
        global UI_OUTPUT_ENTRIES_MAX

        if self.is_exiting.is_set()==True:
            return

        self.lock_log_queue.acquire()
        self.last_log_update_duration=GetTickCount64()
        get_output_queue=self.output_queue[:]
        self.output_queue=[]
        self.lock_log_queue.release()
        get_output_queue_len=len(get_output_queue)

        self.lock_output_update.acquire()

        rows_to_delete=max(0,self.textbox_output_model.rowCount()+get_output_queue_len-UI_OUTPUT_ENTRIES_MAX)
        starting_row=self.textbox_output_model.rowCount()-rows_to_delete
        index=-1

        self.textbox_output.setUpdatesEnabled(False)
        self.textbox_output_model.removeRows(0,rows_to_delete)
        self.textbox_output_model.insertRows(starting_row,get_output_queue_len)
        for entry in get_output_queue:
            index+=1
            target_row=starting_row+index
            self.textbox_output_model.setItem(target_row,QStandardItem(entry[0]))
            self.textbox_output_model.setData(self.textbox_output_model.index(target_row,0),entry[1],Qt.ForegroundRole)
        self.textbox_output.scrollToBottom()
        self.textbox_output.setUpdatesEnabled(True)

        self.last_log_update_time=GetTickCount64()
        self.last_log_update_duration=self.last_log_update_time-self.last_log_update_duration
        self.log_is_updating=False

        self.lock_output_update.release()

        return

    def update_tray_icon(self):
        global __version__

        tray_text_new=u"FileBot v"+str(__version__)+u"\nBot name: "
        if self.label_botname_value.text()!=u"<not retrieved>":
            tray_text_new+=u"\""+self.label_botname_value.text()+u"\"\nStatus: "
        else:
            tray_text_new+=u"<not retrieved>\n"

        tray_candidate="default"
        if self.app_state_is_online==True:
            if self.app_state_is_processing_messages==True:
                tray_candidate="busy"
        else:
            tray_candidate="deactivated"

        if tray_candidate=="default":
            tray_text_new+=u"ONLINE"
        elif tray_candidate=="deactivated":
            tray_text_new+=u"OFFLINE"
        elif tray_candidate=="busy":
            tray_text_new+=u"ONLINE (processing messages)"

        if self.tray_current_text!=tray_text_new:
            self.tray_current_text=tray_text_new
            self.tray_icon.setToolTip(self.tray_current_text)

        if self.tray_current_state!=tray_candidate:
            self.tray_current_state=tray_candidate
            self.tray_icon.setIcon(self.icon_cache[self.tray_current_state])
        return

    def add_to_output_queue(self,input_line):
        global UI_OUTPUT_ENTRIES_MAX

        if input_line.endswith("\n"):
            input_line=input_line[:-1]
        text_source=""
        if len(input_line)>=29:
            if input_line[20]==u"[" and input_line[29]==u"]":
                try:
                    text_source=str(input_line[21:29])
                except:
                    pass

        if text_source in self.output_colors:
            text_color=self.output_colors[text_source]
        else:
            text_color=self.output_colors["<DEFAULT>"]

        self.lock_log_queue.acquire()
        self.output_queue+=[(input_line,text_color)]
        if len(self.output_queue)>UI_OUTPUT_ENTRIES_MAX:
            del self.output_queue[0]
        self.lock_log_queue.release()

        return

    def add_output_line(self,input_line):
        self.add_to_output_queue(input_line)

        if self.is_minimized==False:
            self.queue_log_update()
        else:
            self.update_log_on_restore=True
        return

    def input_commandfield_onsend(self):
        clean_text=self.input_commandfield.text().strip()
        self.input_commandfield.setText(clean_text)
        if clean_text==u"":
            return
        self.send_console_command(clean_text)
        return

    def send_console_command(self,input_command):
        if self.console is None:
            return
        self.input_commandfield.setEnabled(False)
        self.console.SEND_COMMAND(input_command)
        return

    def notify_console_minimized(self,input_state):
        if self.console is None:
            return
        self.console.NOTIFY_MINIMIZED_STATE(input_state)
        return

    def set_UI_lock(self,new_state):
        if new_state!=self.UI_lockstate:
            self.UI_lockstate=new_state
            do_console_disable=self.UI_lockstate or self.console is None
            self.lock_output_update.acquire()
            self.textbox_output.setDisabled(self.UI_lockstate)
            self.lock_output_update.release()
            self.input_commandfield.setDisabled(do_console_disable or self.close_standby)
            if do_console_disable==False:
                self.input_commandfield.setFocus()
        return

    def update_UI_usability(self):
        usable=self.console is not None
        self.set_UI_lock(not usable)
        return

    def signal_response_handler(self,event):
        if self.is_exiting.is_set()==True:
            return

        event_type=event["type"]
        if event_type in self.signal_response_calls:
            self.signal_response_calls[event_type](event["data"])
        else:
            self.log(u"ERROR: Received unsupported signal event type: \""+event_type+u"\".")
        return

    def signal_logger_new_entry(self,event_data):
        self.add_output_line(event_data)
        return

    def signal_attach_console(self,event_data):
        self.console=event_data
        self.notify_console_minimized(self.is_minimized)
        self.input_commandfield.setEnabled(not self.UI_lockstate and not self.close_standby)
        self.update_UI_usability()
        return

    def signal_detach_console(self,event_data):
        if self.console is not None:
            self.notify_console_minimized(False)
            self.console=None
            self.input_commandfield.setEnabled(False)
            self.update_UI_usability()
        return

    def signal_close(self,event_data):
        self.queue_close_event()
        return

    def signal_report_processing_messages_state(self,event_data):
        if self.app_state_is_processing_messages!=event_data:
            self.app_state_is_processing_messages=not self.app_state_is_processing_messages
            self.update_tray_icon()
        return

    def signal_set_bot_name(self,event_data):
        self.label_botname_value.setText(event_data)
        self.label_botname_value.setStyleSheet("QLabel {color: #"+self.colors_status_username+"}")
        self.update_tray_icon()
        return

    def signal_set_status(self,event_data):
        self.label_botstatus_value.setText(event_data)
        if event_data==u"ONLINE":
            self.label_botstatus_value.setStyleSheet("QLabel {color: #"+self.colors_status_ok+"}")
            self.app_state_is_online=True
            self.update_tray_icon()
        elif event_data==u"OFFLINE":
            self.label_botstatus_value.setStyleSheet("QLabel {color: #"+self.colors_status_error+"}")
            self.app_state_is_online=False
            self.update_tray_icon()
        return

    def signal_report_timesync_clock_bias(self,event_data):
        clock_bias=float(event_data.replace("+","").replace("-",""))
        if clock_bias>=60:
            time_stylesheet="QLabel {color: #"+self.colors_status_error+"}"
        elif clock_bias>=30:
            time_stylesheet="QLabel {color: #"+self.colors_status_warn+"}"
        else:
            time_stylesheet="QLabel {color: #"+self.colors_status_ok+"}"
        self.label_clock_bias_value.setStyleSheet(time_stylesheet)
        self.label_clock_bias_value.setText(event_data)
        return

    def signal_commandfield_failed(self,event_data):
        if self.console is not None:
            do_enable=not self.UI_lockstate
            self.input_commandfield.setEnabled(do_enable and not self.close_standby)
            if do_enable==True:
                self.input_commandfield.selectAll()
                self.input_commandfield.setFocus()
        return

    def signal_commandfield_accepted(self,event_data):
        global UI_COMMAND_HISTORY_MAX

        add_command=len(self.command_history)==0
        if add_command==False:
            if self.command_history[-1].lower().strip()!=self.input_commandfield.text().lower().strip():
                add_command=True

        if add_command==True:
            self.command_history+=[self.input_commandfield.text()]
            if len(self.command_history)>UI_COMMAND_HISTORY_MAX:
                del self.command_history[0]
            self.command_history_index=len(self.command_history)

        self.input_commandfield.setText(u"")
        self.input_commandfield.setFocus()
        return

    def signal_close_standby(self,event_data):
        self.close_standby=True
        self.textbox_output.setEnabled(True)
        self.input_commandfield.setEnabled(False)
        return

    def hideEvent(self,event):
        if self.disable_hide==True:
            event.ignore()
            event.setAccepted(False)
        return

    def update_minimized_state(self,new_state):
        self.is_minimized=new_state
        self.notify_console_minimized(new_state)
        return

    def changeEvent(self,event):
        if event.type()==QEvent.WindowStateChange:
            getwinstate=self.windowState()
            if getwinstate==Qt.WindowMinimized:
                self.options_macros["restore"].setVisible(True)
                self.update_minimized_state(True)
                self.hide()
            elif getwinstate==Qt.WindowNoState:
                self.options_macros["restore"].setVisible(False)
                self.update_minimized_state(False)
                self.show()
                self.activateWindow()
                if self.update_log_on_restore==True:
                    self.update_log_on_restore=False
                    self.queue_log_update()
        return QWidget.changeEvent(self,event)

    def tray_onactivate(self,reason):
        if self.has_quit.is_set()==True:
            return

        if reason==QSystemTrayIcon.DoubleClick:
            getwinstate=self.windowState()
            if getwinstate==Qt.WindowMinimized:
                self.options_macros["restore"].setVisible(False)
                self.setWindowState(Qt.WindowNoState)
                self.show()
                self.activateWindow()
            elif getwinstate==Qt.WindowNoState:
                self.options_macros["restore"].setVisible(True)
                self.setWindowState(Qt.WindowMinimized)
                self.hide()
        return

    def traymenu_restore_onselect(self):
        if self.windowState()==Qt.WindowMinimized:
            self.setWindowState(Qt.WindowNoState)
        return

    def traymenu_exit_onselect(self):
        self.close()
        return

    def closeEvent(self,event):
        if self.is_exiting.is_set()==True:
            return

        self.log(u"UI closing...")

        self.is_exiting.set()

        self.tray_icon.setVisible(False)
        self.tray_icon.hide()
        del self.tray_icon

        self.has_quit.set()
        return

class FileBot(object):
    user_token_max_length_bytes=256
    user_entry_line_max_length_bytes=768
    banned_TLS_algorithms=["ANY","SHA1","DHE","CHACHA20-POLY1305","AES-128-CBC","AES-256-CBC","AES-128-GCM","SHA256"]

    def __init__(self,input_working_dir,input_max_7zip_tasks_per_user,input_color_scheme,input_fonts,input_UI_scale_modifier,input_start_minimized,input_log_to_stdout,input_startup_message_additional_text=u""):
        global __author__
        global __version__
        global MAX_BOT_USERS_BY_CPU_ARCHITECTURE

        address_size=ctypes.sizeof(ctypes.c_voidp)
        if address_size==4:
            self.cpu_architecture="32"
        elif address_size==8:
            self.cpu_architecture="64"
        else:
            raise Exception("FileBot cannot instantiate on this CPU architecture.")

        self.path_system32=None
        for system_variable in ["WINDIR","SYSTEMROOT"]:
            try:
                get_path=terminate_with_backslash(os.path.join(os.environ[system_variable],u"System32").strip().replace("/","\\"))
                if os.path.isdir(get_path)==True:
                    self.path_system32=get_path
                    break
            except:
                pass
        if self.path_system32 is None:
            raise Exception("Could not obtain SYSTEM32 folder path.")

        self.process_id=os.getpid()
        self.current_process_handle=ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS,True,self.process_id)
        self.logger=None
        self.active_time_provider=None
        self.active_UI=None
        self.request_sync_time=None
        self.bot_user_limit=MAX_BOT_USERS_BY_CPU_ARCHITECTURE[self.cpu_architecture]
        self.working_dir=terminate_with_backslash(input_working_dir.strip().replace("/","\\"))
        self.allowed_TLS_algorithms=self.get_TLS_allowed_algorithms(FileBot.banned_TLS_algorithms)
        self.max_7zip_tasks_per_user=input_max_7zip_tasks_per_user
        self.color_scheme=input_color_scheme
        self.fonts=input_fonts
        self.UI_scale_modifier=input_UI_scale_modifier
        self.start_minimized=input_start_minimized
        self.log_to_stdout=input_log_to_stdout
        self.startup_message_additional_text=input_startup_message_additional_text
        return

    def RUN(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        if threading.current_thread().__class__.__name__!="_MainThread":
            raise Exception("FileBot needs to be run from the main thread.")

        self.logger=Logger(self.path_system32,os.path.join(self.working_dir,u"log.txt"))
        self.logger.LOG_TO_STDOUT(self.log_to_stdout)

        UI_Signal=UI_Signaller()
        self.logger.ATTACH_SIGNALLER(UI_Signal)

        app_icons_b64={"default":Get_B64_Resource("icons/default"),"deactivated":Get_B64_Resource("icons/deactivated"),"busy":Get_B64_Resource("icons/busy")}
        self.active_UI=UI(self.color_scheme,self.fonts,self.UI_scale_modifier,app_icons_b64,UI_Signal,self.start_minimized,self.logger)
        del app_icons_b64
        app_icons_b64=None

        while self.active_UI.IS_READY()==False:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

        self.logger.ACTIVATE()

        self.log(u"==================================== FileBot ====================================")
        self.log(u"Author: "+str(__author__))
        self.log(u"Version: "+str(__version__))
        self.log(u"=================================================================================")
        self.log(u"7-ZIP (C) Igor Pavlov; distributed under GNU LGPL license; https://www.7-zip.org/\n")
        self.log(u"\n\nREQUIREMENTS:\n"+\
            u"-bot token in \"token.txt\"\n"+\
            u"-users list in \"userlist.txt\" with one entry per line, formatted as such: <USERNAME>|<HOME PATH>\n"+\
            u"Begin home path with \">\" to allow writing. To allow access to all drives, set the path to \"*\".\n"+\
            u"If a user has no username, you can add them via first name and last name with a \"#\" before each. EXAMPLE:\n"+\
            u"FIRST NAME: John LAST NAME: Doe -> #John#Doe\n"+\
            u"Note that this method only works if the user has no username, and that a \"#\" is required even if the last name is empty.\n"+\
            u"Note that users without \"*\" home path will be disallowed from accessing FileBot's running folder even if it's a valid subfolder.\n\n"+\
            u"EXAMPLE ENTRIES:\n"+\
            u"JohnDoe|C:\\MySharedFiles\n"+\
            u"TrustedUser|>*\n\n"+\
            u"A maximum of "+str(self.bot_user_limit)+u" users are supported.\n\n"+self.startup_message_additional_text+u"\n")

        self.log(u"Process ID is "+str(self.process_id)+u". CPU architecture is "+self.cpu_architecture+u"-bit.")

        fatal_error=False
        collect_bot_token=""
        collect_user_file_entries=[]
        collect_allowed_users=[]

        try:
            file_handle=open(os.path.join(self.working_dir,u"token.txt"),"rb")
            collect_bot_token=file_handle.read(FileBot.user_token_max_length_bytes)
            file_handle.close()
        except:
            self.log(u"ERROR: Make sure the file \"token.txt\" exists and contains the bot token.")
            fatal_error=True

        if fatal_error==False:
            collect_bot_token=self.bot_token_from_bytes(collect_bot_token)
            if collect_bot_token=="":
                self.log(u"ERROR: Make sure the token is correctly written in \"token.txt\".")
                fatal_error=True

        if fatal_error==False:
            file_handle=None
            try:
                file_handle=open(os.path.join(self.working_dir,u"userlist.txt"),"rb")
                all_lines=str(file_handle.read(FileBot.user_entry_line_max_length_bytes*self.bot_user_limit),"utf8").split(u"\n")
                file_handle.close()
                file_handle=None
                for line in all_lines:
                    line=line.strip()
                    if line!=u"":
                        collect_user_file_entries+=[line]
            except:
                if file_handle is not None:
                    try:
                        file_handle.close()
                    except:
                        file_handle=None
                self.log(u"ERROR: Could not obtain any valid user entries from \"userlist.txt\".")
                fatal_error=True

        if fatal_error==False:
            for entry in collect_user_file_entries:
                new_user=self.user_entry_from_string(entry)
                if new_user["error_message"]==u"":
                    collect_allowed_users+=[new_user]
                    if len(collect_allowed_users)==self.bot_user_limit:
                        break
                else:
                    self.log(u"WARNING: "+new_user["error_message"])

            collect_user_file_entries=[]
            if len(collect_allowed_users)>0:
                self.log(u"Number of users to listen for: "+str(len(collect_allowed_users))+u".")
            else:
                self.log(u"ERROR: There were no valid user entries to add.")
                fatal_error=True

        if fatal_error==False:
            try:
                active_7ZIP_handler=Task_Handler_7ZIP(self.path_system32,self.working_dir,Get_B64_Resource("binaries/7zipx"+self.cpu_architecture),self.max_7zip_tasks_per_user,self.logger)
            except:
                self.log(u"The 7-ZIP binary could not be written. Make sure you have write permissions to the application folder.")
                fatal_error=True

        if fatal_error==False:
            self.active_time_provider=Time_Provider(self.allowed_TLS_algorithms)
            self.active_time_provider.ADD_SUBSCRIBER(UI_Signal)

            self.log(u"Starting 7-ZIP Task Handler...")
            active_7ZIP_handler.START()

            initial_time_sync_failed_once=False
            self.log(u"Performing initial time synchronization via Internet...")
            sync_result={"success":False}
            while sync_result["success"]==False and self.active_UI.IS_RUNNING()==True:
                sync_result=self.active_time_provider.SYNC()
                if initial_time_sync_failed_once==False:
                    if sync_result["success"]==False:
                        initial_time_sync_failed_once=True
                        self.log(u"Initial time synchronization failed. Will keep trying...")

            if sync_result["success"]==True:
                self.log(u"Initial time synchronization complete. Local clock bias is "+sync_result["time_difference"]+u" second(s).")

                user_handle_instances=[]

                collect_allowed_usernames=[]
                for sender in collect_allowed_users:
                    collect_allowed_usernames+=[sender["username"]]

                active_bot_listener=Bot_Listener(collect_bot_token,self.allowed_TLS_algorithms,collect_allowed_usernames,self.active_time_provider,UI_Signal,self.logger)
                self.log(u"Starting Bot Listener...")
                active_bot_listener.START()

                while active_bot_listener.IS_READY()==False and self.active_UI.IS_RUNNING()==True:
                    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
       
                if self.active_UI.IS_RUNNING()==True:

                    self.log(u"User message handler(s) starting up...")
                    for sender in collect_allowed_users:
                        user_handle_instances+=[User_Message_Handler(self.path_system32,collect_bot_token,self.allowed_TLS_algorithms,sender["home"],sender["username"],sender["allow_write"],[environment_info["working_dir"]],active_bot_listener,self.active_time_provider,active_7ZIP_handler,self.logger)]

                    self.request_sync_time=threading.Event()
                    self.request_sync_time.clear()

                    active_user_console=User_Console(user_handle_instances,UI_Signal,active_7ZIP_handler,self.request_sync_time,self.logger)
                    self.log(u"Starting User Console...")
                    active_user_console.START()

                    self.log(u"Startup complete. Waiting for UI thread to finish...")
                    self.main_loop()
                    self.log(u"Left UI thread waiting loop.")

                    self.request_sync_time=None
                    self.active_time_provider.REMOVE_SUBSCRIBER(UI_Signal)

                    self.log(u"Requesting stop to User Console...")
                    active_user_console.REQUEST_STOP()

                    active_user_console.CONCLUDE()
                    del active_user_console
                    self.log(u"Confirm User Console exit.")

                self.log(u"Requesting stop to 7-ZIP Task Handler...")
                active_7ZIP_handler.REQUEST_STOP()

                self.log(u"Requesting stop to Bot Listener...")
                active_bot_listener.REQUEST_STOP()

                active_bot_listener.CONCLUDE()
                del active_bot_listener
                self.log(u"Confirm Bot Listener exit.")

                active_7ZIP_handler.CONCLUDE()
                del active_7ZIP_handler
                self.log(u"Confirm 7-ZIP Task Handler exit.")

                while len(user_handle_instances)>0:
                    del user_handle_instances[0]

            del self.active_time_provider
            self.active_time_provider=None

        else:

            self.log(u"The program can now be closed.")
            UI_Signal.SEND_EVENT("close_standby")

        self.logger.DETACH_SIGNALLER()
        self.active_UI.CONCLUDE()
        del self.active_UI
        self.active_UI=None
        self.log(u"Confirm UI exit.")

        self.log(u"FileBot has finished.")
        self.logger.DEACTIVATE()
        del self.logger
        self.logger=None

        self.flush_std_buffers()
        return

    def log(self,input_text):
        if self.logger is not None:
            self.logger.LOG("MAINTHRD",input_text)
        return

    def flush_std_buffers(self):
        sys.stdout.flush()
        sys.stderr.flush()
        return

    def bot_token_from_bytes(self,input_bytes):
        retval=input_bytes
        try:
            retval=str(retval,"utf8").strip()
        except:
            return ""
        if len(retval)==0 or len(retval)>64:
            return ""
        for c in retval:
            if c not in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_:":
                return ""
        if retval.count(":")>1:
            return ""
        if len(retval)==0 or len(retval)>64:
            return ""
        return retval
    
    def user_entry_from_string(self,input_string):
        retval={"username":u"","home":u"","allow_write":False,"error_message":""}

        segments=[]

        try:
            segments=input_string.split("|")
            for i in range(len(segments)):
                segments[i]=segments[i].strip()

            if len(segments)==1:
                raise ValueError(u"Home path was not present.")
            elif len(segments)>2:
                raise ValueError(u"Wrong number of \"|\"-separated characters.")

            retval["username"]=segments[0]
            retval["home"]=segments[1].strip()
            retval["allow_write"]=False

            if retval["username"].count(u"#")!=2 and retval["username"].count(u"#")!=0:
                raise ValueError(u"Username contained an incorrect number of \"#\" characters.")

            username_nohashes=retval["username"].replace(u"#",u"")

            if username_nohashes==u"":
                raise ValueError("Username was empty.")

            if username_nohashes[0] in u"_0123456789":
                raise ValueError(u"Username cannot begin with a number or underscore.")

            for c in username_nohashes:
                if c.lower() not in u"_0123456789abcdefghijklmnopqrstuvwxyz":
                    raise ValueError(u"Username contains invalid characters.")

            if retval["home"].startswith(u">")==True:
                retval["allow_write"]=True
                retval["home"]=retval["home"][1:]
            if retval["home"]==u"":
                raise ValueError("Home path was empty.")
            retval["home"]=retval["home"].replace(u"/",u"\\")
            if retval["home"]!=u"*":
                retval["home"]=terminate_with_backslash(retval["home"])

            for c in retval["home"]:
                if c in u"|<>?":
                    raise ValueError(u"Home path contains invalid characters.")

            if (retval["home"].count(u"*")>1 and len(retval["home"])>1) or retval["home"].count(u":")>1 or retval["home"].startswith(u"\\")==True:
                raise ValueError(u"Home path contains invalid characters.")

            if u"\\.\\" in retval["home"] or u"\\..\\" in retval["home"] or u"\\...\\" in retval["home"] or retval["home"].startswith(u"\\\\")==True or len(retval["home"])>255:
                raise ValueError(u"Home path format is invalid.")

        except:
            return {"error_message":u"User entry \""+input_string+u"\" was not validly formatted: "+str(sys.exc_info()[0])+u" "+str(sys.exc_info()[1]),"username":u"","home":u"","allow_write":False}

        return retval

    def get_TLS_allowed_algorithms(self,input_banned_TLS_algorithms):
        cipherlist=ssl.create_default_context().get_ciphers()
        banned_algorithms=[i.upper() for i in input_banned_TLS_algorithms]
    
        cipherstring=""
        for cipher in cipherlist:
            if "digest" in cipher and "auth" in cipher and "symmetric" in cipher and "kea" in cipher:
                ciphername=cipher["name"]
    
                if cipher["digest"] is not None:
                    cipher_digest=cipher["digest"].upper()
                else:
                    cipher_digest=""
    
                if cipher["auth"] is not None:
                    cipher_auth=cipher["auth"].upper()
                    if cipher_auth.startswith("AUTH-"):
                        cipher_auth=cipher_auth[len("AUTH-"):]
                else:
                    cipher_auth=""
    
                if cipher["symmetric"] is not None:
                    cipher_symmetric=cipher["symmetric"].upper()
                else:
                    cipher_symmetric=""
    
                if cipher["kea"] is not None:
                    cipher_kea=cipher["kea"].upper()
                    if cipher_kea.startswith("KX-"):
                        cipher_kea=cipher_kea[len("KX-"):]
                else:
                    cipher_kea=""
    
                digest_ok=False
                auth_ok=False
                symmetric_ok=False
                kea_ok=False
    
                if cipher_digest!="":
                    if cipher_digest not in banned_algorithms:
                        digest_ok=True
                else:
                    digest_ok=True
    
                if digest_ok==True:            
                    if cipher_auth!="":
                        if cipher_auth not in banned_algorithms:
                            auth_ok=True
                    else:
                        auth_ok=True
    
                if digest_ok==True and auth_ok==True:
                    if cipher_symmetric!="":
                        if cipher_symmetric not in banned_algorithms:
                            symmetric_ok=True
                    else:
                        symmetric_ok=True
    
                if digest_ok==True and auth_ok==True and symmetric_ok==True:
                    if cipher_kea!="":
                        if cipher_kea not in banned_algorithms:
                            kea_ok=True
                    else:
                        kea_ok=True
    
                if digest_ok==True and auth_ok==True and symmetric_ok==True and kea_ok==True:
                    cipherstring+=":"+ciphername
    
        if cipherstring.startswith(":")==True:
            cipherstring=cipherstring[1:]
    
        return cipherstring

    def main_loop(self):
        global MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS
        global MAINTHREAD_HEARTBEAT_SECONDS
        global SERVER_TIME_RESYNC_INTERVAL_SECONDS

        priority_check_interval_milliseconds=MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS*1000
        last_process_priority_check=GetTickCount64()-priority_check_interval_milliseconds
        last_server_time_check=datetime.datetime.utcnow()

        while self.active_UI.IS_RUNNING()==True:
            time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)

            self.flush_std_buffers()

            if GetTickCount64()-last_process_priority_check>=priority_check_interval_milliseconds:
                try:
                    if win32process.GetPriorityClass(self.current_process_handle)!=win32process.IDLE_PRIORITY_CLASS:
                        win32process.SetPriorityClass(self.current_process_handle,win32process.IDLE_PRIORITY_CLASS)
                        self.log(u"Idle process priority set.")
                except:
                    self.log(u"Error managing process priority.")
                last_process_priority_check=GetTickCount64()

            if abs((datetime.datetime.utcnow()-last_server_time_check).total_seconds())>=SERVER_TIME_RESYNC_INTERVAL_SECONDS or self.request_sync_time.is_set()==True:
                self.log(u"Performing time synchronization via Internet...")
                sync_result=self.active_time_provider.SYNC()
                if sync_result["success"]==True:
                    self.log(u"Time synchronization complete. Local clock bias is "+sync_result["time_difference"]+u" second(s).")
                else:
                    self.log(u"Time synchronization failed.")
                self.request_sync_time.clear()
                last_server_time_check=datetime.datetime.utcnow()

        return


"""
MAIN
"""


if Versions_Str_Equal_Or_Less(PYQT5_MAX_SUPPORTED_COMPILE_VERSION,PYQT_VERSION_STR)==False:
    sys.stderr.write(u"WARNING: PyQt5 version("+PYQT_VERSION_STR+u") is higher than the maximum supported version for compiling("+PYQT5_MAX_SUPPORTED_COMPILE_VERSION+u"). The application may run off source code but will fail to compile.\n")
    sys.stderr.flush()

environment_info=Get_Runtime_Environment()

argument_start_minimized=False
argument_log_to_stdout=False

for argument in environment_info["arguments"]:
    argument=argument.lower().strip()

    if argument==u"/minimized":
        argument_start_minimized=True
    elif argument==u"/stdout":
        argument_log_to_stdout=True

if environment_info["running_from_source"]==True:
    argument_log_to_stdout=True

FileBotInstance=FileBot(environment_info["working_dir"],MAX_7ZIP_TASKS_PER_USER,COLOR_SCHEME,FONTS,UI_SCALE_MODIFIER,argument_start_minimized,argument_log_to_stdout,STARTUP_MESSAGE_ADDITIONAL_TEXT)
FileBotInstance.RUN()
del FileBotInstance
