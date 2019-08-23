__version__="1.90"
__author__="Searinox Navras"


"""
INIT
"""


import base64
import time
import datetime
import sys
import os
import threading
import shutil
import ctypes
import win32api
import win32con
import win32process
import urllib3
import ssl
import json
from PyQt5.QtCore import (QObject,pyqtSignal,QByteArray,Qt,QEvent,QTimer,QCoreApplication,qInstallMessageHandler)
from PyQt5.QtWidgets import (QApplication,QLabel,QListView,QWidget,QSystemTrayIcon,QMenu,QLineEdit,QMainWindow,QFrame,QAbstractItemView,QGroupBox)
from PyQt5.QtGui import (QIcon,QImage,QPixmap,QFont,QColor,QStandardItemModel,QStandardItem)

def Get_B64_Resource(input_path):
    import resources_base64
    return resources_base64.Get_Resource(input_path)

MAINTHREAD_HEARTBEAT_SECONDS=0.085
PENDING_ACTIVITY_HEARTBEAT_SECONDS=0.05
MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS=60
COMMAND_CHECK_INTERVAL_SECONDS=0.2
SERVER_TIME_RESYNC_INTERVAL_SECONDS=60*60*8
BOT_LISTENER_THREAD_HEARTBEAT_SECONDS=0.8
USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS=0.1
USER_MESSAGE_HANDLER_SENDMSG_WAIT_POLLING_SECONDS=0.1
UI_CLIPBOARD_COPY_TIMEOUT_SECONDS=1.2
UI_CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS=0.125
TASKS_7ZIP_THREAD_HEARTBEAT_SECONDS=0.2
TASKS_7ZIP_UPDATE_INTERVAL_SECONDS=1.25
TASKS_7ZIP_DELETE_TIMEOUT_SECONDS=1.5
UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS=0.055

TELEGRAM_API_REQUEST_TIMEOUT_SECONDS=4
TELEGRAM_API_MAX_GLOBAL_IMS=30
TELEGRAM_API_MAX_GLOBAL_TIME_INTERVAL_SECONDS=1
TELEGRAM_API_UPLOAD_TIMEOUT_SECONDS=60*60
TELEGRAM_API_DOWNLOAD_CHUNK_BYTES=256*256
TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES=1024*1024*50
TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES=1024*1024*20
TELEGRAM_API_MAX_IM_SIZE_BYTES=4096
BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS=30

WEB_REQUEST_CONNECT_TIMEOUT_SECONDS=5
MAX_7ZIP_TASKS_PER_USER=3
MAX_BOT_USERS=100

COMMAND_HISTORY_MAX=50
OUTPUT_ENTRIES_MAX=5000

CUSTOM_UI_SCALING=1.125
QTMSG_BLACKLIST_STARTSWITH=["WARNING: QApplication was not created in the main()","QSystemTrayIcon::setVisible: No Icon set","OleSetClipboard: Failed to set mime data (text/plain) on clipboard: COM error"]
APP_ICONS_B64={"default":Get_B64_Resource("icons/default"),"deactivated":Get_B64_Resource("icons/deactivated"),"busy":Get_B64_Resource("icons/busy")}
FONT_POINT_SIZE=8
FONTS={"general":
       {"type":"Monospace","scale":1,"properties":[]},
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
              "status_warn":"909000",
              "status_error":"900000",
              "output_border":"282828",
              "output":{"<DEFAULT>":"FFFFFF",
                        "MAINTHRD":"A0FFFF",
                        "BOTLSTNR":"FFA0FF",
                        "MSGHNDLR":"FFFFA0",
                        "7ZTSKHND":"FFC85A",
                        "UCONSOLE":"A0FFA0"}}


"""
DEFS
"""


GetTickCount64=ctypes.windll.kernel32.GetTickCount64
GetTickCount64.restype=ctypes.c_uint64
GetTickCount64.argtypes=()

def Flush_Std_Buffers():
    sys.stdout.flush()
    sys.stderr.flush()
    return

def Get_Runtime_Environment():
    retval={"working_dir":"","process_binary":"","running_from_source":False,"architecture":0,"process_id":-1,"arguments":[]}

    sys_exe=sys.executable
    retval["arguments"]=sys.argv
    retval["process_binary"]=os.path.basename(sys_exe).lower()
    retval["working_dir"]=os.path.realpath(os.path.dirname(sys_exe))
    retval["process_id"]=os.getpid()
    retval["system32"]=os.path.join(os.environ["WINDIR"],u"System32")

    if ctypes.sizeof(ctypes.c_voidp)==4:
        retval["architecture"]=32
    else:
        retval["architecture"]=64

    if retval["process_binary"]==u"python.exe":
        if len(retval["arguments"])>0:
            if retval["arguments"][0].replace(u"\"",u"").lower().strip().endswith(u".py"):
                retval["working_dir"]=os.path.realpath(os.path.dirname(retval["arguments"][0]))
                retval["arguments"]=retval["arguments"][1:]
                retval["running_from_source"]=True

    return retval

def log(input_text):
    global LOGGER

    if LOGGER is not None:
        LOGGER.LOG("MAINTHRD",input_text)
    return

def Main_Wait_Loop(input_timeobject,input_waitobject,input_timesync_request_event):
    global MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS
    global MAINTHREAD_HEARTBEAT_SECONDS

    last_process_priority_check=GetTickCount64()-MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS*1000
    last_server_time_check=datetime.datetime.utcnow()

    while input_waitobject.IS_RUNNING()==True:
        time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)

        Flush_Std_Buffers()

        if GetTickCount64()-last_process_priority_check>=MAINTHREAD_IDLE_PRIORITY_CHECK_SECONDS*1000:
            try:
                if win32process.GetPriorityClass(CURRENT_PROCESS_HANDLE)!=win32process.IDLE_PRIORITY_CLASS:
                    win32process.SetPriorityClass(CURRENT_PROCESS_HANDLE,win32process.IDLE_PRIORITY_CLASS)
                    log("Idle process priority set.")
            except:
                log("Error managing process priority.")
            last_process_priority_check=GetTickCount64()

        if abs((datetime.datetime.utcnow()-last_server_time_check).total_seconds())>=SERVER_TIME_RESYNC_INTERVAL_SECONDS or input_timesync_request_event.is_set()==True:
            log("Performing time synchronization via Internet...")
            sync_result=input_timeobject.SYNC()
            if sync_result["success"]==True:
                log("Time synchronization complete. Local clock bias is "+sync_result["time_difference"]+" second(s).")
            else:
                log("Time synchronization failed.")
            if input_timesync_request_event.is_set()==True:
                input_timesync_request_event.clear()
            last_server_time_check=datetime.datetime.utcnow()

    return

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

def Bot_Token_From_String(from_string):
    retval=from_string
    try:
        retval=str(retval.strip())
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

def User_Entry_From_String(from_string):
    retval={"username":"","home":u"","allow_write":False,"error_message":""}

    segments=[]

    try:
        segments=from_string.split("|")
        for i in range(len(segments)):
            segments[i]=segments[i].strip()

        if len(segments)==1:
            raise ValueError("Home path was not present.")
        if len(segments)>2:
            raise ValueError("Wrong number of \"|\"-separated characters.")

        retval["username"]=segments[0]
        retval["home"]=segments[1].strip()
        retval["allow_write"]=False

        if retval["username"].count("#")!=2 and retval["username"].count("#")!=0:
            raise ValueError("Username contained an incorrect number of \"#\" characters.")

        username_nohashes=retval["username"].replace("#","")

        if username_nohashes=="":
            raise ValueError("Username was empty.")

        if username_nohashes[0] in "_0123456789":
            raise ValueError("Username cannot begin with a number or underscore.")

        for c in username_nohashes:
            if c.lower() not in "_0123456789abcdefghijklmnopqrstuvwxyz":
                raise ValueError("Username contains invalid characters.")

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
                raise ValueError("Home path contains invalid characters.")

        if (retval["home"].count(u"*")>1 and len(retval["home"])>1) or retval["home"].count(u":")>1 or retval["home"].startswith(u"\\")==True:
            raise ValueError("Home path contains invalid characters.")

        if u"\\.\\" in retval["home"] or u"\\..\\" in retval["home"] or retval["home"].startswith(u"\\\\")==True or len(retval["home"])>255:
            raise ValueError("Home path format is invalid.")

    except:
        return {"error_message":"User entry \""+from_string+"\" was not validly formatted: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]),"username":"","home":u"","allow_write":False}
    return retval


"""
OBJS
"""


class ShellProcess(object):
    def __init__(self,input_command):
        global PATH_WINDOWS_SYSTEM32

        result=win32process.CreateProcess(None,u"\""+PATH_WINDOWS_SYSTEM32+u"cmd.exe\" /c \""+input_command+u" \"",None,None,0,win32process.CREATE_NO_WINDOW|win32process.CREATE_UNICODE_ENVIRONMENT,None,None,win32process.STARTUPINFO())
        if result:
            self.process_handle=result[0]
            self.process_ID=result[2]
        return

    def IS_RUNNING(self): 
        exit_code=win32process.GetExitCodeProcess(self.process_handle)
        if exit_code!=win32con.STILL_ACTIVE:
            return False
        return True

    def PID(self):
        return self.process_ID

    def WAIT(self):
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS

        while self.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        return


class Logger(object):
    def __init__(self,input_log_path=u""):
        global PATH_WINDOWS_SYSTEM32

        self.logging_path=input_log_path
        self.log_handle=None
        self.log_lock=threading.Lock()
        self.output_stdout=threading.Event()
        self.output_stdout.clear()
        self.active_signaller=None
        if self.logging_path!=u"":
            ShellProcess(u"\""+PATH_WINDOWS_SYSTEM32+u"compact.exe\" /a /c \""+input_log_path+u"\"").WAIT()
        self.is_active=threading.Event()
        self.is_active.clear()
        return

    def ACTIVATE(self):
        try:
            self.log_handle=open(self.logging_path,"a")
        except:
            pass
        self.is_active.set()
        return

    def SET_STDOUT(self,input_state):
        if input_state==True:
            self.output_stdout.set()
        else:
            self.output_stdout.clear()
        return

    def DEACTIVATE(self):
        self.is_active.clear()
        try:
            if self.log_handle is not None:
                self.log_handle.close()
        except:
            pass
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

    def LOG(self,source,input_data=""):
        global UI_SIGNAL

        if self.is_active.is_set()==False:
            return

        if input_data!="":
            source_literal=str(source)
            input_literal=str(input_data)
        else:
            source_literal=""
            input_literal=str(source)
        if source!="":
            source_literal=" ["+source_literal+"] "
        else:
            source_literal=" "

        msg=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+source_literal+input_literal+"\n"

        self.log_lock.acquire()

        if self.log_handle is not None:
            try:
                self.log_handle.write(msg)
                self.log_handle.flush()
            except:
                pass

        if self.output_stdout.is_set()==True:
            try:
                sys.stdout.write(msg)
            except:
                pass

        if self.active_signaller is not None:
            try:
                self.active_signaller.send("logger_newline",msg)
            except:
                pass

        self.log_lock.release()
        return


class Time_Provider(object):
    def __init__(self):
        global WEB_REQUEST_CONNECT_TIMEOUT_SECONDS

        ssl_cert_context=ssl.create_default_context()
        ssl_cert_context.check_hostname=True
        ssl_cert_context.verify_mode=ssl.CERT_REQUIRED
        self.request_pool=urllib3.PoolManager(cert_reqs="CERT_REQUIRED",ssl_context=ssl_cert_context)
        self.request_timeout=urllib3.Timeout(connect=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS,read=WEB_REQUEST_CONNECT_TIMEOUT_SECONDS)
        self.origin_time=datetime.datetime(1970,1,1)
        self.lock_time_delta=threading.Lock()
        self.time_delta=0
        self.lock_subscribers=threading.Lock()
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

    def GET_SERVER_TIME(self):
        self.lock_time_delta.acquire()
        get_delta=self.time_delta
        self.lock_time_delta.release()
        return round(OS_Uptime_Seconds()+get_delta,3)

    def SYNC(self,input_signaller=None):
        if self.update_server_time()==True:
            get_time_diff=self.get_local_machine_time_delta_str()

            self.lock_subscribers.acquire()
            for subscriber in self.signal_subscribers:
                subscriber.send("timesync_clock_bias",get_time_diff)
            self.lock_subscribers.release()
        else:
            return {"success":False}
        return {"success":True,"time_difference":get_time_diff}

    def retrieve_current_UTC_internet_time(self):
        response=self.request_pool.request(method="GET",url="https://worldtimeapi.org/api/timezone/Etc/UTC.txt",preload_content=True,chunked=False,timeout=self.request_timeout)
        if response.status==200:
            timestr=str(response.data,"utf8")
        else:
            raise Exception("Could not get time.")
        quot1=timestr.find("\ndatetime: ")
        quot1+=len("\ndatetime: ")
        quot2=quot1+timestr[quot1+1:].find("+")
        quot2+=1
        timestr=timestr[quot1:quot2-3]
        return (datetime.datetime.strptime(timestr,"%Y-%m-%dT%H:%M:%S.%f")-self.origin_time).total_seconds()

    def update_server_time(self):
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

    def get_local_machine_time_delta_str(self):
        time_difference=round(float((datetime.datetime.utcnow()-self.origin_time).total_seconds())-self.GET_SERVER_TIME(),3)
        if time_difference>0:
            retval="+"+str(time_difference)
        else:
            retval=str(time_difference)
        return retval


class Task_Handler_7ZIP(object):
    def __init__(self,input_path_7zip,input_7zip_binary_base64,input_max_per_user,input_logger=None):
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

        input_path_7zip=input_path_7zip
        input_path_7zip=input_path_7zip.replace(u"/",u"\\")
        input_path_7zip=terminate_with_backslash(input_path_7zip)
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
                        write_7z_binary.close()
                    except:
                        pass
            raise Exception("The 7-ZIP binary could not be written. Make sure you have write permissions to the application folder.")

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
            Active_7ZIP_Handler.binary_7zip_read.close()
        except:
            pass
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
                new_process=ShellProcess(prompt_commands)
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

        self.log("7-ZIP Task Handler started.")
        last_update=GetTickCount64()-TASKS_7ZIP_UPDATE_INTERVAL_SECONDS*1000
        while self.request_exit.is_set()==False:
            time.sleep(TASKS_7ZIP_THREAD_HEARTBEAT_SECONDS)

            if GetTickCount64()-last_update>=TASKS_7ZIP_UPDATE_INTERVAL_SECONDS*1000:
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
        self.end_7zip_tasks(["*"])

        self.log("7-ZIP Task Handler has exited.")
        self.has_quit.set()
        return

    def update_7zip_tasks(self):
        self.lock_instances_7zip.acquire()

        for i in reversed(range(len(self.instances_7zip))):
            if self.instances_7zip[i]["new"]==True:
                self.instances_7zip[i]["new"]=False
                self.log("Task with PID="+str(self.instances_7zip[i]["process"].PID())+" TEMP=\""+self.instances_7zip[i]["temp_file"]+"\" has been added.")
            still_running=True
            try:
                still_running=self.instances_7zip[i]["process"].IS_RUNNING()
            except:
                pass
            if still_running==False:
                self.log("Task with PID="+str(self.instances_7zip[i]["process"].PID())+" TEMP=\""+self.instances_7zip[i]["temp_file"]+"\" has finished.")
                del self.instances_7zip[i]

        self.lock_instances_7zip.release()
        return

    def end_7zip_tasks(self,list_users,list_PIDs=[]):
        global PATH_WINDOWS_SYSTEM32
        global PENDING_ACTIVITY_HEARTBEAT_SECONDS
        global TASKS_7ZIP_DELETE_TIMEOUT_SECONDS

        taskkill_list=[]
        terminate_all=False
        terminated_total=0

        if len(list_users)==1:
            if list_users[0]=="*":
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
                self.log("Terminating ongoing 7-ZIP batch with PID="+str(get_PID)+" and temporary file \""+self.instances_7zip[i]["temp_file"].lower()+"\".")
                taskkill_list+=[{"process":ShellProcess(u"\""+PATH_WINDOWS_SYSTEM32+u"taskkill.exe\" /f /t /pid "+str(get_PID)),u"file":self.instances_7zip[i][u"temp_file"]}]
                del self.instances_7zip[i]
                terminated_total+=1

        self.lock_instances_7zip.release()

        for taskkill in taskkill_list:
            taskkill["process"].WAIT()

        for taskkill in taskkill_list:
            delete_attempt_made=False
            start_time=GetTickCount64()
            while (os.path.isfile(taskkill["file"])==True and GetTickCount64()-start_time<TASKS_7ZIP_DELETE_TIMEOUT_SECONDS*1000) or delete_attempt_made==False:
                try:
                    delete_attempt_made=True
                    os.remove(taskkill["file"])
                except:
                    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

        if terminated_total==0:
            self.log("No 7-ZIP tasks were terminated.")

        return


class Telegram_Message_Rate_Limiter(object):
    def __init__(self,input_max_messages,input_time_interval_seconds):
        self.timer_list=[]
        self.max_messages=input_max_messages
        self.time_interval_ms=input_time_interval_seconds*1000
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.lock_timerlist=threading.Lock()
        return

    def timer_list_size_and_cleanup(self):
        for i in reversed(range(len(self.timer_list))):
            if self.timer_list[i]<GetTickCount64()-self.time_interval_ms:
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
    def __init__(self,input_token):
        global WEB_REQUEST_CONNECT_TIMEOUT_SECONDS
        global TELEGRAM_API_REQUEST_TIMEOUT_SECONDS
        global TELEGRAM_API_UPLOAD_TIMEOUT_SECONDS

        ssl_cert_context=ssl.create_default_context()
        ssl_cert_context.check_hostname=True
        ssl_cert_context.verify_mode=ssl.CERT_REQUIRED
        self.request_pool=urllib3.PoolManager(cert_reqs="CERT_REQUIRED",ssl_context=ssl_cert_context)
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
            return None

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
        else:
            return {"ok":False,"result":None}

    def perform_file_request(self,input_method,input_url,input_args=None):
        if self.is_stopped.is_set()==True:
            return None

        response=None
        try:
            if input_method=="POST":
                if self.active_rate_limiter is not None:
                    self.active_rate_limiter.WAIT_FOR_CLEAR_AND_SEND()
                if self.is_stopped.is_set()==True:
                    return None
                for keyname in input_args:
                    if type(input_args[keyname])==tuple:
                        if len(input_args[keyname])==2:
                            if str(type(input_args[keyname][1]))=="<class '_io.FileIO'>":
                                input_args[keyname]=(input_args[keyname][0],input_args[keyname][1].read())
                                break
                response=self.request_pool.request(method=input_method,fields=input_args,url=input_url,preload_content=True,chunked=True,timeout=self.timeout_upload)
            else:
                response=self.request_pool.request(method=input_method,fields=input_args,url=input_url,preload_content=False,chunked=False,timeout=self.timeout_download)
        except:
            pass
        if response is not None:
            if response.status in [200,201]:
                return response

        return None

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
        if self.is_stopped.is_set()==True:
            raise Exception("Bot is stopped.")

        filename=input_file_path.replace(u"/",u"\\")
        filename=filename[filename.rfind(u"\\")+1:]
        file_handle=open(input_file_path,"rb",buffering=0)
        response=self.perform_file_request("POST",self.base_web_url+"sendDocument",{"chat_id":input_chat_id,"document":(filename,file_handle)})
        file_handle.close()
        if response is not None:
            return response

        raise Exception("Response error.")

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
            raise Exception("Bot is stopped.")

        if "/" not in input_id and "\\" not in input_id:
            try:
                input_id=self.Get_File_Info(input_id)[u"file_path"]
            except:
                raise Exception("Request error.")

        response=self.perform_file_request("GET",self.base_file_url+input_id)

        if response is not None:
            file_handle=None
            try:
                file_handle=open(input_path,"wb")
                for chunk in response.stream(TELEGRAM_API_DOWNLOAD_CHUNK_BYTES):
                    if self.is_stopped.is_set()==True:
                        file_handle.close()
                        os.remove(input_path)
                        raise Exception("Download error.")
                    file_handle.write(chunk)
                file_handle.close()
                return
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
                raise Exception("Download error.")

        raise Exception("Response error.")

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
    def __init__(self,input_token,username_list,input_timeprovider,input_signaller,input_logger=None):
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
        self.name=""
        self.messagelist_lock={}
        for username in self.listen_users:
            self.messagelist_lock[username]=threading.Lock()
        self.user_messages={}
        for username in self.listen_users:
            self.user_messages[username]=[]
        self.bot_handle=Telegram_Bot(input_token)
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
                    self.log("ERROR: The provided bot token is invalid. Startup cannot proceed.")
                    self.REQUEST_STOP()
                else:
                    if activation_fail_announce==False:
                        self.log("Bot Listener activation error. Will keep trying...")
                        activation_fail_announce=True
                    time.sleep(BOT_LISTENER_THREAD_HEARTBEAT_SECONDS)

        if self.request_exit.is_set()==False:
            self.catch_up_IDs()
            self.log("Bot Listener for \""+self.name+"\" is now active.")
            self.active_UI_signaller.send("bot_name",self.name)
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
                    self.log("Message retrieval is now online.")
                    self.active_UI_signaller.send("status","ONLINE")
                else:
                    self.log("Stopped being able to retrieve messages.")
                    self.active_UI_signaller.send("status","OFFLINE")

            self.organize_messages(response)

        self.is_ready.clear()
        self.log("Bot Listener has exited.")
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
                self.log("Caught up with messages.")
            except:
                if announced_fail==False:
                    self.log("Failed to catch up with messages. Will keep trying...")
                    announced_fail=True
                time.sleep(BOT_LISTENER_THREAD_HEARTBEAT_SECONDS)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=self.active_time_provider.GET_SERVER_TIME()
        return

    def organize_messages(self,input_msglist):
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
                    if self.active_time_provider.GET_SERVER_TIME()-msg_send_time<=BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
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
                if self.active_time_provider.GET_SERVER_TIME()-self.user_messages[message][i][u"date"]>BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
                    del self.user_messages[message][i]
            self.messagelist_lock[message].release()
        return

    def consume_user_messages(self,input_username):
        self.messagelist_lock[input_username].acquire()
        get_messages=self.user_messages[input_username][:]
        self.user_messages[input_username]=[]
        self.messagelist_lock[input_username].release()
        return get_messages


class User_Message_Handler(object):
    def __init__(self,input_token,input_root,input_user,input_write,input_blacklisted_paths,input_listener_service,input_timeprovider,input_7zip_task_handler,input_logger=None):
        global PATH_WINDOWS_SYSTEM32

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
        self.last_folder=""
        self.allow_writing=input_write
        self.listen_flag=threading.Event()
        self.listen_flag.clear()
        self.last_send_time=0
        self.account_username=input_user
        self.lastsent_timers=[]
        self.bot_lock_pass=u""
        self.allowed_root=input_root
        self.pending_lockclear=threading.Event()
        self.pending_lockclear.clear()
        self.lock_status=threading.Event()
        self.lock_status.clear()
        self.active_time_provider=input_timeprovider
        self.processing_messages=threading.Event()
        self.processing_messages.clear()
        self.bot_handle=Telegram_Bot(input_token)
        if self.allowed_root==u"*":
            self.set_last_folder(PATH_WINDOWS_SYSTEM32[0].upper()+u":\\")
        else:
            self.set_last_folder(self.allowed_root)
        if self.allowed_root!=u"*":
            self.blacklisted_paths=input_blacklisted_paths
        else:
            self.blacklisted_paths=[]
        for i in range(len(self.blacklisted_paths)):
            self.blacklisted_paths[i]=self.blacklisted_paths[i].lower()
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("MSGHNDLR","<"+self.account_username+"> "+input_text)
        return

    def sendmsg(self,sid,msg):
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
            self.bot_handle.Send_Message(sid,msg)
            self.lastsent_timers+=[self.last_send_time]
            excess_entries=max(0,len(self.lastsent_timers)-40)
            for _ in range(excess_entries):
                del self.lastsent_timers[0]
            return True
        except:
            self.log("User Message Handler was unable to respond.")
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
            retval=win32api.GetLongPathNameW(win32api.GetShortPathName(input_path))
        except:
            retval=input_path
        if len(retval)>1:
            if retval[1]==u":":
                retval=retval[0].upper()+retval[1:]
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

    def rel_to_abs(self,raw_command_args,isfile=False):
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
                self.log("User Message Handler unlocked by console.")
            else:
                self.log("User Message Handler unlock was requested, but it is not locked.")
            self.listener.consume_user_messages(self.account_username)
        return

    def work_loop(self):
        global BOT_LISTENER_THREAD_HEARTBEAT_SECONDS
        global USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS

        self.log("User Message Handler started, home path is \""+self.allowed_root+"\", allow writing: "+str(self.allow_writing).upper()+".")

        while self.request_exit.is_set()==False:
            time.sleep(USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS)
            self.check_pending_tasks()
            if self.listen_flag.is_set()==True:
                new_messages=self.listener.consume_user_messages(self.account_username)
                total_new_messages=len(new_messages)
                if total_new_messages>0:
                    self.processing_messages.set()
                    self.log(str(total_new_messages)+" new message(s) received.")
                    self.process_messages(new_messages)
                    self.processing_messages.clear()

        self.log("User Message Handler has exited.")
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
                self.log("Listen started.")
                self.listener.consume_user_messages(self.account_username)
                self.listen_flag.set()
            else:
                self.log("Listen start was requested, but it is already listening.")
        else:
            if self.listen_flag.is_set()==True:
                self.log("Listen stopped.")
                self.listen_flag.clear()
            else:
                self.log("Listen stop was requested, but it is not currently listening.")
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
            if self.active_time_provider.GET_SERVER_TIME()-m[u"date"]<=BOT_MESSAGE_RELEVANCE_TIMEOUT_SECONDS:
                if u"text" in m:
                    self.process_instructions(m[u"from"][u"id"],m[u"text"],m[u"chat"][u"id"])
                else:
                    if u"document" in m:
                        self.process_files(m[u"from"][u"id"],m[u"document"][u"file_id"],m[u"document"][u"file_name"],m[u"document"][u"file_size"])
                    elif u"audio" in m:
                        proceed=True
                        try:
                            filename=self.bot_handle.Get_File_Info(m[u"audio"][u"file_id"])[u"file_path"]
                            filename=filename[filename.rfind(u"/")+1:]
                            fileext=filename[filename.rfind(u".")+1:]
                            filetitle=""
                            fileperformer=""
                            if u"title" in m[u"audio"]:
                                filetitle=m[u"audio"][u"title"]
                            if u"performer" in m[u"audio"]:
                                fileperformer=m[u"audio"][u"performer"]
                            if filetitle!=u"" or fileperformer!=u"":
                                newname=u""
                                if fileperformer!=u"" and filetitle==u"":
                                    newname=fileperformer
                                if fileperformer!=u"" and filetitle!=u"":
                                    newname=fileperformer+u" - "+filetitle
                                if fileperformer==u"" and filetitle!=u"":
                                    newname=filetitle
                                newname+=u"."+fileext
                                newname=newname.replace(u"/",u"").replace(u"\\",u"").replace(u"?",u"").replace(u"*",u"").replace(u":",u"").replace(u"|",u"").replace(u"<",u"").replace(u">",u"")
                                filename=newname
                        except:
                            self.sendmsg(m[u"from"][u"id"],u"Could not obtain the file name.")
                            proceed=False
                        if proceed==True:
                            self.process_files(m[u"from"][u"id"],m[u"audio"][u"file_id"],filename,m[u"audio"][u"file_size"])
                    else:
                        self.sendmsg(m[u"from"][u"id"],u"Media type unsupported. Send as regular file or the file name will not carry over.")
        return

    def process_files(self,sid,fid,filename,filesize):
        global TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES

        if self.bot_lock_pass!=u"" or self.allow_writing==False:
            return

        if filesize<=TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES:
            foldername=self.get_last_folder()
            complete_put_path=foldername+filename
            self.sendmsg(sid,u"Putting file \""+filename+u"\" at \""+foldername+u"\"...")
            self.log("Receiving file \""+complete_put_path+"\"...")
            if os.path.exists(complete_put_path)==False or (os.path.exists(complete_put_path)==True and os.path.isfile(complete_put_path)==False):
                    try:
                        self.bot_handle.Get_File(fid,complete_put_path)
                        self.sendmsg(sid,u"Finished putting file \""+complete_put_path+u"\".")
                        self.log("File download complete.")
                    except:
                        self.sendmsg(sid,u"File \""+filename+u"\" could not be placed.")
                        self.log("File download aborted due to unknown issue.")
            else:
                self.sendmsg(sid,u"File \""+filename+u"\" already exists at the location.")
                self.log("File download aborted due to existing instance.")
        else:
            self.sendmsg(sid,u"File \""+filename+u"\" could not be obtained because bots are limited to file downloads of max. "+readable_size(TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES)+u".")
            self.log("File download aborted due to size exceeding limit.")
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

    def process_instructions(self,sid,msg,cid):
        global TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES
        global TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES

        if self.bot_lock_pass!=u"":
            if msg.lower().startswith(u"/unlock ")==True:
                attempted_pass=msg[len(u"/unlock "):].strip()
                attempted_pass_len=len(attempted_pass)
                if attempted_pass_len>=4 and attempted_pass_len<=32:
                    if attempted_pass==self.bot_lock_pass:
                        self.bot_lock_pass=u""
                        self.lock_status.clear()
                        self.sendmsg(sid,u"Bot unlocked.")
                        self.log(u"User Message Handler unlocked by user.")
                        return
                    else:
                        return
                else:
                    return
            else:
                return

        if msg[0]!=u"/":
            return
        cmd_end=msg.find(u" ")
        if cmd_end==-1:
            cmd_end=len(msg)
        command_type=msg[1:cmd_end].strip().lower()
        command_args=msg[cmd_end+1:].strip()
        response=u""

        if command_type==u"start":
            self.log("User has sent a start request.")

        elif command_type==u"stop":
            self.log("User has sent a stop request.")

        elif command_type==u"root":
            if self.allowed_root!=u"*":
                response=u"Root folder path is \""+self.allowed_root+u"\"."
            else:
                response=u"This user is allowed to access all host system drives."
            self.log("Root folder path requested, which is \""+self.allowed_root+"\".")

        elif command_type==u"dir":
            extra_search=u""

            if u"?f:" in command_args.lower():
                start=command_args.lower().find(u"?f:")
                end=command_args[start:].find(u" ")
                if end==-1:
                    end=len(command_args)
                else:
                    end+=start
                extra_search=command_args[start+len(u"?f:"):end]
                if command_args[:start].strip()!=u"":
                    command_args=command_args[:start].strip()
                else:
                    command_args=command_args[end:].strip()

            if u"?d" in command_args.lower():
                folders_only=True
                start=command_args.lower().find(u"?d")
                end=start+len(u"?d")
                if command_args[:start].strip()!=u"":
                    command_args=command_args[:start].strip()
                else:
                    command_args=command_args[end:].strip()
            else:
                folders_only=False

            self.log("Listing requested for path \""+command_args+"\" with search string \""+extra_search+"\", folders only="+str(folders_only).upper()+".")

            if command_args==u"":
                use_folder=self.get_last_folder()
            else:
                use_folder=command_args
            use_folder=self.rel_to_abs(command_args)
            if self.allowed_path(use_folder)==True:
                dirlist=self.folder_list_string(use_folder,extra_search,folders_only)
            else:
                dirlist=u""
                response=u"<Path is inaccessible.>"
                self.log("Folder path \""+command_args+"\" was not accessible for listing.")
            if dirlist!=u"<BAD_PATH>":
                segment_list=self.segment_file_list_string(dirlist)
                if len(segment_list)>0:
                    for segment in segment_list:
                        if self.sendmsg(sid,segment)==False:
                            response=u"<Listing interrupted.>"
                            self.log("Listing for folder path \""+command_args+"\" was interrupted.")
                            break
                        if self.request_exit.is_set()==True:
                            break
                else:
                    response=u"<Folder is empty.>"
                    self.log("Folder path \""+command_args+"\" was empty.")
                if response==u"":
                    response=u"<Listing finished.>"
            else:
                response=u"<Path is inaccessible.>"
                self.log("Folder path \""+command_args+"\" was not accessible for listing.")

        elif command_type==u"cd":
            if command_args!="":
                newpath=self.rel_to_abs(command_args)
                if self.usable_dir(newpath)==True:
                    try:
                        newpath=self.proper_caps_path(newpath)
                    except:
                        pass
                    newpath=self.proper_caps_path(terminate_with_backslash(newpath))
                    self.set_last_folder(newpath)
                    response=u"Current folder changed to \""+newpath+"\"."
                    self.log("Current folder changed to \""+newpath+"\".")
                else:
                    response=u"Path could not be accessed."
                    self.log("Path provided \""+newpath+"\" could not be accessed.")
            else:
                newpath=self.get_last_folder()
                response=u"Current folder is \""+newpath+u"\"."
                self.log("Queried current folder, which is \""+newpath+"\".")

        elif command_type==u"get":
            if command_args!=u"":
                newpath=self.rel_to_abs(command_args,True)
                if self.usable_path(newpath)==True:
                    newpath=self.proper_caps_path(newpath)
                    self.log("Requested get file \""+newpath+"\". Sending...")
                    self.sendmsg(sid,u"Getting file, please wait...")
                    try:
                        fsize=os.path.getsize(newpath)
                        if fsize<=TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES and fsize!=0:
                            self.bot_handle.Send_File(cid,newpath)
                            self.log("File \""+newpath+"\" sent.")
                        else:
                            if fsize!=0:
                                response=u"Bots cannot upload files larger than "+str(readable_size(TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES))+u" to the chat."
                                self.log("Requested file \""+newpath+"\" too large to get.")
                            else:
                                response=u"File is empty."
                                self.log("Get file \""+newpath+"\" failed because the file is empty.")
                    except:
                        response=u"Problem getting file."
                        self.log("Get File error for \""+newpath+"\".")
                else:
                    response=u"File not found or inaccessible."
                    self.log("Get file \""+newpath+"\" was not found.")
            else:
                response=u"A file name or path must be provided."
                self.log("Attempted to use get without a file name or path.")

        elif command_type==u"ren" and self.allow_writing==True:
            newname=""
            if u"?to:" in command_args.lower():
                end=command_args.lower().find(u"?to:")
                newname=command_args[end+len(u"?to:"):].strip()
                command_args=command_args[:end].strip()

            if command_args!=u"" and newname!=u"":
                newname_ok=True
                for c in newname:
                    if c in u"|<>\":\\/*?":
                        newname_ok=False
                        break
                if newname_ok==True:
                    newpath=self.rel_to_abs(command_args,True)
                    if self.usable_path(newpath)==True:
                        newpath=self.proper_caps_path(newpath)
                        end=newpath.rfind(u"\\")
                        if end!=-1:
                            foldername=terminate_with_backslash(newpath[:end])
                            self.log("Requested rename \""+newpath+"\" to \""+newname+"\".")
                            newtarget=foldername+newname
                            if os.path.exists(newtarget)==False:
                                try:
                                    os.rename(newpath,newtarget)
                                    response=u"Renamed \""+newpath+u"\" to \""+newname+u"\"."
                                    self.log("Renamed \""+newpath+"\" to \""+newname+"\".")
                                except:
                                    response=u"Problem renaming."
                                    self.log("File/folder \""+newpath+"\" rename error.")
                            else:
                                response=u"A file or folder with the new name already exists."
                                self.log("File/folder rename of \""+newpath+"\" failed because the new target \""+newtarget+"\" already exists.")
                        else:
                            response=u"Problem with path."
                            self.log("File/folder rename \""+newpath+"\" path error.")
                    else:
                        response=u"File/folder not found or inaccessible."
                        self.log("File/folder to rename \""+newpath+"\" not found.")
                else:
                    response=u"The new name must not be a path or contain invalid characters."
                    self.log("Attempted to rename \""+command_args+"\" to a new name containing invalid characters.")
            else:
                response=u"A name or path and a new name preceded by \"?to:\" must be provided."
                self.log("Attempted to rename without specifying a name or path.")

        elif command_type==u"eat" and self.allow_writing==True:
            if command_args.endswith(u" ?confirm")==True:
                command_args=command_args[:-len(u" ?confirm")].strip()
                if command_args!=u"":
                    newpath=self.rel_to_abs(command_args,True)
                    if self.usable_path(newpath)==True:
                        newpath=self.proper_caps_path(newpath)
                        self.log("Requested eat file \""+newpath+"\". Sending...")
                        self.sendmsg(sid,u"Eating file, please wait...")
                        success=False
                        try:
                            fsize=os.path.getsize(newpath)
                            if fsize<=TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES and fsize!=0:
                                self.bot_handle.Send_File(cid,newpath)
                                self.log("File \""+newpath+"\" sent.")
                                success=True
                            else:
                                if fsize!=0:
                                    response=u"Bots cannot upload files larger than "+str(readable_size(TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES))+u" to the chat."
                                    self.log("Requested file \""+newpath+"\" too large to eat.")
                                else:
                                    response=u"File is empty."
                                    self.log("Eat file \""+newpath+"\" failed because the file is empty.")
                        except:
                            response=u"Problem getting file."
                            self.log("File \""+newpath+"\" send error.")
                        if success==True:
                            try:
                                self.log("File \""+newpath+"\" sent. Deleting...")
                                os.remove(newpath)
                                response=u"File deleted."
                                self.log("File \""+newpath+"\" deleted.")
                            except:
                                response=u"Problem deleting file."
                                self.log("File delete error for \""+newpath+"\".")
                    else:
                        response=u"File not found or inaccessible."
                        self.log("File to eat at \""+newpath+"\" not found.")
                else:
                    response=u"A file name or path must be provided."
                    self.log("Attempted to eat file without specifying a name or path.")
            else:
                response=u"This command must end in \" ?confirm\"."
                self.log("Attempted to delete file without confirmation.")

        elif command_type==u"del" and self.allow_writing==True:
            if command_args.endswith(u" ?confirm")==True:
                command_args=command_args[:-len(u" ?confirm")].strip()
                if command_args!="":
                    newpath=self.rel_to_abs(command_args,True)
                    if self.usable_path(newpath)==True:
                        newpath=self.proper_caps_path(newpath)
                        self.log("Requested delete file \""+newpath+"\".")
                        try:
                            self.sendmsg(sid,"Deleting file...")
                            os.remove(newpath)
                            response=u"File deleted."
                            self.log("File \""+newpath+"\" deleted.")
                        except:
                            response=u"Problem deleting file."
                            self.log("File \""+newpath+"\" delete error.")
                    else:
                        response=u"File not found or inaccessible."
                        self.log("File to delete \""+newpath+"\" not found.")
                else:
                    response=u"A file name or path must be provided."
                    self.log("Attempted to delete file without specifying a name or path.")
            else:
                response=u"This command must end in \" ?confirm\"."
                self.log("Attempted to delete file without confirmation.")

        elif command_type==u"mkdir" and self.allow_writing==True:
            if command_args!=u"":
                newpath=self.rel_to_abs(command_args,True)
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
                            self.log("Folder created at \""+newpath+"\".")
                        except:
                            response=u"Problem creating folder."
                            self.log("Folder create error at \""+newpath+"\".")
                    else:
                        response=u"Folder already exists."
                        self.log("Attempted to create already existing folder at \""+newpath+"\".")
                else:
                    response=u"Path is not usable."
                    self.log("Attempted to create folder at unusable path \""+newpath+"\".")
            else:
                response=u"A folder name or path must be provided."
                self.log("Attempted to create folder without specifying a name or path.")

        elif command_type==u"rmdir" and self.allow_writing==True:
            if command_args.endswith(u" ?confirm")==True:
                command_args=command_args[:-len(u" ?confirm")].strip()
                if command_args!=u"":
                    newpath=self.rel_to_abs(command_args,True)
                    if self.usable_dir(newpath)==True:
                        upper_folder=newpath
                        if upper_folder.endswith(u"\\")==True:
                            upper_folder=upper_folder[:-1]
                        if upper_folder.count(u"\\")>0:
                            upper_folder=upper_folder[:upper_folder.rfind(u"\\")+1]
                        if self.usable_dir(upper_folder)==True:
                            newpath=self.proper_caps_path(newpath)
                            self.log("Requested delete folder \""+newpath+"\".")
                            try:
                                self.sendmsg(sid,u"Deleting folder...")
                                shutil.rmtree(newpath)
                                moved_up=u""
                                newpath=terminate_with_backslash(newpath)
                                if self.get_last_folder().lower().endswith(newpath.lower())==True:
                                    self.set_last_folder(upper_folder)
                                    moved_up=u" Current folder is now \""+self.proper_caps_path(upper_folder)+u"\"."
                                response=u"Folder deleted."+moved_up
                                self.log("Folder deleted at \""+newpath+"\"."+moved_up)
                            except:
                                response=u"Problem deleting folder."
                                self.log("Folder delete error at \""+newpath+"\".")
                        else:
                            response=u"No upper folder to switch to after removal."
                            self.log("Attempted to delete \""+newpath+"\" at top folder.")
                    else:
                        response=u"Folder \""+newpath+u"\" not found or inaccessible."
                        self.log("Folder to delete not found at \""+newpath+"\".")
                else:
                    response=u"A folder name or path must be provided."
                    self.log("No folder name or path provided for deletion.")
            else:
                response=u"This command must end in \" ?confirm\"."
                self.log("Attempted to delete folder without confirmation.")

        elif command_type==u"up":
            if self.last_folder.count(u"\\")>1:
                newpath=self.get_last_folder()
                newpath=newpath[:-1]
                newpath=newpath[:newpath.rfind(u"\\")+1]
                if self.allowed_path(newpath)==True:
                    self.set_last_folder(newpath)
                    response=u"Current folder is now \""+newpath+u"\"."
                    self.log("Current folder changed to \""+newpath+"\".")
                else:
                    response=u"Already at top folder."
                    self.log("Attempted to go up while at top folder.")
            else:
                response=u"Already at top folder."
                self.log("Attempted to go up while at top folder.")

        elif command_type==u"zip" and self.allow_writing==True:
            if command_args!=u"":
                newpath=self.rel_to_abs(command_args)
                if os.path.exists(newpath)==False and newpath.endswith(u"\\")==True:
                    newpath=newpath[:-1]
                if self.usable_path(newpath)==True:
                    zip_response=self.active_7zip_task_handler.NEW_TASK(newpath,self.account_username)
                    if zip_response["result"]=="CREATED":
                        response=u"Issued zip command."
                        self.log("Zip command launched on \""+zip_response["full_target"]+"\".")
                    elif zip_response["result"]=="EXISTS":
                        response=u"An archive \""+zip_response["full_target"]+u".7z\" already exists."
                        self.log("Zip \""+command_args+"\" failed because target archive \""+zip_response["full_target"]+".7z\" already exists.")
                    elif zip_response["result"]=="ERROR":
                        response=u"Problem running command."
                        self.log("Zip \""+command_args+"\" command could not be run.")
                    elif zip_response["result"]=="MAXREACHED":
                        response=u"Maximum concurrent archival tasks reached."
                        self.log("Zip \""+command_args+"\" rejected due to max concurrent tasks per user limit.")
                else:
                    response=u"File not found or inaccessible."
                    self.log("Zip \""+command_args+"\" file not found or inaccessible.")
            else:
                response=u"A file or folder name or path must be provided."
                self.log("Attempted to zip without a name or path.")

        elif command_type==u"listzips" and self.allow_writing==True:
            response=u""
            tasks_7zip=self.active_7zip_task_handler.GET_TASKS()

            for taskdata in tasks_7zip:
                if taskdata["user"]==self.account_username:
                    response+=u">ARCHIVING \""+self.proper_caps_path(taskdata["target"])+u"\"\n"

            if response==u"":
                response=u"No archival tasks running."
            else:
                response=u"Ongoing archival tasks:\n\n"+response

            self.log("Requested list of running 7-ZIP archival tasks for user.")

        elif command_type==u"stopzips" and self.allow_writing==True:
            response=u"All running archival tasks will be stopped."
            self.active_7zip_task_handler.END_TASKS([self.account_username])
            self.log("Requested stop of any running 7-ZIP archival tasks.")

        elif command_type==u"lock":
            cmdlen=len(command_args)
            if cmdlen>=4 and cmdlen<=32:
                self.bot_lock_pass=command_args
                response=u"Bot locked."
                self.lock_status.set()
                self.log("User Message Handler was locked with a password.")
            else:
                response=u"Lock password must be between 4 and 32 characters long."
                self.log("Attempted to lock the bot with a password of invalid length.")

        elif command_type==u"unlock":
            response=u"The bot is already unlocked."

        elif command_type==u"help":
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
            response+=u"/lock <PASSWORD>: lock the bot from responding to messages\n"
            response+=u"/unlock <PASSWORD>: unlock the bot\n"
            response+=u"\nSlashes work both ways in paths (/cd c:/windows, /cd c:\windows)\n\n"
            response+=u"File size limit for getting files from host system: "+readable_size(TELEGRAM_API_MAX_UPLOAD_ALLOWED_FILESIZE_BYTES)+u"."
            if self.allow_writing==True:
                response+=u"\nFile size limit for putting files on host system: "+readable_size(TELEGRAM_API_MAX_DOWNLOAD_ALLOWED_FILESIZE_BYTES)+u".\n"
                response+=u"\nNOTE: All commands that delete files or folders must end with \" ?confirm\"."
            self.log(u"Help requested.")
        else:
            response=u"Unrecognized command. Type \"/help\" for a list of commands."

        if response!=u"":
            self.sendmsg(sid,response)
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
        self.lock_command=threading.Lock()
        self.request_time_sync=input_time_sync
        self.active_7zip_task_handler=input_7zip_taskhandler
        self.pending_command=""
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

    def COMMAND_SEND(self,input_command):
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            self.pending_command=input_command
            self.lock_command.release()
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

    def process_command(self,user_input):
        user_data=user_input.split(" ")
        input_command=user_data[0].lower().strip()
        input_arguments=[]
        if len(user_data)>1:
            for i in range(1,len(user_data)):
                new_arg=user_data[i].lower().strip()
                if new_arg!="":
                    input_arguments+=[new_arg]

        if input_command=="startlisten":
            has_acted=False
            for user_handler_instance in self.user_handler_list:
                if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                    user_handler_instance.LISTEN(True)
                    has_acted=True
            if has_acted==False:
                self.log("No matching users were found.")
            return True

        elif input_command=="stoplisten":
            has_acted=False
            for user_handler_instance in self.user_handler_list:
                if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                    user_handler_instance.LISTEN(False)
                    has_acted=True
            if has_acted==False:
                self.log("No matching users were found.")
            return True

        elif input_command=="userstats":
            stats_out=""
            for user_handler_instance in self.user_handler_list:
                if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                    stats_out+="\nMessage handler for user \""+user_handler_instance.account_username+"\":\n"+\
                             "Home path=\""+user_handler_instance.allowed_root+"\"\n"+\
                             "Write mode: "+str(user_handler_instance.allow_writing).upper()+"\n"+\
                             "Current folder=\""+user_handler_instance.get_last_folder()+"\"\n"+\
                             "Locked: "+str(user_handler_instance.lock_status.is_set()).upper()+"\n"+\
                             "Listening: "+str(user_handler_instance.listen_flag.is_set()).upper()+"\n"
            if stats_out!="":
                stats_out="USER STATS:\n"+stats_out
                self.log(stats_out)
            else:
                self.log("No matching users were found.")
            return True

        elif input_command=="listusers":
            list_out=""
            for user_handler_instance in self.user_handler_list:
                list_out+=user_handler_instance.account_username+", "
            list_out=list_out[:-2]+"."
            self.log("Allowed user(s): "+list_out)
            return True

        elif input_command=="unlockusers":
            has_acted=False
            for user_handler_instance in self.user_handler_list:
                if user_handler_instance.account_username.lower() in input_arguments or input_arguments==[]:
                    user_handler_instance.UNLOCK()
                    has_acted=True
            if has_acted==False:
                self.log("No matching users were found.")
            return True

        elif input_command=="synctime":
            if self.request_time_sync.is_set()==False:
                self.log("Manual Internet time synchronization requested...")
                self.request_time_sync.set()
            else:
                self.log("Manual Internet time synchronization is already in progress.")
            return True

        elif input_command=="listzips":
            tasklist=self.active_7zip_task_handler.GET_TASKS()
            user_task_dict={}
            for entry in tasklist:
                if entry["user"] not in user_task_dict.keys():
                    user_task_dict[entry["user"]]=[]
                user_task_dict[entry["user"]]+=[{"target":entry["target"],"pid":entry["pid"]}]
            task_data_out=""
            for username in user_task_dict:
                if username.lower() in input_arguments or input_arguments==[]:
                    task_data_out+="USER \""+username+"\":\n"
                    for entry in user_task_dict[username]:
                        task_data_out+=">TARGET: \""+entry["target"]+"\" BATCH PID: "+str(entry["pid"])+"\n"
                    task_data_out+="\n"
            if task_data_out=="":
                self.log("Found no 7-ZIP tasks running.")
            else:
                if task_data_out.endswith("\n")==True:
                    task_data_out=task_data_out[:-1]
                task_data_out="RUNNING 7-ZIP ARCHIVAL TASK(S):\n"+task_data_out
                self.log(task_data_out)
            return True
                
        elif input_command=="stopzips":
            usernames=[]
            pids=[]

            for arg in input_arguments:
                arg=arg.strip()
                if arg!="":
                    new_pid=-1
                    new_username=""

                    try:
                        new_pid=int(arg)
                        if new_pid<=4 or new_pid>2**32:
                            new_pid=-1
                    except:
                        invalid=False
                        if len(arg)>=5 and len(arg)<=32:
                            if arg[0] in "0123456789_":
                                invalid=True
                            else:
                                for c in arg:
                                    if c.lower() not in "0123456789_abcdefghijklmnopqrstuvwxyz#":
                                        invalid=True
                                        break
                        else:
                            invalid=True

                        if invalid==False:
                            new_username=arg

                    if new_username!="":
                        usernames+=[new_username]
                    elif new_pid!=-1:
                        pids+=[new_pid]
                    else:
                        self.log("One or more PIDs or users were incorrect.")
                        return False

            if len(pids)+len(usernames)>0:
                self.active_7zip_task_handler.END_TASKS(usernames,pids)
            else:
                self.active_7zip_task_handler.END_TASKS(["*"])
            return True

        elif input_command=="help":
            self.log("AVAILABLE CONSOLE COMMANDS:\n"+\
            "listusers: lists all allowed users\n"+\
            "startlisten [USERS]: start listening to messages for listed users; leave blank to apply to all instances\n"+\
            "stoplisten [USERS]: stop listening to messages for listed users; leave blank to apply to all instances\n"+\
            "unlockusers [USERS]: unlock the bot for listed users; leave blank to apply to all instances\n"+\
            "userstats [USERS]: list stats for listed users; leave blank to list all instances\n"+\
            "listzips [USERS]: list running 7-ZIP archival tasks for listed users; leave blank to list all instances\n"+\
            "stopzips [PID | USERS]: stop running 7-ZIP archival tasks by listed userss or PID; leave blank to apply to all instances\n"+\
            "synctime: manually re-synchronize bot time with Internet time\n"+\
            "help: display help\n"+\
            "exit: close the program\n")
            return True

        else:
            self.log("Unrecognized command. Type \"help\" for a list of commands.")
            return False

    def retrieve_command(self):
        retval=""
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            retval=self.pending_command
            self.pending_command=""
            self.lock_command.release()
        return retval

    def work_loop(self):
        global COMMAND_CHECK_INTERVAL_SECONDS
        global COMMAND_HISTORY_MAX

        self.log("Starting User Message Handler(s)...")
        for user_handler_instance in self.user_handler_list:
            user_handler_instance.ATTACH_MESSAGE_RATE_LIMITER(self.message_rate_limiter)
            user_handler_instance.START()
            user_handler_instance.LISTEN(True)

        self.log("User Console activated.\nType \"help\" in the console for available commands.\nUse the up and down arrows to scroll through previous successful commands(max. "+str(COMMAND_HISTORY_MAX)+" history).")
        self.active_UI_signaller.send("attach_console",self)

        if self.user_handlers_running()==0:
            self.is_exiting.set()

        continue_processing=True
        last_busy_state=False

        while continue_processing==True:
            time.sleep(COMMAND_CHECK_INTERVAL_SECONDS)
            if last_busy_state!=self.any_user_handlers_busy():
                last_busy_state=not last_busy_state
                UI_SIGNAL.send("bots_busy",last_busy_state)

            command=self.retrieve_command()

            if command!="":
                result=False

                if command.lower()=="exit":
                    self.log("Exit requested. Closing...")
                    self.REQUEST_STOP()
                else:
                    result=self.process_command(command)

                if result==True:
                    UI_SIGNAL.send("commandfield_accepted",{})

            if self.request_exit.is_set()==True:
                self.is_exiting.set()

            if self.is_exiting.is_set()==False:
                if command!="":
                    self.active_UI_signaller.send("commandfield_failed",{})
            else:
                continue_processing=False

                self.log("Requesting stop to Message Handler(s)...")
                for user_handler_instance in self.user_handler_list:
                    user_handler_instance.REQUEST_STOP()

                for user_handler_instance in self.user_handler_list:
                    user_handler_instance.CONCLUDE()
                self.log("Confirmed User Message Handler(s) exit.")

        self.log("User Console exiting...")
        self.active_UI_signaller.send("detach_console",{})
        self.active_UI_signaller.send("close",{})
        self.has_quit.set()
        return


class UI(object):
    def __init__(self,input_colorscheme,input_icons_b64,input_signaller,input_minimized,input_logger=None):
        self.colorscheme=json.loads(json.dumps(input_colorscheme))
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
        self.working_thread=threading.Thread(target=self.UI_thread_launcher)
        self.working_thread.daemon=True
        self.working_thread.start()
        return

    def __del__(self):
        qInstallMessageHandler(None)
        return

    @staticmethod
    def qtmsg_handler(msg_type,msg_log_context,msg_string):
        global QTMSG_BLACKLIST_STARTSWITH

        for entry in QTMSG_BLACKLIST_STARTSWITH:
            if msg_string.startswith(entry):
                return

        sys.stderr.write(msg_string+"\n")
        return

    def UI_thread_launcher(self):
        self.UI_app=QApplication([])
        self.UI_app.setStyle("fusion")
        self.UI_window=Main_Window(self.colorscheme,self.icons_b64,self.is_ready,self.is_exiting,self.has_quit,self.UI_signaller,self.start_minimized,self.active_logger)
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

    def send(self,input_type,input_data={}):
        output_signal_info={"type":input_type,"data":input_data}
        self.active_signal.emit(output_signal_info)
        return


"""
WINS
"""


class Main_Window(QMainWindow):
    def __init__(self,input_colorscheme,input_icons_b64,input_is_ready,input_is_exiting,input_has_quit,input_signaller,start_minimized,input_logger=None):
        global __author__
        global __version__
        global FONTS
        global CUSTOM_UI_SCALING

        super(Main_Window,self).__init__(None)

        self.active_logger=input_logger
        self.is_exiting=input_is_exiting
        self.has_quit=input_has_quit

        UI_SCALE=self.logicalDpiX()/96.0
        UI_SCALE*=CUSTOM_UI_SCALING
        self.font_cache={}
        for fontname in FONTS:
            self.font_cache[fontname]=QFont(FONTS[fontname]["type"])
            self.font_cache[fontname].setPointSize(FONT_POINT_SIZE*FONTS[fontname]["scale"]*CUSTOM_UI_SCALING)
            for fontproperty in FONTS[fontname]["properties"]:
                if fontproperty=="bold":
                    self.font_cache[fontname].setBold(True)
                if fontproperty=="italic":
                    self.font_cache[fontname].setItalic(True)
                if fontproperty=="underline":
                    self.font_cache[fontname].setUnderline(True)
                if fontproperty=="strikeout":
                    self.font_cache[fontname].setStrikeOut(True)

        self.setFixedSize(940*UI_SCALE,598*UI_SCALE)
        self.setWindowTitle("FileBot   v"+str(__version__)+"   by "+str(__author__))
        self.setWindowFlags(self.windowFlags()|Qt.MSWindowsFixedSizeDialogHint)

        self.lock_log_queue=threading.Lock()
        self.lock_output_update=threading.Lock()
        self.lock_clipboard=threading.Lock()
        self.active_clipboard=QApplication.clipboard()
        self.UI_signaller=input_signaller
        self.UI_signaller.active_signal.connect(self.signal_response_handler)

        self.is_minimized=False
        self.disable_hide=False
        self.command_history=[]
        self.output_queue=[]
        self.UI_lockstate=False
        self.last_bots_busy_state=False
        self.online_state=False
        self.command_history_index=-1
        self.console=None
        self.update_log_on_restore=False
        self.clipboard_queue=""
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
        self.tray_current_text="FileBot"
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
        self.options_macros["restore"]=self.tray_menu.addAction("Restore")
        self.options_macros["restore"].triggered.connect(self.traymenu_restore_onselect)
        self.options_macros["restore"].setFont(self.font_cache["general"])
        self.tray_menu.addSeparator()
        self.options_macros["exit"]=self.tray_menu.addAction("Exit")
        self.options_macros["exit"].triggered.connect(self.traymenu_exit_onselect)
        self.options_macros["exit"].setFont(self.font_cache["general"])
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.tray_onactivate)

        self.options_macros["restore"].setVisible(False)

        self.label_botname=QGroupBox(self)
        self.label_botname.setGeometry(-10*UI_SCALE,-100*UI_SCALE,self.width()+10*UI_SCALE,self.height()+100*UI_SCALE)
        self.label_botname.setStyleSheet("QGroupBox {"+window_colors+"}")

        self.label_botname=QLabel(self)
        self.label_botname.setText("Bot name:")
        self.label_botname.setGeometry(12*UI_SCALE,6*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botname.setFont(self.font_cache["general"])
        self.label_botname.setAlignment(Qt.AlignLeft)
        self.label_botname.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botname_value=QLabel(self)
        self.label_botname_value.setGeometry(65*UI_SCALE,6*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botname_value.setFont(self.font_cache["status"])
        self.label_botname_value.setText("<not retrieved>")
        self.label_botname_value.setAlignment(Qt.AlignLeft)
        self.label_botname_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botstatus=QLabel(self)
        self.label_botstatus.setText("Status:")
        self.label_botstatus.setGeometry(384*UI_SCALE,6*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botstatus.setFont(self.font_cache["general"])
        self.label_botstatus.setAlignment(Qt.AlignLeft)
        self.label_botstatus.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_botstatus_value=QLabel(self)
        self.label_botstatus_value.setGeometry(422*UI_SCALE,6*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botstatus_value.setFont(self.font_cache["status"])
        self.label_botstatus_value.setText("NOT STARTED")
        self.label_botstatus_value.setAlignment(Qt.AlignLeft)
        self.label_botstatus_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_clock_bias=QLabel(self)
        self.label_clock_bias.setText("Local machine clock bias(seconds):")
        self.label_clock_bias.setGeometry(625*UI_SCALE,6*UI_SCALE,300*UI_SCALE,26*UI_SCALE)
        self.label_clock_bias.setFont(self.font_cache["general"])
        self.label_clock_bias.setAlignment(Qt.AlignLeft)
        self.label_clock_bias.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.label_clock_bias_value=QLabel(self)
        self.label_clock_bias_value.setGeometry(796*UI_SCALE,6*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_clock_bias_value.setFont(self.font_cache["status"])
        self.label_clock_bias_value.setText("UNKNOWN")
        self.label_clock_bias_value.setAlignment(Qt.AlignLeft)
        self.label_clock_bias_value.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.textbox_output_model=QStandardItemModel(self)
        self.textbox_output=QListView(self)
        self.textbox_output.setModel(self.textbox_output_model)
        self.textbox_output.setFont(self.font_cache["log"])
        self.textbox_output.setGeometry(9*UI_SCALE,24*UI_SCALE,922*UI_SCALE,524*UI_SCALE)
        self.textbox_output.setStyleSheet("QListView::item:selected {border-top:"+str(int(1*UI_SCALE))+"px solid #"+colors_output_border+"; color:#"+colors_selection_text+"; background-color:#"+colors_selection_background+";} QListView::item {border-top:"+str(int(1*UI_SCALE))+"px solid #"+colors_output_border+";} QListView::enabled {background-color:#"+colors_background_IO+"; "+selection_colors+"} QListView::disabled {background-color:#"+colors_background_IO_disabled+"; "+selection_colors+"}")
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
        self.textbox_output.verticalScrollBar().setStyleSheet("QScrollBar:vertical {border:"+str(int(1*UI_SCALE))+"px solid #"+colors_scrollbar_background+"; color:#"+colors_scrollbar_text+"; background-color:#"+colors_scrollbar_background+"; width:"+str(int(15*UI_SCALE))+"px;} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {color:#"+colors_scrollbar_text+"; background-color:#"+colors_scrollarea_background+"}")
        self.textbox_output.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.textbox_output.installEventFilter(self)

        self.label_commands=QLabel(self)
        self.label_commands.setText("INPUT COMMANDS:")
        self.label_commands.setGeometry(410*UI_SCALE,552*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_commands.setFont(self.font_cache["general"])
        self.label_commands.setAlignment(Qt.AlignLeft)
        self.label_commands.setStyleSheet("QLabel {color:#"+colors_window_text+"}")

        self.input_commandfield=QLineEdit(self)
        self.input_commandfield.setGeometry(9*UI_SCALE,566*UI_SCALE,922*UI_SCALE,22*UI_SCALE)
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
        self.is_minimized=True
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
        self.clipboard_queue=""
        self.lock_clipboard.release()
        return

    def queue_clipboard_insert(self,input_text):
        if input_text=="":
            return

        self.lock_clipboard.acquire()
        self.clipboard_queue=input_text
        self.lock_clipboard.release()
        self.timer_clipboard.start(0)
        return

    def queue_close(self):
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
                                self.input_commandfield.setText("")
                        return True

        elif widget==self.textbox_output:
            if event.type()==QEvent.KeyPress:
                key_pressed=event.key()
                if key_pressed==Qt.Key_Escape:
                    rows=self.textbox_output.selectionModel().clearSelection()
                elif key_pressed==Qt.Key_C:
                    if event.modifiers()&Qt.ControlModifier:
                        if (GetTickCount64()-self.last_clipboard_selection_time)/1000.0>UI_CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS:
                            self.last_clipboard_selection_time=GetTickCount64()
                            rows=self.textbox_output.selectionModel().selectedRows()
                            if len(rows)>0:
                                clipboard_data=""
                                cache_model=self.textbox_output.model()
                                for row in rows:
                                    clipboard_data+=cache_model.itemData(row)[0]+"\n"
                                self.queue_clipboard_insert(clipboard_data)
                        return True

        return QWidget.eventFilter(self,widget,event)

    def queue_log_update(self):
        global UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS

        if self.log_is_updating==False:
            self.log_is_updating=True
            extra_timer=max(self.last_log_update_duration-GetTickCount64()+self.last_log_update_time,0)*1.1
            self.timer_update_output.start(max(0,self.last_log_update_time+UI_LOG_UPDATE_INTERVAL_MINIMUM_SECONDS*1000.0+extra_timer-GetTickCount64()))
        return

    def update_output(self):
        global OUTPUT_ENTRIES_MAX

        if self.is_exiting.is_set()==True:
            return

        self.lock_log_queue.acquire()
        self.last_log_update_duration=GetTickCount64()
        get_output_queue=self.output_queue[:]
        self.output_queue=[]
        self.lock_log_queue.release()
        get_output_queue_len=len(get_output_queue)

        self.lock_output_update.acquire()

        rows_to_delete=max(0,self.textbox_output_model.rowCount()+get_output_queue_len-OUTPUT_ENTRIES_MAX)
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

        tray_text_new="FileBot v"+str(__version__)+"\nBot name: "
        if self.label_botname_value.text()!="<not retrieved>":
            tray_text_new+="\""+self.label_botname_value.text()+"\"\nStatus: "
        else:
            tray_text_new+="<not retrieved>\n"

        tray_candidate="default"
        if self.online_state==True:
            if self.last_bots_busy_state==True:
                tray_candidate="busy"
        else:
            tray_candidate="deactivated"

        if tray_candidate=="default":
            tray_text_new+="ONLINE"
        elif tray_candidate=="deactivated":
            tray_text_new+="OFFLINE"
        elif tray_candidate=="busy":
            tray_text_new+="ONLINE (processing messages)"

        if self.tray_current_text!=tray_text_new:
            self.tray_current_text=tray_text_new
            self.tray_icon.setToolTip(self.tray_current_text)

        if self.tray_current_state!=tray_candidate:
            self.tray_current_state=tray_candidate
            self.tray_icon.setIcon(self.icon_cache[self.tray_current_state])
        return

    def add_to_output_queue(self,input_line):
        global OUTPUT_ENTRIES_MAX

        if input_line.endswith("\n"):
            input_line=input_line[:-1]
        text_source=""
        if len(input_line)>=29:
            if input_line[20]=="[" and input_line[29]=="]":
                text_source=input_line[21:29]
        if text_source in self.output_colors:
            text_color=self.output_colors[text_source]
        else:
            text_color=self.output_colors["<DEFAULT>"]
        self.lock_log_queue.acquire()
        self.output_queue+=[(input_line,text_color)]
        if len(self.output_queue)>OUTPUT_ENTRIES_MAX:
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
        clean_text=str(self.input_commandfield.text().strip())
        self.input_commandfield.setText(clean_text)
        if clean_text=="":
            return
        self.send_console_command(clean_text)
        return

    def send_console_command(self,input_command):
        if self.console is None:
            return
        self.input_commandfield.setEnabled(False)
        self.console.COMMAND_SEND(input_command)
        return

    def set_UI_lock(self,new_state):
        if new_state!=self.UI_lockstate:
            self.UI_lockstate=new_state
            do_console_disable=self.UI_lockstate or self.console is None
            self.lock_output_update.acquire()
            self.textbox_output.setDisabled(self.UI_lockstate)
            self.lock_output_update.release()
            self.input_commandfield.setDisabled(do_console_disable)
            if do_console_disable==False:
                self.input_commandfield.setFocus()
        return

    def update_UI_usability(self):
        usable=self.console is not None
        self.set_UI_lock(not usable)
        return

    def signal_response_handler(self,event):
        global COMMAND_HISTORY_MAX

        if self.is_exiting.is_set()==True:
            return

        event_type=event["type"]
        event_data=event["data"]

        if event["type"]=="logger_newline":
            self.add_output_line(event_data)

        elif event_type=="attach_console":
            self.console=event_data
            self.input_commandfield.setEnabled(not self.UI_lockstate)
            self.update_UI_usability()

        elif event_type=="detach_console":
            self.console=None
            self.input_commandfield.setEnabled(False)
            self.update_UI_usability()

        elif event_type=="close":
            self.queue_close()

        elif event_type=="bots_busy":
            if self.last_bots_busy_state!=event_data:
                self.last_bots_busy_state=not self.last_bots_busy_state
                self.update_tray_icon()

        elif event_type=="bot_name":
            self.label_botname_value.setText(event_data)
            self.label_botname_value.setStyleSheet("QLabel {color: #"+self.colors_status_username+"}")
            self.update_tray_icon()

        elif event_type=="status":
            self.label_botstatus_value.setText(event_data)
            if event_data=="ONLINE":
                self.label_botstatus_value.setStyleSheet("QLabel {color: #"+self.colors_status_ok+"}")
                self.online_state=True
                self.update_tray_icon()
            elif event_data=="OFFLINE":
                self.label_botstatus_value.setStyleSheet("QLabel {color: #"+self.colors_status_error+"}")
                self.online_state=False
                self.update_tray_icon()

        elif event_type=="timesync_clock_bias":
            self.label_clock_bias_value.setText(event_data)
            get_number=float(event_data.replace("+","").replace("-",""))
            self.label_clock_bias_value.setStyleSheet("QLabel {color: #"+self.colors_status_ok+"}")
            if get_number>=30:
                self.label_clock_bias_value.setStyleSheet("QLabel {color: #"+self.colors_status_warn+"}")
            if get_number>=60:
                self.label_clock_bias_value.setStyleSheet("QLabel {color: #"+self.colors_status_error+"}")

        elif event_type=="commandfield_failed":
            if self.console is not None:
                do_enable=not self.UI_lockstate
                self.input_commandfield.setEnabled(do_enable)
                if do_enable==True:
                    self.input_commandfield.selectAll()
                    self.input_commandfield.setFocus()

        elif event_type=="commandfield_accepted":
            self.command_history+=[self.input_commandfield.text()]
            if len(self.command_history)>COMMAND_HISTORY_MAX:
                del self.command_history[0]
            self.command_history_index=len(self.command_history)
            self.input_commandfield.setText("")
            self.input_commandfield.setFocus()

        elif event_type=="close_standby":
            self.textbox_output.setEnabled(True)
            self.input_commandfield.setEnabled(False)

        return

    def hideEvent(self,event):
        if self.disable_hide==True:
            event.ignore()
            event.setAccepted(False)
        return

    def changeEvent(self,event):
        if event.type()==QEvent.WindowStateChange:
            getwinstate=self.windowState()
            if getwinstate==Qt.WindowMinimized:
                self.options_macros["restore"].setVisible(True)
                self.is_minimized=True
                self.hide()
            elif getwinstate==Qt.WindowNoState:
                self.options_macros["restore"].setVisible(False)
                self.is_minimized=False
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

        self.log("UI closing...")

        self.is_exiting.set()

        self.tray_icon.setVisible(False)
        self.tray_icon.hide()
        del self.tray_icon

        self.has_quit.set()
        return


"""
MAIN
"""


environment_info=Get_Runtime_Environment()
PATH_WINDOWS_SYSTEM32=terminate_with_backslash(environment_info["system32"])

start_minimized=False
stdout_output=False
for argument in environment_info["arguments"]:
    argument=argument.lower().strip()

    if argument==u"/minimized":
        start_minimized=True
    elif argument==u"/stdout":
        stdout_output=True

if environment_info["running_from_source"]==True:
    stdout_output=True

LOGGER=Logger(os.path.join(environment_info["working_dir"],u"log.txt"))
LOGGER.SET_STDOUT(stdout_output)
LOGGER.ACTIVATE()

CURRENT_PROCESS_HANDLE=ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS,True,environment_info["process_id"])

UI_SIGNAL=UI_Signaller()
LOGGER.ATTACH_SIGNALLER(UI_SIGNAL)
Active_UI=UI(COLOR_SCHEME,APP_ICONS_B64,UI_SIGNAL,start_minimized,LOGGER)
del APP_ICONS_B64
APP_ICONS_B64=None

while Active_UI.IS_READY()==False:
    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

log("==================================== FileBot ====================================")
log("Author: "+str(__author__))
log("Version: "+str(__version__))
log("=================================================================================")
log("7-ZIP (C) Igor Pavlov; distributed under GNU LGPL license; https://www.7-zip.org/\n")
log("\n\nREQUIREMENTS:\n"+\
    "-bot token in \"token.txt\"\n"+\
    "-users list in \"userlist.txt\" with one entry per line, formatted as such: <USERNAME>|<HOME PATH>\n"+\
    "Begin home path with \">\" to allow writing. To allow access to all drives, set the path to \"*\".\n"+\
    "If a user has no username, you can add them via first name and last name with a \"#\" before each. EXAMPLE:\n"+\
    "FIRST NAME: John LAST NAME: Doe -> #John#Doe\n"+\
    "Note that this method only works if the user has no username, and that a \"#\" is required even if the last name is empty.\n"+\
    "Note that users without \"*\" home path will be disallowed from accessing FileBot's running folder even if it's a valid subfolder.\n\n"+\
    "EXAMPLE ENTRIES:\n"+\
    "JohnDoe|C:\\MySharedFiles\n"+\
    "TrustedUser|>*\n\n"+\
    "A maximum of "+str(MAX_BOT_USERS)+" users are supported.\n\n"+\
    "COMMAND LINE:\n"+\
    "/minimized: starts the application minimized to system tray\n"+\
    "/stdout: output log to stdout in addition to window\n")

log("Process ID is "+str(environment_info["process_id"])+". FileBot architecture is "+str(environment_info["architecture"])+"-bit.")

fatal_error=False
collect_bot_token=""
collect_user_file_entries=[]
collect_allowed_users=[]

try:
    file_handle=open(os.path.join(environment_info["working_dir"],u"token.txt"),"r")
    collect_bot_token=file_handle.read(128)
    file_handle.close()
except:
    log("ERROR: Make sure the file \"token.txt\" exists and contains the bot token.")
    fatal_error=True

if fatal_error==False:
    collect_bot_token=Bot_Token_From_String(collect_bot_token)
    if collect_bot_token=="":
        log("ERROR: Make sure the token is correctly written in \"token.txt\".")
        fatal_error=True

if fatal_error==False:
    file_handle=None
    try:
        file_handle=open(os.path.join(environment_info["working_dir"],u"userlist.txt"),"r")
        all_lines=file_handle.readlines(384*MAX_BOT_USERS)
        for line in all_lines:
            line=line.strip()
            if line!=u"":
                collect_user_file_entries+=[line]
        file_handle.close()
    except:
        if file_handle is not None:
            try:
                file_handle.close()
            except:
                pass
        log("ERROR: Could not obtain any valid user entries from \"userlist.txt\".")
        fatal_error=True

if fatal_error==False:
    for entry in collect_user_file_entries:
        new_user=User_Entry_From_String(entry)
        if new_user["error_message"]=="":
            collect_allowed_users+=[new_user]
            if len(collect_allowed_users)==MAX_BOT_USERS:
                break
        else:
            log("WARNING: "+new_user["error_message"])

    collect_user_file_entries=[]
    if len(collect_allowed_users)>0:
        log("Number of users to listen for: "+str(len(collect_allowed_users))+".")
    else:
        log("ERROR: There were no valid user entries to add.")
        fatal_error=True

if fatal_error==False:
    try:
        Active_7ZIP_Handler=Task_Handler_7ZIP(environment_info["working_dir"],Get_B64_Resource("binaries/7zipx"+str(environment_info["architecture"])),MAX_7ZIP_TASKS_PER_USER,LOGGER)
    except:
        log("The 7-ZIP binary could not be written. Make sure you have write permissions to the application folder.")
        fatal_error=True

if fatal_error==False:
    Active_Time_Provider=Time_Provider()
    Active_Time_Provider.ADD_SUBSCRIBER(UI_SIGNAL)

    log("Starting 7-ZIP Task Handler...")
    Active_7ZIP_Handler.START()

    log("Obtaining local machine clock bias info...")
    sync_result={"success":False}
    while sync_result["success"]==False and Active_UI.IS_RUNNING()==True:
        log("Performing initial time synchronization via Internet...")
        sync_result=Active_Time_Provider.SYNC()

    if sync_result["success"]==True:
        log("Initial time synchronization complete. Local clock bias is "+sync_result["time_difference"]+" second(s).")

        UserHandleInstances=[]

        collect_allowed_usernames=[]
        for sender in collect_allowed_users:
            collect_allowed_usernames+=[sender["username"]]

        Active_BotListener=Bot_Listener(collect_bot_token,collect_allowed_usernames,Active_Time_Provider,UI_SIGNAL,LOGGER)
        log("Starting Bot Listener...")
        Active_BotListener.START()

        while Active_BotListener.IS_READY()==False and Active_UI.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

        if Active_UI.IS_RUNNING()==True:

            log("User message handler(s) starting up...")
            for sender in collect_allowed_users:
                UserHandleInstances+=[User_Message_Handler(collect_bot_token,sender["home"],sender["username"],sender["allow_write"],[environment_info["working_dir"]],Active_BotListener,Active_Time_Provider,Active_7ZIP_Handler,LOGGER)]

            request_sync_time=threading.Event()
            request_sync_time.clear()

            Active_User_Console=User_Console(UserHandleInstances,UI_SIGNAL,Active_7ZIP_Handler,request_sync_time,LOGGER)
            log("Starting User Console...")
            Active_User_Console.START()

            log("Startup complete. Waiting for UI thread to finish...")
            Main_Wait_Loop(Active_Time_Provider,Active_UI,request_sync_time)
            log("Left UI thread waiting loop.")

            Active_Time_Provider.REMOVE_SUBSCRIBER(UI_SIGNAL)

            log("Requesting stop to User Console...")
            Active_User_Console.REQUEST_STOP()

            Active_User_Console.CONCLUDE()
            del Active_User_Console
            log("Confirm User Console exit.")

        log("Requesting stop to 7-ZIP Task Handler...")
        Active_7ZIP_Handler.REQUEST_STOP()

        log("Requesting stop to Bot Listener...")
        Active_BotListener.REQUEST_STOP()

        Active_BotListener.CONCLUDE()
        del Active_BotListener
        log("Confirm Bot Listener exit.")

        Active_7ZIP_Handler.CONCLUDE()
        del Active_7ZIP_Handler
        log("Confirm 7-ZIP Task Handler exit.")

        while len(UserHandleInstances)>0:
            del UserHandleInstances[0]

else:

    UI_SIGNAL.send("close_standby")

LOGGER.DETACH_SIGNALLER()
Active_UI.CONCLUDE()
del Active_UI
log("Confirm UI exit.")

log("Main thread exit; program has finished.")
LOGGER.DEACTIVATE()
Flush_Std_Buffers()
