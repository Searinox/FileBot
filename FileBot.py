__version__="1.50"
__author__="Searinox Navras"


"""
INIT
"""


try:
    import sip
except:
    pass
import os
import ctypes
import sys
import time
import datetime
import threading
import warnings
import telepot
import subprocess
import win32api
import win32con
import win32process
import urllib2
import ssl
from PyQt5.QtCore import (QObject,pyqtSignal,QByteArray,Qt,qInstallMessageHandler,QEvent,QTimer,QStringListModel,QCoreApplication)
from PyQt5.QtWidgets import (QApplication,QLabel,QListView,QWidget,QSystemTrayIcon,QMenu,QLineEdit,QMainWindow,QFrame,QAbstractItemView,QGroupBox)
from PyQt5.QtGui import (QIcon,QImage,QPixmap,QFont)

SSL_NOCERT=ssl.create_default_context()
SSL_NOCERT.check_hostname=False
SSL_NOCERT.verify_mode=ssl.CERT_NONE

PENDING_ACTIVITY_HEARTBEAT_SECONDS=0.15
MAINTHREAD_HEARTBEAT_SECONDS=0.04
PRIORITY_RECHECK_INTERVAL_SECONDS=60
COMMAND_CHECK_INTERVAL_SECONDS=0.2
SERVER_TIME_RESYNC_INTERVAL_SECONDS=60*60*8
LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS=0.8
USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS=0.2
CLIPBOARD_COPY_TIMEOUT_SECONDS=2
CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS=0.125
LOG_UPDATE_INTERVAL_SECONDS=0.08

BOTS_MAX_ALLOWED_FILESIZE_BYTES=1024*1024*50
MAX_IM_SIZE_BYTES=4096

FONT_POINT_SIZE=8
FONTS={"general":{"type":"Monospace","size":1,"properties":[]},"status":{"type":"Monospace","size":1,"properties":["bold"]},"log":{"type":"Consolas","size":1,"properties":["bold"]}}

CUSTOM_UI_SCALING=1.125
COMMAND_HISTORY_MAX=50
OUTPUT_ENTRIES_MAX=8000

APP_ICONS_B64={"default":"iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAIAAABMXPacAAAABnRSTlMA/wD/AP83WBt9AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEnElEQVR42u2dMW7VQBCGn0e+AVJEQYWQklyDGokLRLTpEEdBdGlRLoBEzTWSSBEVBYrEGUzxpGDs9dvZ3dmZ2fW/FXnys/2+f+bfmbWxh2maDo2MYRj4G7fyuwafJ5rEumlJHAlQA7p/MYwF0ITuUwwbATxwd6KEtgAl6C/urvgb31/eNiGDngBJ6JNYV5JEh0x1Afjca0AvF6M6n3oHYKLX5J6tREVKlXYdpW/LPUOJWqDE99scelsZhAU4Td8z+iQlBKGJCdANeqYMYtxEdnSCfqPo1TQoFaBj9DoyFAlQm352N1up2d46nyKG2V/eoi8V+Pr0TTQg0BeRJ3uNKycDggcTdPwF/ZuHJwWy1+dnST8kGCIZMMk5fbcj+JMz8oBA31YDAn1bDcgn/U9ffuxEAwJ9Ww0I9G01IKmD7Zl+CRZKDX/QT9IgmgQE+rYakMlZ9ko/aR6NCFAv/LunnwSKQN/WiFQtaFfOwwxZUgv/vfk+cyYYdar+9TrP549vuyd+cXcVXeCi7EUMDJEkILWmd58jCnBUDn+dy1vOk2B+4YwQ/rZJQHB/25mAEP62SUCgYzsI/mPrQgT/sXUhWJDxGL2d0PMdajvpQmg9AcB/dFzoiB0WBAty7xIaZSgGBIAAGBbzMKEEwiS8+z4AAwLAgtAHIANgQRgQAHMAylBkACwIQ9OCpmlydUV+72Voi/9dHRaEwR2L+J6mCQIgA9AHoA8wzoDFc54wD+tMALAg43GMeyxHu5yE4UI6/vNPgIbeJtaT/3i0oLxiKWhc/ILK0PcoNWWqMuUgC27G/K43//lPAFsXYuI7vZlnDYL+E7Gg+8tbnfu05uCuz8+YhvDn1ZvjP178eox8/evv8C4+vLQN/6UA3pamt3R6Rj//cy5DK+Efb8QUZoKgobtdzJAN/4AAyjPBHNbrb+84qizCf+1IDYU/aylCpxw60p9r0HHzFRFALQn6KGlKwv/AXIyrnQTzwO8mCZjQiKmVuAbMnmv94Va146oKWuPa8hUSl7Qk/E8kAX+1oK31VEoyLPHw3zKc58+3kmAe74s/Gwr/SCe87stEeuM505/vv3O2Pwb1zcPT/LtB6OHwV+l4M+jHLUhhMkgap+3F3Hwy4JDOYUowLba/eXha7yH4oQf6USePXw8ILhAVelE5LM4eNCXJfqsVKwOCO8Jly3L6CRYEDWrQPyRdkhTxos4WGMrfp5c2CSMPZOnnVEF5GrTyBAT+eUq9SzLzdba136baXOBnrx1k3pq4dbDu7Uj8fcKu36jdPf0D3ilf3vwXAiy9M+54+I4fvFsPfdEcUONUdkj/IHhvqPN7igTRywbceMBIqeLEcx0CmKGHAAm9S71JTlKAhqYBfsNYu74YZA/g+SGYqV26Tmk3thKhqVpmL4ool9RjK/6gsMpk0s2M/tF3yd2jAMr0nXTv467oO1wyGT2jX/BKqnFbWZ4afdIP4utyyW/0H/h9DwL93WVAjQt7EACB78OCTnA8Efh7flYL6YQ8bGdrDOII+NU66JuVoUBvWYaCvqUAoG9mQUBvmQGgb5YBQK+dAXPioB8dfwFI8/wMQP2QSAAAAABJRU5ErkJggg==",
"deactivated":"iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAIAAABMXPacAAAABnRSTlMA/wD/AP83WBt9AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEkUlEQVR42u2dP47VMBDGk5FvgLSi2AqttPegRuIGtNshjoLoXssNkKi5x5MQFQVaac8QikiPkDjxv/HM2PncvVVe4vf7Zj57nGw8TtM0NNLGcYw/uJXfNdrsaBLrpiUxJEAN6PbFUBZAErpNMXQEsMDdiBLSApSgf7l/iD/41e+fTcggJ0AS+iTWlSSRIVNdgHjuNaCXi1GdT70LRKKX5J6tREVKlU4dpK/LPUOJWqDYz9scel0ZmAU4pm8ZfZISjNDYBOgGfaQMbNxYTnRAv1H0YhqUCtAxehkZigSoTT+7mq1UbO/1p4hh9pf36HMFvjx9FQ0I9FnkyV7jyskA78UYHX9F/3J9FiD79HiX9EO8IZIBk4zTN9u8PzkjDwj0dTUg0NfVgGzS//Tlx0k0INDX1YBAX1cD4rrYmemXYKHU8Af9JA2CSUCgr6sBqfSyV/pJ42hAgHrh3z39JFAE+rpGJGpBp3KeyJAlsfA/m+9HjgROZta/Xef5/PFt98Rf7h+CC1yUvYiBxpIEJFb0nrMFATrh8Je5vWU8CZY3zgjhr5sEBPfXHQkI4a+bBAQ6uo3gP7ouRPAfXReCBSk3Z61DtyfUTlKF0HYAgP/IuNCMHRYECzLvEhLTUDQIAAHQNMZhwhQIg/Dp6wA0CAALQh2ADIAFoUEAjAGYhiIDYEFokhY0TZOpO/Jnn4a2+O/qsCC02LaK72maIAAyAHUA6gDlDFi95wnjsMwAAAtSbnPcYzna5CAMF5Lxn38CNLSbWE/+Y9GC8iZLXuOKn1Ap+p47SBnhR1RmXkEWXqyR37XmP/+NAbouFBmtx4dVrSFq+E/AgsSSYAnu6fEuMpBvfVvGl//rX//4T/HhtW74rwWwtjS9p9MqLOaPrczcVk5DJepVMp9CJzFlRMkv6xAeCZaw3nx7F6PKnis28VTrFi+Va8jSZvpLDTouvgICiCVBH1OakvAfIhfjaifBMvC7SYJIaBSpFbsGMQHuPWavJ6ZmQdvO7PkKsUtaEv4HSRBf5ba1nkpJhsUe/nuGc/v7XhIso2H1saHwD1TC27qMpTZeMv31/nvM8XNQX67Py+96ofvDX6TizaAftiCBwSCpHduLuvlkwCGZy5RgWh1/uT5vz+D9owX6QSeP2saqfA+HW+fMjpCp21ix0I/NAO+JcNuynH6CBUGDGvSH1J30sr2oIanyrDV7Bp82CCMPeOnnzILyNGjlDQjx/eTaSzJzO9vau6k2F/jZaweZjybuXax7O2LfT9j0jtrd0x+wp3x58V8IsPTJuPnyHb94tx76ojGgRldOSH9gfDbU+DNFjOh5A84NaCmzOPZchwBq6CFAQu1Sb5DjFKChYSC+YKw9vxh5L2D5JZipVbrM1M61EqGpWmYvighPqV0r/iCwyqRSzTj76LvkblEAYfpGqnd3KvoGl0ycZfQrXklz3FaWp5xN+l58XS75OfuB33cj0D9dBtS4sQcBEPg2LOiA40Hgn/ldLSQT8rCdvTayI4ifrYO+2jQU6DWnoaCvKQDoq1kQ0GtmAOirZQDQS2fAkjjoB9tftPkDoEi2BJIAAAAASUVORK5CYII=",
"busy":"iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAIAAABMXPacAAAABnRSTlMA/wD/AP83WBt9AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEk0lEQVR42u2dPY7UQBCF7VLHkyCtCIgQ0t6DmDOQboY4CiKblBtwAe4xEiEBGolkLmACS4Pxz/RfdVV19+todzVje75X9bqqx+sep2kaKhnjOIa/uJbPNdq80CjWVUtiSIAS0O2LoSyAJHSbYugIYIG7ESWkBchBP91iTnSqQwY5AeJqmFuBCzhZVKK4AOHcS0DPF6M4n3InCEQvyT1ZiYKUCh3aS1+Xe4ISpUCxH7c69LoyMAvwmL5l9FFKMEJjE6AZ9IEysHFjOdAD+pWiF9MgV4CG0cvIkCVAafrJ3WyhZvvoerIYJr/5iD5X4MvTV9GAQJ9FnuQ1rpQM2D0Zo+Ov6J8vVwGyL89PUR9kN0QSYJJx+mbH7kdOyAMCfV0NCPR1NSCb9D9//dGJBgT6uhoQ6OtqQFwn65l+DhaKDX/Qj9LAmwQE+roakMpVtko/ah71CFAu/JunHwWKQF/XiEQtqCvnCQxZEgv/3nw/cCZwMlX/dp3ny6f3zROfbv4FLkpexMBgSQISa3r7HF6ATjj8Zb7eMp4Eyy/OCOGvmwQE99edCQjhr5sEBDq6g+A/ui5E8B9dF4IFKQ9n7YLud6h10oXQdgKA/8i40IwdFgQLMu8SEmUoBgSAABga8zChBMIk3H0fgAEBYEHoA5ABsCAMCIA5AGUoMgAWhCFpQdM0mfpGvvcytMZ/V4cFYYSOVXxP0wQBkAHoA9AHKGfA6jlPmIdlJgBYkPKY4x7L0SYnYbiQjP/8E6Ci3cRa8h+LFpRWLO0aV3hBpeh77kHKCN+iMvPystjFGvhea/7z3xyg60KB0fr4ZUV7iBL+47EgsSRYgnt5fgoM5D9v3s0/vPr10/P2b7/3D/HxtW74rwWwtjR9pNMd/fLXpQy1hL+/EROoR7e+kekkpowo+mEdwjPBEtbb7x9CVFmF/9aRKgr/oKUImaZspr/UoOHmyyOAWBK0UdLkhP8Q+ujik0T4b39uPvwPBdhqxa5BSIDvvuao2jFVBW1xHfkKsUuaE/4PkiC8y61rPZWiDIs9/I8M5/73oyRYxvvq14rCf/DuIcP1BMX7NZ0v14TZ9R7U3vcuwz9qMS52DxkW+n4LEpgM0pSwaT4JcEjmNDmYVq8/X67bI+z+0QJ9r5MHbWOVv4fD0oJsToaZFpS8q1VQBuweCF9b5tOPsCBoUIL+ELuTXrIXVSRVmrUmV/BxkzDygJd+ShWUpkEtT0AIv06uvSQTt7MtvZtqdYGfvHaQeGvi0cmatyP2/YRN76jdPP0Be8rnN/+ZAHPvjJtP3/CDd8uhz5oDSlxKh/QHxntDjd9TxIieN+DcgBHV0HDnOgRQQw8BInqXcpMcpwAVTQPhDWPp+mLkPYHlh2DGdukypZ2rJUJjtUxeFBEuqV0t/iCwyqTSzTj76JvkblEAYfpGunfXFX2DSybOMvr1QyxiatxalqecTfq7+Jpc8nP2A7/tQaDfXQaU+GIPAiDwbVjQo/9EOA78np/VQjIhD9s5RMSOILxaB321MhToNctQ0NcUAPTVLAjoNTMA9NUyAOilM2BJHPS94y98l4ldLLAYcwAAAABJRU5ErkJggg=="}

QTMSG_BLACKLIST_STARTSWITH=["Qt: Untested Windows version","WARNING: QApplication was not created in the main()","QTextCursor::setPosition: Position '","OleSetClipboard: Failed to set mime data (text/plain) on clipboard: COM error"]

LOG_HANDLE=None
UI_SIGNAL=None
PATH_7ZIP=""


"""
DEFS
"""


GetTickCount64=ctypes.windll.kernel32.GetTickCount64
GetTickCount64.restype=ctypes.c_uint64
GetTickCount64.argtypes=()

def get_run_environment():
    retval={"working_dir":"","process_binary":"","source_mode":False,"arguments":[]}
    sys_exe=sys.executable
    retval["arguments"]=sys.argv
    retval["process_binary"]=os.path.basename(sys_exe).lower()
    retval["working_dir"]=os.path.realpath(os.path.dirname(sys_exe))
    retval["process_id"]=os.getpid()

    if retval["process_binary"]=="python.exe":
        if len(retval["arguments"])>0:
            if retval["arguments"][0].replace("\"","").lower().strip().endswith(".py"):
                retval["working_dir"]=os.path.realpath(os.path.dirname(retval["arguments"][0]))
                retval["arguments"]=retval["arguments"][1:]
                retval["source_mode"]=True
    return retval

def qtmsg_handler(msg_type,msg_log_context,msg_string):
    global QTMSG_BLACKLIST_STARTSWITH

    for entry in QTMSG_BLACKLIST_STARTSWITH:
        if msg_string.startswith(entry):
            return

    sys.stderr.write(msg_string+"\n")
    return

def log(input_text):
    global LOGGER

    if LOGGER is not None:
        LOGGER.LOG("MAINTHRD",input_text)

    return

def OS_uptime():
    return ctypes.windll.kernel32.GetTickCount64()/1000.0

def Current_UTC_Internet_Time():
    global SSL_NOCERT

    response=urllib2.urlopen("https://time.gov/actualtime.cgi",context=SSL_NOCERT)
    timestr=response.read()
    quot1=timestr.find("time=\"")
    quot1+=len("time=\"")
    quot2=quot1+timestr[quot1+1:].find("\"")
    quot2+=1
    return int(timestr[quot1:quot2-3])/1000.0

def set_process_priority_idle():
    global CURRENT_PROCESS_HANDLE

    try:
        if win32process.GetPriorityClass(CURRENT_PROCESS_HANDLE)!=win32process.IDLE_PRIORITY_CLASS:
            win32process.SetPriorityClass(CURRENT_PROCESS_HANDLE,win32process.IDLE_PRIORITY_CLASS)
            log("Idle process priority set.")
    except:
        log("Error managing process priority.")
    return

def Perform_Time_Sync(input_signaller=None):
    log("Performing time synchronization via Internet...")
    if Sync_Server_Time()==True:
        get_time_diff=local_machine_time_delta_str()
        log("Time synchronization complete. Local clock bias is "+get_time_diff+" second(s).")
        if input_signaller is not None:
            input_signaller.send("clock_bias",get_time_diff)
    else:
        log("Time synchronization failed.")
        return False
    return True

def Sync_Server_Time():
    global TIME_DELTA_LOCK
    global TELEGRAM_SERVER_TIMER_DELTA

    update_success=False

    try:
        get_new_delta=Current_UTC_Internet_Time()-OS_uptime()
        update_success=True
    except:
        pass

    if update_success==True:
        TIME_DELTA_LOCK.acquire()
        TELEGRAM_SERVER_TIMER_DELTA=get_new_delta
        TIME_DELTA_LOCK.release()

    return update_success

def server_time():
    global TIME_DELTA_LOCK
    global TELEGRAM_SERVER_TIMER_DELTA

    TIME_DELTA_LOCK.acquire()
    get_delta=TELEGRAM_SERVER_TIMER_DELTA
    TIME_DELTA_LOCK.release()
    return round(OS_uptime()+get_delta,3)

def local_machine_time_delta_str():
    time_difference=round(time.time()-server_time(),3)
    if time_difference>0:
        retval="+"+str(time_difference)
    else:
        retval=str(time_difference)
    return retval

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


class Logger(object):
    def __init__(self,input_path):
        self.logging_path=input_path
        self.log_handle=None
        self.log_lock=threading.Lock()
        self.active_signaller=None
        return

    def START(self):
        try:
            self.log_handle=open(self.logging_path,"a")
        except:
            pass
        return

    def STOP(self):
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

        try:
            sys.stdout.write(msg)
        except:
            pass

        self.log_lock.release()

        if self.active_signaller is not None:
            try:
                self.active_signaller.send("logger_newline",msg)
            except:
                pass

        return


class Message_Listener(object):
    def __init__(self,input_token,username_list,input_listener,input_logger=None):
        self.token=input_token
        self.active_logger=input_logger
        self.keep_running=threading.Event()
        self.keep_running.clear()
        self.has_quit=threading.Event()
        self.has_quit.set()
        self.is_ready=threading.Event()
        self.is_ready.clear()
        self.last_ID_checked=-1
        self.start_time=0
        self.active_UI_signaller=input_listener
        self.working_thread=threading.Thread(target=self.work_loop)
        self.working_thread.daemon=True
        self.listen_users=username_list
        self.messagelist_lock={}
        for username in self.listen_users:
            self.messagelist_lock[username]=threading.Lock()
        self.user_messages={}
        for username in self.listen_users:
            self.user_messages[username]=[]
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("LSTNSRVC",input_text)

    def START(self):
        self.has_quit.clear()
        self.keep_running.set()
        self.working_thread.start()

    def STOP(self):
        self.keep_running.clear()
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def IS_READY(self):
        return self.is_ready.is_set()==True

    def work_loop(self):
        self.bot_handle=telepot.Bot(self.token)
        last_check_status=False
        bot_bind_ok=False
        activation_fail_announce=False

        while bot_bind_ok==False and self.keep_running.is_set()==True:
            try:
                self.name=self.bot_handle.getMe()[u"username"]
                bot_bind_ok=True
            except:
                if activation_fail_announce==False:
                    self.log("Listener service activation error. Will keep trying...")
                    activation_fail_announce=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)

        if self.keep_running.is_set()==True:
            self.catch_up_IDs()
            self.log("Listener service for bot \""+self.name+"\" is now active.")
            self.active_UI_signaller.send("bot_name",self.name)
            self.is_ready.set()

        while self.keep_running.is_set()==True:
            time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)
            response=[]

            try:
                response=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
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
        self.log("Listener has exited.")
        self.has_quit.set()
        return

    def catch_up_IDs(self):
        retrieved=False
        responses=[]
        announced_fail=False
        while retrieved==False:
            try:
                responses=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                retrieved=True
                self.log("Caught up with messages.")
            except:
                if announced_fail==False:
                    self.log("Failed to catch up with messages. Will keep trying...")
                    announced_fail=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=server_time()
        return

    def organize_messages(self,input_msglist):
        collect_new_messages={}
        for username in self.listen_users:
            collect_new_messages[username]=[]

        newest_ID=self.last_ID_checked
        for i in reversed(range(len(input_msglist))):
            this_msg_ID=input_msglist[i][u"update_id"]
            if this_msg_ID>self.last_ID_checked:
                if newest_ID<this_msg_ID:
                    newest_ID=this_msg_ID
                try:
                    msg_send_time=input_msglist[i][u"message"][u"date"]
                except:
                    msg_send_time=0
                if msg_send_time>=self.start_time:
                    if server_time()-msg_send_time<=30:
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
            self.messagelist_lock[message].acquire()
            if len(collect_new_messages[message])>0:
                self.user_messages[message]+=collect_new_messages[message]
            for i in reversed(range(len(self.user_messages[message]))):
                if server_time()-self.user_messages[message][i][u"date"]>30:
                    del self.user_messages[message][i]
            self.messagelist_lock[message].release()
        return

    def consume_user_messages(self,input_username):
        self.messagelist_lock[input_username].acquire()
        get_messages=self.user_messages[input_username]
        self.user_messages[input_username]=[]
        self.messagelist_lock[input_username].release()
        return get_messages

class User_Message_Handler(object):
    def __init__(self,input_token,input_root,input_user,input_write,input_listener_service,input_logger=None):
        self.active_logger=input_logger
        self.working_thread=threading.Thread(target=self.work_loop)
        self.working_thread.daemon=True
        self.token=input_token
        self.listener=input_listener_service
        self.keep_running=threading.Event()
        self.keep_running.clear()
        self.bot_has_quit=threading.Event()
        self.bot_has_quit.set()
        self.lock_last_folder=threading.Lock()
        self.last_folder=""
        self.allow_writing=input_write
        self.listen_flag=threading.Event()
        self.listen_flag.clear()
        self.last_send_time=0
        self.allowed_user=input_user
        self.lastsent_timers=[]
        self.bot_lock_pass=""
        self.allowed_root=input_root
        self.pending_lockclear=threading.Event()
        self.pending_lockclear.clear()
        self.lock_status=threading.Event()
        self.lock_status.clear()
        self.processing_messages=threading.Event()
        self.processing_messages.clear()
        if self.allowed_root=="*":
            self.set_last_folder("C:\\")
        else:
            self.set_last_folder(self.allowed_root)
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("MSGHNDLR",input_text)
        return

    def sendmsg(self,sid,msg):
        for i in reversed(range(len(self.lastsent_timers))):
            if OS_uptime()-self.lastsent_timers[i]>=60:
                del self.lastsent_timers[i]
        second_delay=OS_uptime()-self.last_send_time
        if second_delay<1:
            second_delay=1-second_delay
        else:
            second_delay=0
        if len(self.lastsent_timers)>0:
            extra_sleep=(len(self.lastsent_timers)**1.8)/25.5
        else:
            extra_sleep=0
        throttle_time=second_delay+max(extra_sleep-second_delay,0)
        time.sleep(throttle_time)
        try:
            self.last_send_time=OS_uptime()
            self.bot_handle.sendMessage(sid,msg)
            self.lastsent_timers.append(self.last_send_time)
            excess_entries=max(0,len(self.lastsent_timers)-40)
            for _ in range(excess_entries):
                del self.lastsent_timers[0]
            return True
        except:
            self.log("<"+self.allowed_user+"> "+"Message handler was unable to respond.")
            return False

    def allowed_path(self,input_path):
        if input_path.lower().find(self.allowed_root.lower())==0 or self.allowed_root=="*":
            return True
        else:
            return False

    def usable_dir(self,newpath):
        if self.allowed_path(newpath)==True:
            if os.path.exists(newpath)==True:
                return True
        return False

    def usable_path(self,newpath):
        if self.allowed_path(newpath)==True:
            if os.path.exists(newpath)==True:
                try:
                    win32api.GetLongPathNameW(win32api.GetShortPathName(newpath))
                    return True
                except:
                    return False
        return False

    def rel_to_abs(self,raw_command_args,isfile=False):
        command_args=raw_command_args.replace("/","\\")
        if command_args.find(":")!=-1:
            newpath=command_args
        else:
            newpath=os.path.join(self.last_folder,command_args)
        if newpath[-1]!="\\" and isfile==False:
            newpath+="\\"
        if newpath.find("\\\\")!=-1 or newpath.find("\\.\\")!=-1 or newpath.find("\\..\\")!=-1 or newpath.find("?")!=-1 or newpath.find("*")!=-1:
            newpath="<BAD PATH>"
        return newpath

    def check_tasks(self):
        if self.pending_lockclear.is_set()==True:
            self.pending_lockclear.clear()
            if self.bot_lock_pass!="":
                self.bot_lock_pass=""
                self.log("<"+self.allowed_user+"> "+"Message handler unlocked by console.")
            else:
                self.log("<"+self.allowed_user+"> "+"Message handler unlock was requested, but it is not locked.")
            self.listener.consume_user_messages(self.allowed_user)
        return

    def work_loop(self):
        global LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS
        global USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS

        self.bot_handle=telepot.Bot(self.token)
        bot_bind_ok=False
        activation_fail_announce=False
        while bot_bind_ok==False:
            try:
                self.bot_handle.getMe()[u"username"]
                bot_bind_ok=True
            except:
                if activation_fail_announce==False:
                    self.log("<"+self.allowed_user+"> "+"Message handler activation error. Will keep trying...")
                    activation_fail_announce=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)

        self.listener.consume_user_messages(self.allowed_user)
        self.log("<"+self.allowed_user+"> "+"Message handler for user \""+self.allowed_user+"\" is now active.")

        while self.keep_running.is_set()==True:
            time.sleep(USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS)
            self.check_tasks()
            if self.listen_flag.is_set()==True:
                new_messages=self.listener.consume_user_messages(self.allowed_user)
                total_new_messages=len(new_messages)
                if total_new_messages>0:
                    self.processing_messages.set()
                    self.log("<"+self.allowed_user+"> "+str(total_new_messages)+" new message(s) received.")
                    self.process_messages(new_messages)
                    self.processing_messages.clear()

        self.log("<"+self.allowed_user+"> "+"Message handler exited.")
        self.bot_has_quit.set()
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
        self.log("<"+self.allowed_user+"> "+"User message handler start issued, home path is \""+self.allowed_root+"\", allow writing: "+str(self.allow_writing).upper()+".")
        self.bot_has_quit.clear()
        self.keep_running.set()
        self.working_thread.start()
        return

    def LISTEN(self,new_state):
        if new_state==True:
            self.log("<"+self.allowed_user+"> "+"Listen started.")
            self.listener.consume_user_messages(self.allowed_user)
            self.listen_flag.set()
        else:
            self.log("<"+self.allowed_user+"> "+"Listen stopped.")
            self.listen_flag.clear()
        return

    def STOP(self):
        self.log("<"+self.allowed_user+"> "+"Message handler stop issued.")
        self.listen_flag.clear()
        self.keep_running.clear()
        return

    def IS_RUNNING(self):
        return self.bot_has_quit.is_set()==False

    def process_messages(self,input_msglist):
        for m in input_msglist:
            if server_time()-m[u"date"]<=30:
                if u"text" in m:
                    self.process_instructions(m[u"from"][u"id"],m[u"text"],m[u"chat"][u"id"])
                else:
                    if u"document" in m:
                        self.process_files(m[u"from"][u"id"],m[u"document"][u"file_id"],m[u"document"][u"file_name"])
                    elif u"audio" in m:
                        proceed=True
                        try:
                            filename=self.bot_handle.getFile(m[u"audio"][u"file_id"])[u"file_path"]
                            filename=filename[filename.rfind("/")+1:]
                            fileext=filename[filename.rfind(".")+1:]
                            filetitle=""
                            fileperformer=""
                            if u"title" in m[u"audio"]:
                                filetitle=m[u"audio"][u"title"]
                            if u"performer" in m[u"audio"]:
                                fileperformer=m[u"audio"][u"performer"]
                            if filetitle!="" or fileperformer!="":
                                newname=""
                                if fileperformer!="" and filetitle=="":
                                    newname=fileperformer
                                if fileperformer!="" and filetitle!="":
                                    newname=fileperformer+" - "+filetitle
                                if fileperformer=="" and filetitle!="":
                                    newname=filetitle
                                newname+="."+fileext
                                newname=newname.replace("/","").replace("\\","").replace("?","").replace("*","").replace(":","").replace("|","").replace("<","").replace(">","")
                                filename=newname
                        except:
                            self.sendmsg(m[u"from"][u"id"],"Could not get filename.")
                            proceed=False
                        if proceed==True:
                            self.process_files(m[u"from"][u"id"],m[u"audio"][u"file_id"],filename)
                    else:
                        self.sendmsg(m[u"from"][u"id"],"Media type unsupported. Send as regular file or the filename will not preserve.")
        return

    def process_files(self,sid,fid,filename):
        if self.bot_lock_pass!="" or self.allow_writing==False:
            return

        foldername=self.get_last_folder()
        complete_put_path=foldername+filename
        self.sendmsg(sid,"Putting file \""+filename+"\" at \""+foldername+"\"...")
        self.log("<"+self.allowed_user+"> "+" Receiving file \""+complete_put_path+"\"...")
        if os.path.exists(complete_put_path)==False or (os.path.exists(complete_put_path)==True and os.path.isfile(complete_put_path)==False):
            try:
                self.bot_handle.download_file(fid,complete_put_path)
                self.sendmsg(sid,"Finished putting file \""+complete_put_path+"\".")
                self.log("<"+self.allowed_user+"> "+" File download complete.")
            except:
                self.sendmsg(sid,"File \""+filename+"\" could not be placed.")
                self.log("<"+self.allowed_user+"> "+" File download aborted due to unknown issue.")
        else:
            self.sendmsg(sid,"File \""+filename+"\" already exists at the location.")
            self.log("<"+self.allowed_user+"> "+" File download aborted due to existing instance.")
        return

    def chunkalize(self,input_string,chunksize):
        retval=[]
        start=0
        while start<len(input_string):
            end=start+min(chunksize,len(input_string)-start)
            retval.append(input_string[start:end])
            start=end
        return retval

    def folder_list_string(self,input_folder,search_in,folders_only):
        search=search_in.lower()
        foldername=input_folder.lower().strip()
        if foldername=="":
            return "<No path.>"

        response=""
        filelist=[]
        folderlist=[]

        if foldername[-1]!="\\":
            foldername+="\\"

        try:
            for name in os.listdir(foldername):
                path=os.path.join(foldername,name)
    
                if os.path.isfile(path):
                    if folders_only==False:
                        if name.lower().find(search)!=-1 or search=="":
                            filelist.append(name+" [Size: "+readable_size(os.path.getsize(path))+"]")
                else:
                    if name.lower().find(search)!=-1 or search=="":
                        folderlist.append(name)

            if len(folderlist)>0:
                response+="<FOLDERS:>\n"

            for folder in folderlist:
                response+="\n"+folder

            if len(folderlist)>0:
                response+="\n\n"

            if len(filelist)>0:
                response+="<FILES:>\n"

            for filename in filelist:
                response+="\n"+filename
        except:
            response="<Bad dir path.>"

        return response

    def process_instructions(self,sid,msg,cid):
        global BOTS_MAX_ALLOWED_FILESIZE_BYTES
        global MAX_IM_SIZE_BYTES
        if self.bot_lock_pass!="":
            if msg.lower().find("/unlock ")==0:
                if msg[len("/unlock "):].strip()==self.bot_lock_pass:
                    self.bot_lock_pass=""
                    self.lock_status.clear()
                    self.sendmsg(sid,"Bot unlocked.")
                    self.log("<"+self.allowed_user+"> "+"Message handler unlocked by user.")
                    return
                else:
                    return
            else:
                return

        if msg[0]!="/":
            return
        cmd_end=msg.find(" ")
        if cmd_end==-1:
            cmd_end=len(msg)
        command_type=msg[1:cmd_end].strip().lower()
        command_args=msg[cmd_end+1:].strip()
        response=""

        if command_type=="start":
            self.log("<"+self.allowed_user+"> "+"Message handler start requested.")
        elif command_type=="dir":

            extra_search=""

            if command_args.lower().find("?f:")!=-1:
                start=command_args.lower().find("?f:")
                end=command_args[start:].find(" ")
                if end==-1:
                    end=len(command_args)
                else:
                    end+=start
                extra_search=command_args[start+len("?f:"):end]
                if command_args[:start].strip()!="":
                    command_args=command_args[:start].strip()
                else:
                    command_args=command_args[end:].strip()

            if command_args.lower().find("?d")!=-1:
                folders_only=True
                start=command_args.lower().find("?d")
                end=start+len("?d")
                if command_args[:start].strip()!="":
                    command_args=command_args[:start].strip()
                else:
                    command_args=command_args[end:].strip()
            else:
                folders_only=False

            self.log("<"+self.allowed_user+"> "+"Listing requested for path \""+command_args+"\" with search string \""+extra_search+"\", folders only="+str(folders_only).upper()+".")

            if command_args=="":
                use_folder=self.get_last_folder()
            else:
                use_folder=command_args
            use_folder=self.rel_to_abs(command_args)
            if self.allowed_path(use_folder)==True:
                dirlist=self.folder_list_string(use_folder,extra_search,folders_only)
            else:
                dirlist="<Bad dir path.>"
            for chunk in self.chunkalize(dirlist,MAX_IM_SIZE_BYTES):
                if self.sendmsg(sid,chunk)==False:
                    response="<Listing interrupted.>"
                    break
            if response=="":
                response="<Listing finished.>"

        elif command_type=="cd":
            if command_args.strip()!="":
                newpath=self.rel_to_abs(command_args)
                if self.usable_dir(newpath)==True:
                    if os.path.exists(newpath)==True:
                        try:
                            newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                        except:
                            pass
                        if newpath[-1]!="\\":
                            newpath+="\\"
                        if len(newpath)>0:
                            newpath=newpath[0].upper()+newpath[1:]
                        self.set_last_folder(newpath)
                        response="Current folder changed to \""+newpath+"\"."
                        self.log("<"+self.allowed_user+"> "+"Current folder changed to \""+newpath+"\".")
                else:
                    response="Bad path."
            else:
                newpath=self.get_last_folder()
                response="Current folder is \""+newpath+"\"."
                self.log("<"+self.allowed_user+"> "+"Queried current folder, which is \""+newpath+"\".")
        elif command_type=="get":
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                self.log("<"+self.allowed_user+"> "+"Requested get file \""+newpath+"\". Processing...")
                self.sendmsg(sid,"Getting file, please wait...")
                try:
                    fsize=os.path.getsize(newpath)
                    if fsize<=BOTS_MAX_ALLOWED_FILESIZE_BYTES and fsize!=0:
                        self.bot_handle.sendDocument(cid,open(newpath,"rb"))
                    else:
                        if fsize!=0:
                            response="Bots cannot upload files larger than "+readable_size(BOTS_MAX_ALLOWED_FILESIZE_BYTES)+"."
                            self.log("<"+self.allowed_user+"> "+"Requested file too large.")
                        else:
                            response="File is empty."
                except:
                    response="Problem getting file."
                    self.log("<"+self.allowed_user+"> "+"File send error.")
            else:
                response="File not found or inaccessible."
                self.log("<"+self.allowed_user+"> "+"File not found.")
        elif command_type=="eat" and self.allow_writing==True:
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                self.log("<"+self.allowed_user+"> "+"Requested eat file \""+newpath+"\".")
                self.sendmsg(sid,"Eating file, please wait...")
                success=False
                try:
                    fsize=os.path.getsize(newpath)
                    if fsize<=BOTS_MAX_ALLOWED_FILESIZE_BYTES and fsize!=0:
                        self.bot_handle.sendDocument(cid,open(newpath,"rb"))
                        success=True
                    else:
                        if fsize!=0:
                            response="Bots cannot upload files larger than 50MB."
                        else:
                            response="File is empty."
                except:
                    response="Problem getting file."
                    self.log("<"+self.allowed_user+"> "+"File send error.")
                if success==True:
                    try:
                        self.log("<"+self.allowed_user+"> "+"File sent. Deleting...")
                        os.remove(newpath)
                        self.sendmsg(sid,"File deleted.")
                    except:
                        response="Problem deleting file."
                        self.log("<"+self.allowed_user+"> "+"File delete error.")
                        self.log("<"+self.allowed_user+"> "+"File deleted.")
            else:
                response="File not found or inaccessible."
        elif command_type=="del" and self.allow_writing==True:
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                self.log("<"+self.allowed_user+"> "+"Requested delete file \""+newpath+"\".")
                try:
                    os.remove(newpath)
                    self.sendmsg(sid,"File deleted.")
                except:
                    response="Problem deleting file."
                    self.log("<"+self.allowed_user+"> "+"File delete error.")
            else:
                response="File not found or inaccessible."
        elif command_type=="up":
            if self.last_folder.count("\\")>1:
                newpath=self.get_last_folder()
                newpath=newpath[:-1]
                newpath=newpath[:newpath.rfind("\\")+1]
                if self.allowed_path(newpath)==True:
                    self.set_last_folder(newpath)
                    response="Current folder is now \""+newpath+"\"."
                    self.log("<"+self.allowed_user+"> "+"Current folder changed to \""+newpath+"\".")
                else:
                    response="Already at top folder."
            else:
                response="Already at top folder."
        elif command_type=="zip" and self.allow_writing==True:
            newpath=self.rel_to_abs(command_args)
            if os.path.exists(newpath)==False and newpath[-1]=="\\":
                newpath=newpath[:-1]
            if self.usable_path(newpath)==True:
                try:
                    if os.path.isfile(newpath):
                        folder_path=newpath[:newpath.rfind("\\")+1]
                    else:
                        folder_path=newpath[:newpath[:-1].rfind("\\")+1]
                    archive_filename=newpath[newpath.rfind("\\")+1:]
                    if archive_filename=="":
                        archive_filename=newpath[newpath[:-1].rfind("\\")+1:]
                        if archive_filename[-1]=="\\":
                            archive_filename=archive_filename[:-1]
                    zip_command="\""+PATH_7ZIP+"7z.exe"+"\" a -mx9 -t7z \""+archive_filename+".7z.TMP\" \""+archive_filename+"\""
                    folder_command="cd /d \""+folder_path+"\""
                    rename_command="ren \""+archive_filename+".7z.TMP\" \""+archive_filename+".7z\""
                    prompt_commands=folder_command+" & "+zip_command+" & "+rename_command
                    if os.path.exists(folder_path+archive_filename+".7z")==False:
                        subprocess.Popen(prompt_commands,shell=True,creationflags=subprocess.SW_HIDE)
                        response="Issued zip command."
                        self.log("<"+self.allowed_user+"> "+"Zip command issued on \""+folder_path+archive_filename+"\".")
                    else:
                        response="The archive \""+archive_filename+".7z\" already exists at the location."
                except:
                    response="Problem getting file."
                    self.log("<"+self.allowed_user+"> "+"Zip \""+command_args+"\" failed.")
            else:
                response="File not found or inaccessible."
                self.log("<"+self.allowed_user+"> "+"[BOTWRK] Zip \""+command_args+"\" file not found or inaccessible.")
        elif command_type=="lock":
            if command_args.strip()!="" and len(command_args.strip())<=32:
                self.bot_lock_pass=command_args.strip()
                response="Bot locked."
                self.lock_status.set()
                self.log("<"+self.allowed_user+"> "+"Message handler was locked down with password.")
            else:
                response="Bad password for locking."
        elif command_type=="unlock":
            response="The bot is already unlocked."
        elif command_type=="help":
            response="AVAILABLE BOT COMMANDS:\n\n"
            response+="/help: display this help screen\n"
            response+="/cd [PATH]: change path(eg: /cd c:\windows); no argument returns current path\n"
            response+="/dir [PATH] [?f:<filter>] [?d]: list files/folders; filter results(/dir c:\windows ?f:.exe); use ?d for listing directories only; no arguments lists current folder\n"
            if self.allow_writing==True:
                response+="/zip <PATH[FILE]>: make a 7-ZIP archive, extension will be .7z.TMP until finished\n"
            response+="/up: move up one folder from current path\n"
            response+="/get <[PATH]FILE>: retrieve the file at the location to Telegram\n"
            if self.allow_writing==True:
                response+="/eat <[PATH]FILE>: upload the file at the location to Telegram, then delete it from its original location\n"
                response+="/del <[PATH]FILE>: delete the file at the location\n"
            response+="/lock <PASSWORD>: lock the bot from responding to messages\n"
            response+="/unlock <PASSWORD>: unlock the bot\n"
            response+="\nSlashes work both ways in paths (/cd c:/windows, /cd c:\windows)"
            self.log("<"+self.allowed_user+"> "+"Help requested.")
        else:
            self.sendmsg(sid,"Command unknown. Type \"/help\" for a list of commands.")

        if response!="":
            self.sendmsg(sid,response)
        return

class User_Console(object):
    def __init__(self,bot_list,input_signaller,input_time_sync,input_logger=None):
        self.active_logger=input_logger
        self.working_thread=threading.Thread(target=self.process_input)
        self.working_thread.daemon=True
        self.active_UI_signaller=input_signaller
        self.is_exiting=threading.Event()
        self.is_exiting.clear()
        self.bot_list=bot_list
        self.has_quit=threading.Event()
        self.has_quit.clear()
        self.request_exit=threading.Event()
        self.request_exit.clear()
        self.lock_command=threading.Lock()
        self.request_time_sync=input_time_sync
        self.pending_command=""
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("UCONSOLE",input_text)

    def START(self):
        self.working_thread.start()
        return

    def STOP(self):
        self.request_exit.set()
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def bots_running(self):
        total=0
        for bot_instance in self.bot_list:
            if bot_instance.IS_RUNNING()==True:
                total+=1
        return total

    def any_bots_busy(self):
        for bot_instance in self.bot_list:
            if bot_instance.processing_messages.is_set()==True:
                return True
        return False

    def process_command(self,user_input):
        user_data=user_input.split(" ")
        input_command=user_data[0].lower().strip()
        if len(user_data)>1:
            input_argument=user_data[1].strip()
        else:
            input_argument=""

        if input_command=="start":
            for bot_instance in self.bot_list:
                if bot_instance.allowed_user.lower()==input_argument or input_argument=="":
                    bot_instance.LISTEN(True)
            return True
        elif input_command=="stop":
            for bot_instance in self.bot_list:
                if bot_instance.allowed_user.lower()==input_argument or input_argument=="":
                    bot_instance.LISTEN(False)
            return True
        elif input_command=="stats":
            for bot_instance in self.bot_list:
                if bot_instance.allowed_user.lower()==input_argument or input_argument=="":
                    self.log("Message handler for user \""+bot_instance.allowed_user+"\":\nHome path=\""+bot_instance.allowed_root+"\"\nWrite mode: "+str(bot_instance.allow_writing).upper()+"\nCurrent folder=\""+bot_instance.get_last_folder()+"\"\nLocked: "+str(bot_instance.lock_status.is_set()).upper()+"\nListening: "+str(bot_instance.listen_flag.is_set()).upper()+"\n")
            return True
        elif input_command=="list":
            list_out=""
            for bot_instance in self.bot_list:
                list_out+=bot_instance.allowed_user+", "
            list_out=list_out[:-2]+"."
            self.log("Allowed user(s): "+list_out)
            return True
        elif input_command=="unlock":
            for bot_instance in self.bot_list:
                if bot_instance.allowed_user.lower()==input_argument or input_argument=="":
                    bot_instance.pending_lockclear.set()
            return True
        elif input_command=="sync":
            if self.request_time_sync.is_set()==False:
                self.log("Manual Internet time synchronization requested...")
                self.request_time_sync.set()
            else:
                self.log("Manual Internet time synchronization is already in progress.")
            return True
        elif input_command=="help":
            self.log("AVAILABLE CONSOLE COMMANDS:\n")
            self.log("start [USER]: start listening to messages for user; leave blank to apply to all instances")
            self.log("stop [USER]: stop listening to messages for user; leave blank to apply to all instances")
            self.log("unlock [USER]: unlock the bot for user; leave blank to apply to all instances")
            self.log("stats [USER]: list bot stats; leave blank to list all instances")
            self.log("list: lists allowed users")
            self.log("sync: manually re-synchronize bot time with Internet time")
            self.log("help: display help")
            self.log("exit: close the program\n")
            return True
        else:
            self.log("Unrecognized command. Type \"help\" for a list of commands.")
            return False
        return False

    def COMMAND_SEND(self,input_command):
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            self.pending_command=input_command
            self.lock_command.release()
        return

    def retrieve_command(self):
        retval=""
        if self.request_exit.is_set()==False:
            self.lock_command.acquire()
            retval=self.pending_command
            self.pending_command=""
            self.lock_command.release()
        return retval

    def process_input(self):
        global COMMAND_CHECK_INTERVAL_SECONDS

        for bot_instance in self.bot_list:
            bot_instance.START()
            bot_instance.LISTEN(True)
        self.log("User console activated.")
        self.log("Type \"help\" in the console for available commands.")
        self.active_UI_signaller.send("attach_console",self)

        if self.bots_running()==0:
            self.is_exiting.set()

        continue_processing=True

        last_busy_state=False

        while continue_processing==True:
            time.sleep(COMMAND_CHECK_INTERVAL_SECONDS)
            if last_busy_state!=self.any_bots_busy():
                last_busy_state=not last_busy_state
                UI_SIGNAL.send("bots_busy",last_busy_state)

            command=self.retrieve_command()

            if command!="":
                result=False

                if command.lower()=="exit":
                    self.log("Exit requested. Closing...")
                    self.is_exiting.set()
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
                for bot_instance in self.bot_list:
                    bot_instance.STOP()
                while self.bots_running()>0:
                    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
                continue_processing=False

        self.log("User console exiting...")
        self.active_UI_signaller.send("detach_console",{})
        self.active_UI_signaller.send("close",{})
        self.has_quit.set()
        return


class User_Entry(object):
    def __init__(self,from_string):
        segments=[]

        try:
            segments=from_string.split("|")
            for i in range(len(segments)):
                segments[i]=segments[i].strip()
        
            if len(segments)==1:
                raise ValueError("Home path was not present.")
            if len(segments)>2:
                raise ValueError("Wrong number of \"|\"-separated characters.")

            self.username=segments[0]
            self.home=segments[1]
            self.allow_write=False

            if self.username.count("#")!=2 and self.username.count("#")!=0:
                raise ValueError("Username contained an incorrect number of \"#\" characters.")

            if self.username=="##" or self.username=="":
                raise ValueError("Username was empty.")

            if len(self.home)>0:
                if self.home[0]==">":
                    self.allow_write=True
                    self.home=self.home[1:]
            if self.home=="":
                raise ValueError("Home path was empty.")
        except:
            self.log("m","WARNING: User list \""+from_string+"\" was not validly formatted: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
            self.username=""
            self.home=""
            self.allow_write=False
        return


class UI(object):
    def __init__(self,input_signaller,input_logger=None):
        self.active_logger=input_logger
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

    def UI_thread_launcher(self):
        self.UI_APP=0
        self.UI_APP=QApplication([])
        self.UI_APP.setStyle("fusion")
        self.UI_window=Main_Window(self.is_ready,self.is_exiting,self.has_quit,self.UI_signaller,self.active_logger)
        self.UI_window.show()
        self.UI_APP.aboutToQuit.connect(self.UI_APP.deleteLater)
        self.UI_window.raise_()
        self.UI_window.activateWindow()
        sys.exit(self.UI_APP.exec_())
        return

    def IS_RUNNING(self):
        return self.has_quit.is_set()==False

    def IS_READY(self):
        return self.is_ready.is_set()==True


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
    def __init__(self,input_is_ready,input_is_exiting,input_has_quit,input_signaller,input_logger=None):
        global __author__
        global __version__
        global APP_ICONS_B64
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
            self.font_cache[fontname].setPointSize(FONT_POINT_SIZE*FONTS[fontname]["size"]*CUSTOM_UI_SCALING)
            for fontproperty in FONTS[fontname]["properties"]:
                if fontproperty=="bold":
                    self.font_cache[fontname].setBold(True)
                if fontproperty=="italic":
                    self.font_cache[fontname].setItalic(True)
                if fontproperty=="underline":
                    self.font_cache[fontname].setUnderline(True)
                if fontproperty=="strikeout":
                    self.font_cache[fontname].setStrikeOut(True)

        self.setFixedSize(900*UI_SCALE,618*UI_SCALE)
        self.setWindowTitle("FileBot   v"+str(__version__)+"   by "+str(__author__))

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
        self.last_clipboard_selection_time=GetTickCount64()
        self.last_log_update_time=GetTickCount64()

        self.icon_cache={}
        for iconname in APP_ICONS_B64:
            icon_qba=QByteArray.fromBase64(APP_ICONS_B64[iconname])
            icon_qimg=QImage.fromData(icon_qba,"PNG")
            icon_qpix=QPixmap.fromImage(icon_qimg)
            self.icon_cache[iconname]=QIcon(icon_qpix)

        self.setWindowIcon(self.icon_cache["default"])

        self.tray_current_state="deactivated"
        self.tray_current_text="FileBot"
        self.tray_icon=QSystemTrayIcon(self.icon_cache[self.tray_current_state],self)
        self.tray_icon.setVisible(True)
        self.tray_icon.show()

        self.timer_update_output=QTimer(self)
        self.timer_update_output.timeout.connect(self.update_output)
        self.timer_update_output.setSingleShot(True)

        self.timer_close=QTimer(self)
        self.timer_close.timeout.connect(self.close)
        self.timer_close.setSingleShot(True)

        self.timer_clipboard=QTimer(self)
        self.timer_clipboard.timeout.connect(self.clipboard_insert)
        self.timer_clipboard.setSingleShot(True)

        self.options_macros={}
        self.tray_menu=QMenu(self)
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
        self.label_botname.setStyleSheet("QGroupBox {background-color:#F0F0FF;}")

        self.label_botname=QLabel(self)
        self.label_botname.setText("Bot name:")
        self.label_botname.setGeometry(22*UI_SCALE,12*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botname.setFont(self.font_cache["general"])
        self.label_botname.setAlignment(Qt.AlignLeft)

        self.label_botname_value=QLabel(self)
        self.label_botname_value.setGeometry(75*UI_SCALE,12*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botname_value.setFont(self.font_cache["status"])
        self.label_botname_value.setText("<not retrieved>")
        self.label_botname_value.setAlignment(Qt.AlignLeft)

        self.label_botstatus=QLabel(self)
        self.label_botstatus.setText("Status:")
        self.label_botstatus.setGeometry(372*UI_SCALE,12*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botstatus.setFont(self.font_cache["general"])
        self.label_botstatus.setAlignment(Qt.AlignLeft)

        self.label_botstatus_value=QLabel(self)
        self.label_botstatus_value.setGeometry(410*UI_SCALE,12*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_botstatus_value.setFont(self.font_cache["status"])
        self.label_botstatus_value.setText("NOT STARTED")
        self.label_botstatus_value.setAlignment(Qt.AlignLeft)

        self.label_clock_bias=QLabel(self)
        self.label_clock_bias.setText("Local machine clock bias(seconds):")
        self.label_clock_bias.setGeometry(620*UI_SCALE,12*UI_SCALE,300*UI_SCALE,26*UI_SCALE)
        self.label_clock_bias.setFont(self.font_cache["general"])
        self.label_clock_bias.setAlignment(Qt.AlignLeft)

        self.label_clock_bias_value=QLabel(self)
        self.label_clock_bias_value.setGeometry(800*UI_SCALE,12*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_clock_bias_value.setFont(self.font_cache["status"])
        self.label_clock_bias_value.setText("UNKNOWN")
        self.label_clock_bias_value.setAlignment(Qt.AlignLeft)

        self.textbox_output=QListView(self)
        self.textbox_output.setModel(QStringListModel(self))
        self.textbox_output.setFont(self.font_cache["log"])
        self.textbox_output.setGeometry(20*UI_SCALE,32*UI_SCALE,860*UI_SCALE,524*UI_SCALE)
        self.textbox_output.setStyleSheet("QListView::enabled {background-color:#000000; color:#FFFFFF;} QListView::disabled {background-color:#808080; color:#000000;}")
        self.textbox_output.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn);
        self.textbox_output.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);
        self.textbox_output.setAcceptDrops(False)
        self.textbox_output.setToolTip(None)
        self.textbox_output.setWordWrap(True)
        self.textbox_output.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.textbox_output.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.textbox_output.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.textbox_output.setFrameStyle(QFrame.NoFrame)
        self.textbox_output.setToolTipDuration(0)
        self.textbox_output.setDragEnabled(False)
        self.textbox_output.verticalScrollBar().setStyleSheet("QScrollBar:vertical {border:"+str(int(1*UI_SCALE))+"px solid #CDCDCD; color:#000000; background-color:#CDCDCD; width:"+str(int(15*UI_SCALE))+"px;} QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background-color:#DBDBDB}")
        self.textbox_output.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.textbox_output.installEventFilter(self)

        self.label_commands=QLabel(self)
        self.label_commands.setText("INPUT COMMANDS:")
        self.label_commands.setGeometry(390*UI_SCALE,565*UI_SCALE,120*UI_SCALE,26*UI_SCALE)
        self.label_commands.setFont(self.font_cache["general"])
        self.label_commands.setAlignment(Qt.AlignLeft)

        self.input_commandfield=QLineEdit(self)
        self.input_commandfield.setGeometry(20*UI_SCALE,580*UI_SCALE,860*UI_SCALE,24*UI_SCALE)
        self.input_commandfield.setFont(self.font_cache["log"])
        self.input_commandfield.setMaxLength(512)
        self.input_commandfield.setAcceptDrops(False)
        self.input_commandfield.returnPressed.connect(self.input_commandfield_onsend)
        self.input_commandfield.installEventFilter(self)
        self.input_commandfield.setStyleSheet("QLineEdit::enabled {background-color:#000000; color:#00FF00;} QLineEdit::disabled {background-color:#808080; color:#000000;}")

        self.set_UI_lock(True)
        self.update_UI_usability()
        self.update_tray_icon()

        input_is_ready.set()
        return

    def log(self,input_text):
        if self.active_logger is not None:
            self.active_logger.LOG("GUINTRFC",input_text)
        return

    def clipboard_insert(self):
        global CLIPBOARD_COPY_TIMEOUT_SECONDS

        if self.is_exiting.is_set()==True:
            return

        self.lock_clipboard.acquire()
        start_time=GetTickCount64()
        while self.active_clipboard.text()!=self.clipboard_queue and (GetTickCount64()-start_time)/1000.0<CLIPBOARD_COPY_TIMEOUT_SECONDS:
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
        global CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS

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
                        if (GetTickCount64()-self.last_clipboard_selection_time)/1000.0>CLIPBOARD_COPY_MAX_REPEAT_INTERVAL_SECONDS:
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
        global LOG_UPDATE_INTERVAL_SECONDS

        if self.log_is_updating==False:
            self.log_is_updating=True
            self.timer_update_output.start(max(0,self.last_log_update_time+LOG_UPDATE_INTERVAL_SECONDS*1000.0-GetTickCount64()))
        return

    def update_output(self):
        global OUTPUT_ENTRIES_MAX

        if self.is_exiting.is_set()==True:
            return

        self.lock_log_queue.acquire()
        get_output_queue=self.output_queue[:]
        self.output_queue=[]
        self.lock_log_queue.release()
        get_output_queue_len=len(get_output_queue)
        cache_model=self.textbox_output.model()

        self.lock_output_update.acquire()

        rows_to_delete=max(0,cache_model.rowCount()+get_output_queue_len-OUTPUT_ENTRIES_MAX)
        starting_row=cache_model.rowCount()-rows_to_delete
        index=-1

        self.textbox_output.setUpdatesEnabled(False)
        cache_model.removeRows(0,rows_to_delete)
        cache_model.insertRows(starting_row,get_output_queue_len)
        for line in get_output_queue:
            index+=1
            cache_model.setItemData(cache_model.index(starting_row+index),{0:line})
        self.textbox_output.scrollToBottom()
        self.textbox_output.setUpdatesEnabled(True)
        self.last_log_update_time=GetTickCount64()
        self.log_is_updating=False

        self.lock_output_update.release()

        return

    def update_tray_icon(self):
        tray_text_new=self.label_botname_value.text()
        if tray_text_new!="<not retrieved>":
            tray_text_new="FileBot running bot \""+tray_text_new+"\""

        tray_candidate="default"
        if self.online_state==True:
            if self.last_bots_busy_state==True:
                tray_candidate="busy"
        else:
            tray_candidate="deactivated"

        if tray_candidate=="default":
            tray_text_new+=" - ONLINE"
        elif tray_candidate=="deactivated":
            tray_text_new+=" - OFFLINE"
        elif tray_candidate=="busy":
            tray_text_new+=" - ONLINE (processing messages)"

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
        self.lock_log_queue.acquire()
        self.output_queue+=[input_line]
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
            self.label_botname_value.setStyleSheet("QLabel {color: #000099}")
            self.update_tray_icon()

        elif event_type=="status":
            self.label_botstatus_value.setText(event_data)
            if event_data=="ONLINE":
                self.label_botstatus_value.setStyleSheet("QLabel {color: #009900}")
                self.online_state=True
                self.update_tray_icon()
            elif event_data=="OFFLINE":
                self.label_botstatus_value.setStyleSheet("QLabel {color: #990000}")
                self.online_state=False
                self.update_tray_icon()

        elif event_type=="clock_bias":
            self.label_clock_bias_value.setText(event_data)
            get_number=float(event_data.replace("+","").replace("-",""))
            self.label_clock_bias_value.setStyleSheet("QLabel {color: #009900}")
            if get_number>=30:
                self.label_clock_bias_value.setStyleSheet("QLabel {color: #999900}")
            if get_number>=60:
                self.label_clock_bias_value.setStyleSheet("QLabel {color: #990000}")

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


warnings.filterwarnings("ignore",category=UserWarning,module="urllib2")
TIME_DELTA_LOCK=threading.Lock()

environment_info=get_run_environment()
qInstallMessageHandler(qtmsg_handler)

LOGGER=Logger(os.path.join(environment_info["working_dir"],"log.txt"))
LOGGER.START()

UI_SIGNAL=UI_Signaller()
LOGGER.ATTACH_SIGNALLER(UI_SIGNAL)
Active_UI=UI(UI_SIGNAL,LOGGER)

while Active_UI.IS_READY()==False:
    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

log("============================ FileBot ============================")
log("Author: "+str(__author__))
log("Version: "+str(__version__))
log("=================================================================")
log("\n\nRequirements:\n-bot token in \"token.txt\"\n"+
"-users list in \"userlist.txt\" with one entry per line, formatted as such: <USERNAME>|<HOME PATH>\n\n"+
"Begin home path with \">\" to allow writing. To allow access to all drives, set the path to \"*\".\n"+
"If a user has no username, you can add them via first name and last name with a \"#\" before each. Example:\n"+
"FIRST NAME: John LAST NAME: Doe -> #John#Doe\n"+
"Note that this method only works if the user has no username, and that a \"#\" is required even if the last name is empty.\n")

PATH_7ZIP=environment_info["working_dir"]
CURRENT_PROCESS_HANDLE=win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,True,environment_info["process_id"])
TELEGRAM_SERVER_TIMER_DELTA=-1

log("Process ID is "+str(environment_info["process_id"])+".")

fatal_error=False
collect_api_token=""

try:
    file_handle=open(os.path.join(environment_info["working_dir"],"token.txt"),"r")
    collect_api_token=file_handle.readline()
    file_handle.close()
except:
    log("ERROR: Make sure the file \"token.txt\" exists and contains the bot token.")
    fatal_error=True

if len(collect_api_token)==0 and fatal_error==False:
    log("ERROR: Make sure the token is correctly written in \"token.txt\".")
    fatal_error=True

collect_allowed_senders=[]

if fatal_error==False:
    file_entries=[]
    try:
        file_handle=open(os.path.join(environment_info["working_dir"],"userlist.txt"),"r")
        file_entries=file_handle.readlines()
        for entry in file_entries:
            if entry.strip()!="":
                collect_allowed_senders.append(User_Entry(entry.strip()))
    except:
        log("ERROR: Could not read entries from \"userlist.txt\".")
        fatal_error=True
    file_entries=[]

for i in reversed(range(len(collect_allowed_senders))):
    if collect_allowed_senders[i].username=="":
        del collect_allowed_senders[i]

if fatal_error==False:
    log("Number of users to listen for: "+str(len(collect_allowed_senders))+".")
    if len(collect_allowed_senders)==0:
        log("ERROR: There were no valid user lists to add.")
        fatal_error=True

if fatal_error==False:
    if os.path.isfile(os.path.join(environment_info["working_dir"],"7z.exe"))==False or os.path.isfile(os.path.join(environment_info["working_dir"],"7z.dll"))==False:
        log("7-ZIP files are missing. Files \"7z.exe\" and \"7z.dll\" must both be present in FileBot's folder.")
        fatal_error=True

if fatal_error==False:

    log("Obtaining local machine clock bias info...")
    time_synced=False
    while time_synced==False and Active_UI.IS_RUNNING()==True:
        time_synced=Perform_Time_Sync(UI_SIGNAL)

    if time_synced==True:
        UserHandleInstances=[]

        collect_allowed_usernames=[]
        for sender in collect_allowed_senders:
            collect_allowed_usernames.append(sender.username)

        ListenerService=Message_Listener(collect_api_token,collect_allowed_usernames,UI_SIGNAL,LOGGER)
        log("Starting Listener...")
        ListenerService.START()

        while ListenerService.IS_READY()==False and Active_UI.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

        if Active_UI.IS_RUNNING()==True:

            log("User message handler(s) starting up...")

            for sender in collect_allowed_senders:
                UserHandleInstances.append(User_Message_Handler(collect_api_token,sender.home,sender.username,sender.allow_write,ListenerService,LOGGER))

            request_sync_time=threading.Event()
            request_sync_time.clear()

            Command_Console=User_Console(UserHandleInstances,UI_SIGNAL,request_sync_time,LOGGER)
            log("Starting Console...")
            Command_Console.START()

            log("Startup complete. Waiting for secondary threads to finish...")

            process_total_time=PRIORITY_RECHECK_INTERVAL_SECONDS
            last_server_time_check=time.time()

            while Active_UI.IS_RUNNING()==True:

                time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)

                sys.stdout.flush()
                sys.stderr.flush()

                process_total_time+=MAINTHREAD_HEARTBEAT_SECONDS
                if process_total_time>=PRIORITY_RECHECK_INTERVAL_SECONDS:
                    process_total_time-=PRIORITY_RECHECK_INTERVAL_SECONDS
                    set_process_priority_idle()

                if abs(time.time()-last_server_time_check)>=SERVER_TIME_RESYNC_INTERVAL_SECONDS or request_sync_time.is_set()==True:
                    time_sync_result=Perform_Time_Sync(UI_SIGNAL)
                    if request_sync_time.is_set()==True:
                        request_sync_time.clear()
                        if time_sync_result==True:
                            last_server_time_check=time.time()
                    else:
                        request_sync_time.clear()
                        last_server_time_check=time.time()

            log("Left thread waiting loop.")

            ListenerService.STOP()
            Command_Console.STOP()

            while Command_Console.IS_RUNNING()==True:
                time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
            Command_Console.working_thread.join()
            del Command_Console
            log("Confirm Console exit.")
        else:
            ListenerService.STOP()

        while ListenerService.IS_RUNNING()==True:
            time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
        ListenerService.working_thread.join()
        del ListenerService
        log("Confirm Listener exit.")

        while len(UserHandleInstances)>0:
            UserHandleInstances[0].working_thread.join()
            del UserHandleInstances[0]
        log("Confirm Message Handler(s) exit.")

else:

    UI_SIGNAL.send("close_standby")

LOGGER.DETACH_SIGNALLER()
Active_UI.working_thread.join()
del Active_UI
log("Confirm UI exit.")

log("Main thread exit; program has finished.")
LOGGER.STOP()
