__version__="1.31"


"""
INIT
"""


import os
import ctypes
import sys
import time
import datetime
import threading
import warnings
import telepot
import subprocess
import msvcrt
import win32api
import win32con
import win32process
import _winreg
import urllib2

PENDING_ACTIVITY_HEARTBEAT_SECONDS=0.2
MAINTHREAD_HEARTBEAT_SECONDS=0.04
SCREEN_OUTPUT_REFRESH_RATE_SECONDS=0.05
REPORT_OUTPUT_REFRESH_INTERVAL_SECONDS=0.9
PRIORITY_RECHECK_INTERVAL_SECONDS=60
COMMAND_CHECK_INTERVAL_SECONDS=0.2
CONSOLE_INPUT_KEY_READ_POLLING_SECONDS=0.02
SERVER_TIME_RESYNC_INTERVAL_SECONDS=60*60*8
LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS=0.8
USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS=0.2

BOTS_MAX_ALLOWED_FILESIZE_BYTES=1024*1024*50
MAX_IM_SIZE_BYTES=4096

WINDOW_ROWS=58
WINDOW_COLS=130

TITLEBAR_Y=1
TITLEBAR_BOTNAME_X=2
TITLEBAR_TIMEDIFF_X=86
TITLEBAR_ONLINESTATUS_X=58

COMMAND_BOX_TITLE="INPUT COMMANDS:"
REPORT_X=1
REPORT_WIDTH=WINDOW_COLS-REPORT_X*2
REPORT_Y=3
REPORT_HEIGHT=WINDOW_ROWS-REPORT_Y-4

INPUT_FIELD_X=1
INPUT_FIELD_Y=WINDOW_ROWS-2
INPUT_FIELD_LENGTH=WINDOW_COLS-2

COLOR_WINDOW_TX=15
COLOR_WINDOW_BG=4
COLOR_FRAME_TX=14
COLOR_TITLEBAR_TX=15

COLOR_REPORT_TX=15
COLOR_REPORT_BG=1

COLOR_COMMAND_TX=10
COLOR_COMMAND_BG=0
COLOR_COMMAND_TITLE_TX=15


"""
DEFS
"""


class _CursorInfo(ctypes.Structure):
    _fields_=[("size",ctypes.c_int),("visible",ctypes.c_byte)]
                    
def cursor_visibility(state):
    global WINDOW_HANDLE
    ci=_CursorInfo()
    ctypes.windll.kernel32.GetConsoleCursorInfo(WINDOW_HANDLE,ctypes.byref(ci))
    ci.visible=state
    ctypes.windll.kernel32.SetConsoleCursorInfo(WINDOW_HANDLE,ctypes.byref(ci))
    return

def console_setup():
    global COLOR_WINDOW_TX
    global COLOR_WINDOW_BG
    global WINDOW_ROWS
    global WINDOW_COLS
    global WINDOW_HANDLE

    OUTPUT_ROW_BUFFER=WINDOW_ROWS

    os.system("@title FileBot v"+__version__)
    os.system("color "+str(hex(COLOR_WINDOW_TX+COLOR_WINDOW_BG*16))[2:])
    os.popen("mode con: lines="+str(WINDOW_ROWS)+" cols="+str(WINDOW_COLS))
    WINDOW_HANDLE=ctypes.windll.kernel32.GetStdHandle(-12)
    ctypes.windll.kernel32.SetConsoleScreenBufferSize(WINDOW_HANDLE,OUTPUT_ROW_BUFFER*(2**16)+WINDOW_COLS)
    cursor_visibility(False)
    return

def report(source,input_data=""):
    global LOG_LOCK

    if input_data!="":
        source_literal=str(source)
        input_literal=str(input_data)
    else:
        source_literal=""
        input_literal=str(source)
    source_literal=source_literal.lower().strip()
    if len(source_literal)>0:
        source_literal=source_literal[0]
    if source_literal=="w":
        source_literal="MSGHNDLR"
    elif source_literal=="u":
        source_literal="MSGHDMGR"
    elif source_literal=="c":
        source_literal="UCONSOLE"
    elif source_literal=="m":
        source_literal="MAINTHRD"
    elif source_literal=="l":
        source_literal="LSTNSRVC"
    elif source_literal=="o":
        source_literal="LSRVCMGR"
    if source_literal!="":
        source_literal=" ["+source_literal+"] "
    else:
        source_literal=" "
    msg=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+source_literal+input_literal+"\n"

    add_report_out_text(msg)

    LOG_LOCK.acquire()

    try:
        log_handle=open("log.txt","a")
        log_handle.write(msg)
        log_handle.close()
    except:
        pass

    LOG_LOCK.release()
    return

def add_report_out_text(msg):
    global LOCK_SCREEN_REPORT
    global SCREEN_REPORT_LINES
    global SCREEN_REPORT_EDITED
    global REPORT_HEIGHT

    LOCK_SCREEN_REPORT.acquire()
    SCREEN_REPORT_LINES+=[msg]
    if len(SCREEN_REPORT_LINES)>REPORT_HEIGHT:
        del SCREEN_REPORT_LINES[0]
    SCREEN_REPORT_EDITED=True
    LOCK_SCREEN_REPORT.release()

    return

def OS_uptime():
    return ctypes.windll.kernel32.GetTickCount64()/1000.0
    
def Current_UTC_Internet_Time():
    response=urllib2.urlopen("http://time.gov/actualtime.cgi")
    timestr=response.read()
    quot1=timestr.find("time=\"")
    quot1+=len("time=\"")
    quot2=quot1+timestr[quot1+1:].find("\"")
    quot2+=1
    return int(timestr[quot1:quot2-3])/1000.0

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

def chunkalize(input_string,chunksize):
    retval=[]
    start=0
    while start<len(input_string):
        end=start+min(chunksize,len(input_string)-start)
        retval.append(input_string[start:end])
        start=end
    return retval

def readable_size(input_size):
    if input_size<1024:
        return str(input_size)+" Bytes"
    if input_size<1024**2:
        return str(round(input_size/1024.0,2))+" KB"
    if input_size<1024**3:
        return str(round(input_size/1024.0**2,2))+" MB"
    if input_size<1024**4:
        return str(round(input_size/1024.0**3,2))+" GB"

def folder_list_string(input_folder,search_in,folders_only=False):
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

        for i in folderlist:
            response+="\n"+i

        if len(folderlist)>0:
            response+="\n\n"

        if len(filelist)>0:
            response+="<FILES:>\n"

        for i in filelist:
            response+="\n"+i
    except:
        response="<Bad dir path.>"

    return response

class listener_object(object):
    def __init__(self,input_token,username_list):
        self.token=input_token
        self.keep_running=threading.Event()
        self.keep_running.clear()
        self.has_exited=threading.Event()
        self.has_exited.set()
        self.is_active=threading.Event()
        self.is_active.clear()
        self.last_ID_checked=-1
        self.start_time=0
        self.listen_thread=threading.Thread(target=self.listen_thread_work)
        self.listen_thread.daemon=True
        self.listen_users=username_list
        self.messagelist_lock={}
        for i in self.listen_users:
            self.messagelist_lock[i]=threading.Lock()
        self.user_messages={}
        for i in self.listen_users:
            self.user_messages[i]=[]
        return

    def START(self):
        report("o","Listener service start issued.")
        self.has_exited.clear()
        self.keep_running.set()
        self.listen_thread.start()
        
    def STOP(self):
        report("o","Listener service stop issued.")
        self.keep_running.clear()
        return
    
    def IS_RUNNING(self):
        return self.has_exited.is_set()==False
        
    def ACTIVE(self):
        return self.is_active.is_set()==True

    def listen_thread_work(self):
        self.bot_handle=telepot.Bot(self.token)
        last_check_status=False
        bot_bind_ok=False
        activation_fail_announce=False

        while bot_bind_ok==False:
            try:
                self.name=self.bot_handle.getMe()[u"username"]
                bot_bind_ok=True
            except:
                if activation_fail_announce==False:
                    report("l","Listener service activation error. Will keep trying...")
                    activation_fail_announce=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)

        self.catch_up_IDs()
        os.system("@title FileBot v"+__version__+" - "+self.name)
        set_general_data("bot_name",self.name)
        report("l","Listener service for bot \""+self.name+"\" is now active.")
        self.is_active.set()

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
                    set_general_data("online","yes")
                    report("l","Message retrieval is now online.")
                else:
                    set_general_data("online","no")
                    report("l","Stopped being able to retrieve messages.")

            self.organize_messages(response)

        self.is_active.clear()
        report("l","Listener has exited.")
        self.has_exited.set()
        return

    def catch_up_IDs(self):
        retrieved=False
        responses=[]
        announced_fail=False
        while retrieved==False:
            try:
                responses=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                retrieved=True
                report("l","Caught up with messages.")
            except:
                if announced_fail==False:
                    report("l","Failed to catch up with messages. Will keep trying...")
                    announced_fail=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=server_time()
        return

    def organize_messages(self,input_msglist):
        collect_new_messages={}
        for i in self.listen_users:
            collect_new_messages[i]=[]

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

        for i in collect_new_messages:
            self.messagelist_lock[i].acquire()
            if len(collect_new_messages[i])>0:
                self.user_messages[i]+=collect_new_messages[i]
            for j in reversed(range(len(self.user_messages[i]))):
                if server_time()-self.user_messages[i][j][u"date"]>30:
                    del self.user_messages[i][j]
            self.messagelist_lock[i].release()
        return

    def consume_user_messages(self,input_username):
        self.messagelist_lock[input_username].acquire()
        get_messages=self.user_messages[input_username]
        self.user_messages[input_username]=[]
        self.messagelist_lock[input_username].release()
        return get_messages

class user_message_handler(object):
    def __init__(self,input_token,input_root,input_user,input_write,input_listener_service):
        self.bot_thread=threading.Thread(target=self.message_handler_thread_work)
        self.bot_thread.daemon=True
        self.token=input_token
        self.listener=input_listener_service
        self.keep_running=threading.Event()
        self.keep_running.clear()
        self.bot_has_exited=threading.Event()
        self.bot_has_exited.set()
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
            for i in range(excess_entries):
                del self.lastsent_timers[0]
            return True
        except:
            report("w","<"+self.allowed_user+"> "+"Message handler was unable to respond.")
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
            self.bot_lock_pass=""
            report("w","<"+self.allowed_user+"> "+"Message handler unlocked by console.")
            self.listener.consume_user_messages(self.allowed_user)
        return

    def message_handler_thread_work(self):
        self.bot_handle=telepot.Bot(self.token)
        bot_bind_ok=False
        activation_fail_announce=False
        while bot_bind_ok==False:
            try:
                self.bot_handle.getMe()[u"username"]
                bot_bind_ok=True
            except:
                if activation_fail_announce==False:
                    report("w","<"+self.allowed_user+"> "+"Message handler activation error. Will keep trying...")
                    activation_fail_announce=True
                time.sleep(LISTENER_SERVICE_THREAD_HEARTBEAT_SECONDS)

        self.listener.consume_user_messages(self.allowed_user)
        report("w","<"+self.allowed_user+"> "+"Message handler for user \""+self.allowed_user+"\" is now active.")

        while self.keep_running.is_set()==True:
            time.sleep(USER_MESSAGE_HANDLER_THREAD_HEARTBEAT_SECONDS)
            self.check_tasks()
            if self.listen_flag.is_set()==True:
                new_messages=self.listener.consume_user_messages(self.allowed_user)
                total_new_messages=len(new_messages)
                if total_new_messages>0:
                    report("w","<"+self.allowed_user+"> "+str(total_new_messages)+" new message(s) received.")
                    self.process_messages(new_messages)

        report("w","<"+self.allowed_user+"> "+"Message handler exited.")
        self.bot_has_exited.set()
        return

    def START(self):
        report("u","<"+self.allowed_user+"> "+"User message handler start issued, home path is \""+self.allowed_root+"\", allow writing: "+str(self.allow_writing).upper()+".")
        self.bot_has_exited.clear()
        self.keep_running.set()
        self.bot_thread.start()
        return

    def LISTEN(self,new_state):
        if new_state==True:
            report("u","<"+self.allowed_user+"> "+"Listen started.")
            if self.allowed_root=="*":
                self.last_folder="C:\\"
            else:
                self.last_folder=self.allowed_root
            self.listener.consume_user_messages(self.allowed_user)
            self.listen_flag.set()
        else:
            report("u","<"+self.allowed_user+"> "+"Listen stopped.")
            self.listen_flag.clear()

    def STOP(self):
        report("u","<"+self.allowed_user+"> "+"Message handler stop issued.")
        self.listen_flag.clear()
        self.keep_running.clear()
        return

    def IS_RUNNING(self):
        return self.bot_has_exited.is_set()==False

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
        if self.bot_lock_pass!="":
            return

        if self.allow_writing==False:
            return

        foldername=self.last_folder
        complete_put_path=foldername+filename
        self.sendmsg(sid,"Putting file \""+filename+"\" at \""+foldername+"\"...")
        report("w","<"+self.allowed_user+"> "+" Receiving file \""+complete_put_path+"\"...")
        if os.path.exists(complete_put_path)==False or (os.path.exists(complete_put_path)==True and os.path.isfile(complete_put_path)==False):
            try:
                self.bot_handle.download_file(fid,complete_put_path)
                self.sendmsg(sid,"Finished putting file \""+complete_put_path+"\".")
                report("w","<"+self.allowed_user+"> "+" File download complete.")
            except:
                self.sendmsg(sid,"File \""+filename+"\" could not be placed.")
                report("w","<"+self.allowed_user+"> "+" File download aborted due to unknown issue.")
        else:
            self.sendmsg(sid,"File \""+filename+"\" already exists at the location.")
            report("w","<"+self.allowed_user+"> "+" File download aborted due to existing instance.")

    def process_instructions(self,sid,msg,cid):
        global BOTS_MAX_ALLOWED_FILESIZE_BYTES
        global MAX_IM_SIZE_BYTES
        if self.bot_lock_pass!="":
            if msg.lower().find("/unlock ")==0:
                if msg[len("/unlock "):].strip()==self.bot_lock_pass:
                    self.bot_lock_pass=""
                    self.lock_status.clear()
                    self.sendmsg(sid,"Bot unlocked.")
                    report("w","<"+self.allowed_user+"> "+"Message handler unlocked by user.")
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
            report("w","<"+self.allowed_user+"> "+"Message handler start requested.")
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

            report("w","<"+self.allowed_user+"> "+"Listing requested for path \""+command_args+"\" with search string \""+extra_search+"\", folders only="+str(folders_only).upper()+".")

            if command_args=="":
                use_folder=self.last_folder
            else:
                use_folder=command_args
            use_folder=self.rel_to_abs(command_args)
            if self.allowed_path(use_folder)==True:
                dirlist=folder_list_string(use_folder,extra_search,folders_only)
            else:
                dirlist="<Bad dir path.>"
            for chunk in chunkalize(dirlist,MAX_IM_SIZE_BYTES):
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
                        self.last_folder=newpath
                        if len(self.last_folder)>0:
                            self.last_folder=self.last_folder[0].upper()+self.last_folder[1:]
                        response="Current folder changed to \""+self.last_folder+"\"."
                        report("w","<"+self.allowed_user+"> "+"Current folder changed to \""+self.last_folder+"\".")
                else:
                    response="Bad path."
            else:
                response="Current folder is \""+self.last_folder+"\"."
                report("w","<"+self.allowed_user+"> "+"Queried current folder, which is \""+self.last_folder+"\".")
        elif command_type=="get":
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","<"+self.allowed_user+"> "+"Requested get file \""+newpath+"\". Processing...")
                self.sendmsg(sid,"Getting file, please wait...")
                try:
                    fsize=os.path.getsize(newpath)
                    if fsize<=BOTS_MAX_ALLOWED_FILESIZE_BYTES and fsize!=0:
                        self.bot_handle.sendDocument(cid,open(newpath,"rb"))
                    else:
                        if fsize!=0:
                            response="Bots cannot upload files larger than "+readable_size(BOTS_MAX_ALLOWED_FILESIZE_BYTES)+"."
                            report("w","<"+self.allowed_user+"> "+"Requested file too large.")
                        else:
                            response="File is empty."
                except:
                    response="Problem getting file."
                    report("w","<"+self.allowed_user+"> "+"File send error.")
            else:
                response="File not found or inaccessible."
                report("w","<"+self.allowed_user+"> "+"File not found.")
        elif command_type=="eat" and self.allow_writing==True:
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","<"+self.allowed_user+"> "+"Requested eat file \""+newpath+"\".")
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
                    report("w","<"+self.allowed_user+"> "+"File send error.")
                if success==True:
                    try:
                        report("w","<"+self.allowed_user+"> "+"File sent. Deleting...")
                        os.remove(newpath)
                        self.sendmsg(sid,"File deleted.")
                    except:
                        response="Problem deleting file."
                        report("w","<"+self.allowed_user+"> "+"File delete error.")
                        report("w","<"+self.allowed_user+"> "+"File deleted.")
            else:
                response="File not found or inaccessible."
        elif command_type=="del" and self.allow_writing==True:
            newpath=self.rel_to_abs(command_args,True)
            if self.usable_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","<"+self.allowed_user+"> "+"Requested delete file \""+newpath+"\".")
                try:
                    os.remove(newpath)
                    self.sendmsg(sid,"File deleted.")
                except:
                    response="Problem deleting file."
                    report("w","<"+self.allowed_user+"> "+"File delete error.")
            else:
                response="File not found or inaccessible."
        elif command_type=="up":
            if self.last_folder.count("\\")>1:
                newpath=self.last_folder[:-1]
                newpath=newpath[:newpath.rfind("\\")+1]
                if self.allowed_path(newpath)==True:
                    self.last_folder=newpath
                    response="Current folder is now \""+self.last_folder+"\"."
                    report("w","<"+self.allowed_user+"> "+"Current folder changed to \""+self.last_folder+"\".")
                else:
                    response="Already at top folder."
            else:
                response="Already at top folder."
        elif command_type=="zip" and self.allow_writing==True and PATH_7ZIP!="":
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
                        report("w","<"+self.allowed_user+"> "+"Zip command issued on \""+folder_path+archive_filename+"\".")
                    else:
                        response="The archive \""+archive_filename+".7z\" already exists at the location."
                except:
                    response="Problem getting file."
                    report("w","<"+self.allowed_user+"> "+"Zip \""+command_args+"\" failed.")
            else:
                response="File not found or inaccessible."
                report("w","<"+self.allowed_user+"> "+"[BOTWRK] Zip \""+command_args+"\" file not found or inaccessible.")
        elif command_type=="lock":
            if command_args.strip()!="" and len(command_args.strip())<=32:
                self.bot_lock_pass=command_args.strip()
                response="Bot locked."
                self.lock_status.set()
                report("w","<"+self.allowed_user+"> "+"Message handler was locked down with password.")
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
                if PATH_7ZIP!="":
                    response+="/zip <PATH[FILE]>: make a 7-ZIP archive, extension will be .7z.TMP until finished\n"
            response+="/up: move up one folder from current path\n"
            response+="/get <[PATH]FILE>: retrieve the file at the location to Telegram\n"
            if self.allow_writing==True:
                response+="/eat <[PATH]FILE>: upload the file at the location to Telegram, then delete it from its original location\n"
                response+="/del <[PATH]FILE>: delete the file at the location\n"
            response+="/lock <PASSWORD>: lock the bot from responding to messages\n"
            response+="/unlock <PASSWORD>: unlock the bot\n"
            response+="\nSlashes work both ways in paths (/cd c:/windows, /cd c:\windows)"
            report("w","<"+self.allowed_user+"> "+"Help requested.")
        else:
            self.sendmsg(sid,"Command unknown. Type \"/help\" for a list of commands.")

        if response!="":
            self.sendmsg(sid,response)
        return

class user_console(object):
    def __init__(self,bot_list,key_input_source):
        self.working_thread=threading.Thread(target=self.process_input)
        self.working_thread.daemon=True
        self.bot_list=bot_list
        self.finished_work=threading.Event()
        self.active_input=key_input_source
        self.finished_work.clear()
        self.working_thread.start()
        return

    def IS_DONE(self):
        return self.finished_work.is_set()==True

    def bots_running(self):
        total=0
        for i in self.bot_list:
            if i.IS_RUNNING()==True:
                total+=1
        return total

    def process_command(self,user_input):
        user_data=user_input.strip().split(" ")
        input_command=user_data[0].lower().strip()
        if len(user_data)>1:
            input_argument=user_data[1].strip()
        else:
            input_argument=""
            
        if input_command=="start":
            for i in self.bot_list:
                if i.allowed_user.lower()==input_argument or input_argument=="":
                    i.LISTEN(True)
        elif input_command=="stop":
            for i in self.bot_list:
                if i.allowed_user.lower()==input_argument or input_argument=="":
                    i.LISTEN(False)
        elif input_command=="stats":
            for i in self.bot_list:
                if i.allowed_user.lower()==input_argument or input_argument=="":
                    report("c","Message handler for user \""+i.allowed_user+"\":\nHome path=\""+i.allowed_root+"\"\nWrite mode: "+str(i.allow_writing).upper()+"\nLocked: "+str(i.lock_status.is_set()).upper()+"\nListening: "+str(i.listen_flag.is_set()).upper()+"\n\n")
        elif input_command=="list":
            list_out=""
            for i in self.bot_list:
                list_out+=i.allowed_user+", "
            list_out=list_out[:-2]+"."
            report("c","Allowed user(s): "+list_out)
        elif input_command=="unlock":
            for i in self.bot_list:
                if i.allowed_user.lower()==input_argument or input_argument=="":
                    i.pending_lockclear.set()
        elif input_command=="sync":
            report("c","Manual Internet time synchronization requested...")
            if Sync_Server_Time():
                get_time_diff=local_machine_time_delta_str()
                set_general_data("time_difference",get_time_diff)
                report("c","Manual Internet time synchronization successful. Local clock bias is "+get_time_diff+" second(s).")
            else:
                report("c","Time sync failed.")
        elif input_command=="help":
            report("c","AVAILABLE CONSOLE COMMANDS:\n")
            report("c","start [USER]: start listening to messages for user; leave blank to apply to all instances")
            report("c","stop [USER]: stop listening to messages for user; leave blank to apply to all instances")
            report("c","unlock [USER]: unlock the bot for user; leave blank to apply to all instances")
            report("c","stats [USER]: list bot stats; leave blank to list all instances")
            report("c","list: lists allowed users")
            report("c","sync: manually re-synchronize bot time with Internet time")
            report("c","help: display help\n")
        else:
            report("c","Unrecognized command. Type \"help\" for a list of commands.")
        return

    def process_input(self):
        global COMMAND_CHECK_INTERVAL_SECONDS

        loop_input=True
        for i in self.bot_list:
            i.START()
            i.LISTEN(True)
        report("c","User console activated.")
        report("c","Type \"help\" in the console for available commands.")
        while loop_input==True:
            command=self.active_input.get_console_input(True)["command"]
            if command!="":
                if command.lower().strip()=="exit" or self.bots_running()==0:
                    loop_input=False
                    self.active_input.STOP()
                    for i in self.bot_list:
                        i.STOP()
                    while self.bots_running()>0 or self.active_input.exit_complete.is_set()==False:
                        time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
                    self.finished_work.set()
                else:
                    self.process_command(command)
            time.sleep(COMMAND_CHECK_INTERVAL_SECONDS)
        return

class user_entry(object):
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
            report("m","WARNING: User list \""+from_string+"\" was not validly formatted: "+str(sys.exc_info()[0])+" "+str(sys.exc_info()[1]))
            self.username=""
            self.home=""
            self.allow_write=False
        return

def clear_key():
    while msvcrt.kbhit()!=0:
        msvcrt.getch()
    return

def get_key():
    retval=[0,0]
    if msvcrt.kbhit()!=0:
        retval[0]=ord(msvcrt.getch())
        if msvcrt.kbhit()!=0:
            retval[1]=ord(msvcrt.getch())
    if retval[0]==224:
        if retval[1]!=0:
            retval[0]=0
    return retval

def wait_for_enter():
    last_val=[0,0]
    clear_key()
    while not (last_val[1]==0 and (last_val[0]==10 or last_val[0]==13)):
        last_val=get_key()
        time.sleep(0.05)
    return

class Console_Input(object):
    def __init__(self,input_length):
        self.exit_requested=threading.Event()
        self.exit_requested.clear()
        self.OUT_LOCK=threading.Lock()
        self.current_command=""
        self.current_input=""
        self.max_length=input_length
        self.exit_complete=threading.Event()
        self.exit_complete.clear()
        self.working_thread=threading.Thread(target=self.update_loop)
        self.working_thread.daemon=True
        self.working_thread.start()
        return

    def update_loop(self):
        global CONSOLE_INPUT_KEY_READ_POLLING_SECONDS

        clear_key()

        while self.exit_requested.is_set()==False:
            self.OUT_LOCK.acquire()
            if self.current_command=="":
                key_pressed=get_key()
                if key_pressed[0]+key_pressed[1]>0:
                    if key_pressed[0]!=0 and key_pressed[1]==0:
                        if key_pressed[0]==13 or key_pressed[0]==10:
                            if len(self.current_input)>0:
                                self.current_command=self.current_input
                        elif key_pressed[0]==8:
                            if len(self.current_input)>0:
                                self.current_input=self.current_input[:-1]
                        else:
                            if len(self.current_input)<self.max_length:
                                self.current_input+=chr(key_pressed[0])
            self.OUT_LOCK.release()
            time.sleep(CONSOLE_INPUT_KEY_READ_POLLING_SECONDS)

        self.exit_complete.set()
        return

    def get_console_input(self,clear=False):
        retval={"input":"","command":""}

        self.OUT_LOCK.acquire()
        retval["command"]=self.current_command
        retval["input"]=self.current_input
        if clear==True:
            if self.current_command!="":
                self.current_command=""
                self.current_input=""
        self.OUT_LOCK.release()

        return retval

    def STOP(self):
        self.OUT_LOCK.acquire()
        self.current_command=""
        self.current_input=""
        self.OUT_LOCK.release()
        self.exit_requested.set()
        return

def move_cursor(x,y):
    global WINDOW_HANDLE
    ctypes.windll.kernel32.SetConsoleCursorPosition(WINDOW_HANDLE,y*(2**16)+x)
    return

def cursor_color(tx,bg):
    global WINDOW_HANDLE
    ctypes.windll.kernel32.SetConsoleTextAttribute(WINDOW_HANDLE,bg*16+tx)
    return

def flat_coords(x,y):
    global WINDOW_ROWS_RANGE
    return x+WINDOW_COLS*y

class Screen_Manager(object):
    def __init__(self,console_handle):
        global WINDOW_ROWS
        global WINDOW_COLS
        global COLOR_REPORT_TX
        global COLOR_REPORT_BG
        global WINDOW_ROWS_RANGE
        global WINDOW_COLS_RANGE

        self.exit_requested=threading.Event()
        self.exit_requested.clear()
        self.screenbuffer_current=[{"col_tx":0,"col_bg":COLOR_WINDOW_BG,"char":32} for i in range(WINDOW_ROWS*WINDOW_COLS)]
        self.screenbuffer_last=[{"col_tx":0,"col_bg":COLOR_WINDOW_BG,"char":32} for i in range(WINDOW_ROWS*WINDOW_COLS)]
        self.exit_complete=threading.Event()
        self.exit_complete.clear()
        self.active_console=console_handle
        self.screen_init()
        self.last_input_field="\n"
        self.last_report_refresh_time=0
        self.working_thread=threading.Thread(target=self.refresh_loop)
        self.working_thread.daemon=True
        self.working_thread.start()
        return

    def out_pos_color_txt(self,x,y,tx,bg,txt):
        for i in range(len(txt)):
            self.screenbuffer_current[flat_coords((x+i)%WINDOW_COLS,y+int((x+i)/WINDOW_COLS))]["col_tx"]=tx
            self.screenbuffer_current[flat_coords((x+i)%WINDOW_COLS,y+int((x+i)/WINDOW_COLS))]["col_bg"]=bg
            self.screenbuffer_current[flat_coords((x+i)%WINDOW_COLS,y+int((x+i)/WINDOW_COLS))]["char"]=ord(txt[i])
        return

    def screen_init(self):
        global COLOR_FRAME_TX
        global REPORT_X
        global REPORT_Y
        global REPORT_WIDTH
        global REPORT_HEIGHT
        global COLOR_WINDOW_BG
        global COLOR_REPORT_TX
        global COLOR_REPORT_BG
        global WINDOW_COLS
        global COMMAND_BOX_TITLE
        global COLOR_COMMAND_TITLE_TX
        global REPORT_WIDTH_RANGE
        global TITLEBAR_ONLINESTATUS_X
        global TITLEBAR_TIMEDIFF_X
        global TITLEBAR_BOTNAME_X
        global COLOR_TITLEBAR_TX
        global COLOR_TITLEBAR_BG

        title="FileBot v"+__version__+" by Searinox Navras"
        self.out_pos_color_txt(WINDOW_COLS/2-len(title)/2,0,14,COLOR_WINDOW_BG,title)
        self.out_pos_color_txt(TITLEBAR_BOTNAME_X,TITLEBAR_Y,COLOR_TITLEBAR_TX,COLOR_WINDOW_BG,"Bot name: <not retrieved>")
        self.out_pos_color_txt(TITLEBAR_TIMEDIFF_X,TITLEBAR_Y,COLOR_TITLEBAR_TX,COLOR_WINDOW_BG,"Local clock bias(seconds): UNKNOWN")
        self.out_pos_color_txt(TITLEBAR_ONLINESTATUS_X,TITLEBAR_Y,COLOR_TITLEBAR_TX,COLOR_WINDOW_BG,"Status: NOT STARTED")

        for i in REPORT_WIDTH_RANGE:
            self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y-1)]["col_tx"]=14
            self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y-1)]["char"]=205
            self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y+REPORT_HEIGHT)]["col_tx"]=14
            self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y+REPORT_HEIGHT)]["char"]=205

        for i in range(REPORT_HEIGHT):
            self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y+i)]["col_tx"]=14
            self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y+i)]["char"]=186
            self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y+i)]["col_tx"]=14
            self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y+i)]["char"]=186

        self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y-1)]["col_tx"]=14
        self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y-1)]["char"]=201

        self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y-1)]["col_tx"]=14
        self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y-1)]["char"]=187

        self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y+REPORT_HEIGHT)]["col_tx"]=14
        self.screenbuffer_current[flat_coords(REPORT_X-1,REPORT_Y+REPORT_HEIGHT)]["char"]=200

        self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y+REPORT_HEIGHT)]["col_tx"]=14
        self.screenbuffer_current[flat_coords(REPORT_X+REPORT_WIDTH,REPORT_Y+REPORT_HEIGHT)]["char"]=188

        for i in REPORT_WIDTH_RANGE:
            for j in range(REPORT_HEIGHT):
                self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y+j)]["col_tx"]=COLOR_REPORT_TX
                self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y+j)]["col_bg"]=COLOR_REPORT_BG
                self.screenbuffer_current[flat_coords(REPORT_X+i,REPORT_Y+j)]["char"]=32

        center_text=int(WINDOW_COLS/2-len(COMMAND_BOX_TITLE)/2)
        self.out_pos_color_txt(center_text,INPUT_FIELD_Y-1,COLOR_COMMAND_TITLE_TX,COLOR_WINDOW_BG,COMMAND_BOX_TITLE)

        return

    def recompile_report(self,get_screen_report):
        global REPORT_X
        global REPORT_Y
        global REPORT_WIDTH
        global REPORT_HEIGHT
        global COLOR_REPORT_TX
        global COLOR_REPORT_BG
        global REPORT_WIDTH_RANGE

        parse_report_lines=len(get_screen_report)-1

        screen_report_formatted=[]
        while len(screen_report_formatted)<REPORT_HEIGHT and parse_report_lines>=0:
            curr_line=get_screen_report[parse_report_lines]
            curr_line_array=reversed(curr_line.splitlines())
            for line in curr_line_array:
                if line=="":
                    screen_report_formatted.insert(0," "*REPORT_WIDTH)
                else:
                    for segment in reversed(chunkalize(line,REPORT_WIDTH)):
                        screen_report_formatted.insert(0,segment+" "*(REPORT_WIDTH-len(segment)))
                        if len(screen_report_formatted)==REPORT_HEIGHT:
                            break
                if len(screen_report_formatted)==REPORT_HEIGHT:
                    break
            parse_report_lines-=1

        for line_idx in range(len(screen_report_formatted)):
            for c_idx in REPORT_WIDTH_RANGE:
                self.screenbuffer_current[flat_coords(REPORT_X+c_idx,REPORT_Y+line_idx)]={
                "char":ord(screen_report_formatted[line_idx][c_idx]),
                "col_tx":COLOR_REPORT_TX,
                "col_bg":COLOR_REPORT_BG
                }

        return

    def recompile_input(self,got_input):
        global INPUT_FIELD_X
        global INPUT_FIELD_Y
        global INPUT_FIELD_LENGTH
        global COLOR_COMMAND_TX
        global COLOR_COMMAND_BG

        if len(got_input)<INPUT_FIELD_LENGTH:
            got_input+="_"
        got_input+=" "*(INPUT_FIELD_LENGTH-len(got_input))

        for c_idx in range(len(got_input)):
            self.screenbuffer_current[flat_coords(INPUT_FIELD_X+c_idx,INPUT_FIELD_Y)]={
            "char":ord(got_input[c_idx]),"col_tx":COLOR_COMMAND_TX,"col_bg":COLOR_COMMAND_BG
            }

        return

    def screen_prepare(self):
        global REPORT_OUTPUT_REFRESH_INTERVAL_SECONDS
        global LOCK_SCREEN_REPORT
        global SCREEN_REPORT_EDITED
        global TITLEBAR_Y
        global COLOR_TITLEBAR_TX
        global COLOR_WINDOW_BG
        global TITLEBAR_BOTNAME_X
        global TITLEBAR_TIMEDIFF_X
        global TITLEBAR_ONLINESTATUS_X

        got_input=self.active_console.get_console_input()["input"]

        if self.last_input_field!=got_input:
            self.last_input_field=got_input
            self.recompile_input(got_input)

        if OS_uptime()-self.last_report_refresh_time>=REPORT_OUTPUT_REFRESH_INTERVAL_SECONDS:
            LOCK_SCREEN_REPORT.acquire()
            get_screen_report=SCREEN_REPORT_LINES
            get_report_edited=SCREEN_REPORT_EDITED
            SCREEN_REPORT_EDITED=False
            LOCK_SCREEN_REPORT.release()

            if get_report_edited==True:
                self.last_report_lines=get_screen_report
                self.recompile_report(get_screen_report)

            self.last_report_refresh_time=OS_uptime()

        general_data=get_new_general_data()
        for data_type in general_data:
            value=general_data[data_type]
            if data_type=="bot_name":
                self.out_pos_color_txt(TITLEBAR_BOTNAME_X+len("Bot name: "),TITLEBAR_Y,11,COLOR_WINDOW_BG,value+" "*(32-len(value)))
            elif data_type=="time_difference":
                time_difference=float(value[1:])
                time_color=10
                if time_difference>=30:
                    time_color=14
                if time_difference>=60:
                    time_color=12
                self.out_pos_color_txt(TITLEBAR_TIMEDIFF_X+len("Local clock bias(seconds): "),TITLEBAR_Y,time_color,COLOR_WINDOW_BG,value+" "*(10-len(value)))
            elif data_type=="online":
                if value=="yes":
                    out="ONLINE"
                    colorstate=10
                else:
                    out="OFFLINE"
                    colorstate=12
                self.out_pos_color_txt(TITLEBAR_ONLINESTATUS_X+len("Status: "),TITLEBAR_Y,colorstate,COLOR_WINDOW_BG,out+" "*(11-len(out)))

        return

    def refresh_loop(self):
        global SCREEN_OUTPUT_REFRESH_RATE_SECONDS

        while self.exit_requested.is_set()==False:
            time.sleep(SCREEN_OUTPUT_REFRESH_RATE_SECONDS)
            self.screen_prepare()
            self.screen_delta_update()

        self.last_report_refresh_time=0
        self.screen_prepare()
        self.screen_delta_update()
        move_cursor(0,WINDOW_ROWS)
        cursor_visibility(True)
        self.exit_complete.set()
        return

    def screen_delta_update(self):
        global WINDOW_COLS
        global WINDOW_TILES_RANGE

        for i in WINDOW_TILES_RANGE:
            current_char=self.screenbuffer_current[i]
            last_char=self.screenbuffer_last[i]
            if last_char["col_tx"]!=current_char["col_tx"] or last_char["col_bg"]!=current_char["col_bg"] or last_char["char"]!=current_char["char"]:
                move_cursor(i%WINDOW_COLS,i/WINDOW_COLS)
                cursor_color(current_char["col_tx"],current_char["col_bg"])
                sys.stdout.write(chr(current_char["char"]))
                self.screenbuffer_last[i]={
                "col_tx":current_char["col_tx"],"col_bg":current_char["col_bg"],"char":current_char["char"]
                }

        return

    def STOP(self):
        self.exit_requested.set()
        return


def set_general_data(data_type,value):
    global GENERAL_DATA
    global LOCK_GENERAL_DATA
    
    LOCK_GENERAL_DATA.acquire()
    GENERAL_DATA[data_type]=["0",str(value)]
    LOCK_GENERAL_DATA.release()

    return

def get_new_general_data():
    retval={}

    LOCK_GENERAL_DATA.acquire()
    for data_type in GENERAL_DATA:
        if GENERAL_DATA[data_type][0]=="0":
            GENERAL_DATA[data_type][0]="1"
            retval[data_type]=GENERAL_DATA[data_type][1]
    LOCK_GENERAL_DATA.release()

    return retval


"""
MAIN
"""


warnings.filterwarnings("ignore",category=UserWarning,module="urllib2")
TIME_DELTA_LOCK=threading.Lock()
LOG_LOCK=threading.Lock()
LOCK_SCREEN_REPORT=threading.Lock()
LOCK_GENERAL_DATA=threading.Lock()
SCREEN_REPORT_LINES=[]
GENERAL_DATA={}
SCREEN_REPORT_EDITED=False
WINDOW_ROWS_RANGE=range(WINDOW_ROWS)
WINDOW_COLS_RANGE=range(WINDOW_COLS)
WINDOW_TILES_RANGE=range(WINDOW_ROWS*WINDOW_COLS)
REPORT_WIDTH_RANGE=range(REPORT_WIDTH)

console_setup()

Active_Key_Input=Console_Input(INPUT_FIELD_LENGTH)
Active_Screen=Screen_Manager(Active_Key_Input)

report("============================ FileBot ============================")
report("Author: Searinox Navras")
report("Version: "+str(__version__))
report("=================================================================\n")
report("\n\nRequirements:\n-bot token in \"token.txt\"\n"+
"-users list in \"userlist.txt\" with one entry per line, formatted as such: <USERNAME>|<HOME PATH>\n\n"+
"7-ZIP x64 will be needed for \"/zip\" functionality.\n"+
"Begin home path with \">\" to allow writing. To allow access to all drives, set the path to \"*\".\n"+
"If a user has no username, you can add them via first name and last name with a \"#\" before each. Example:\n"+
"FIRST NAME: John LAST NAME: Doe -> #John#Doe\n"+
"Note that this method only works if the user has no username, and that a \"#\" is required even if the last name is empty.\n")

CURRENT_PROCESS_ID=win32api.GetCurrentProcessId()
CURRENT_PROCESS_HANDLE=win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,True,CURRENT_PROCESS_ID)
PATH_7ZIP=""
TELEGRAM_SERVER_TIMER_DELTA=-1

try:
    reg_conn=_winreg.ConnectRegistry(None,_winreg.HKEY_LOCAL_MACHINE)
    zipkey=_winreg.OpenKey(reg_conn,"SOFTWARE\\7-Zip")
    enumvals=-1
    while PATH_7ZIP=="":
        enumvals+=1
        result=_winreg.EnumValue(zipkey,enumvals)
        if result[0].lower()=="path":
            PATH_7ZIP=result[1]
            if PATH_7ZIP[-1]!="\\":
                PATH_7ZIP+="\\"
            break
except:
    pass

if PATH_7ZIP=="":
    report("m","WARNING: 7-ZIP path not found in registry. \"/zip\" functionality will not be available.")
else:
    report("m","7-ZIP installation path found at \""+PATH_7ZIP+"\".")

fatal_error=False
collect_api_token=""

try:
    file_handle=open("token.txt","r")
    collect_api_token=file_handle.readline()
    file_handle.close()
except:
    report("m","ERROR: Make sure the file \"token.txt\" exists and contains the bot token.")
    fatal_error=True

if len(collect_api_token)==0 and fatal_error==False:
    report("m","ERROR: Make sure the token is correctly written in \"token.txt\".")
    fatal_error=True

collect_allowed_senders=[]

if fatal_error==False:
    file_entries=[]
    try:
        file_handle=open("userlist.txt","r")
        file_entries=file_handle.readlines()
        for i in file_entries:
            if i.strip()!="":
                collect_allowed_senders.append(user_entry(i.strip()))
    except:
        report("m","ERROR: Could not read entries from \"userlist.txt\".")
        fatal_error=True
    file_entries=[]

for i in reversed(range(len(collect_allowed_senders))):
    if collect_allowed_senders[i].username=="":
        del collect_allowed_senders[i]

if fatal_error==False and len(collect_allowed_senders)==0:
    report("m","ERROR: There were no valid user lists to add.")
    fatal_error=True

report("m","Performing initial Internet time synchronization...")
time_synced=False
while time_synced==False:
    time_synced=Sync_Server_Time()
    if time_synced==False:
        time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)

get_time_diff=local_machine_time_delta_str()
set_general_data("time_difference",get_time_diff)
report("m","Initial Internet time synchronization complete. Local clock bias is "+get_time_diff+" second(s).")

report("m","Number of users to listen for: "+str(len(collect_allowed_senders))+".")

if fatal_error==False:

    UserHandleInstances=[]

    collect_allowed_usernames=[]
    for i in collect_allowed_senders:
        collect_allowed_usernames.append(i.username)

    ListenerService=listener_object(collect_api_token,collect_allowed_usernames)
    ListenerService.START()
    while ListenerService.ACTIVE()==False:
        time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

    report("m","User message handler(s) starting up...")
    for i in collect_allowed_senders:
        UserHandleInstances.append(user_message_handler(collect_api_token,i.home,i.username,i.allow_write,ListenerService))
    Console=user_console(UserHandleInstances,Active_Key_Input)

    process_total_time=PRIORITY_RECHECK_INTERVAL_SECONDS
    last_server_time_check=time.time()

    while Console.IS_DONE()==False:
        time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)
        sys.stdout.flush()
        sys.stderr.flush()
        process_total_time+=MAINTHREAD_HEARTBEAT_SECONDS
        if process_total_time>=PRIORITY_RECHECK_INTERVAL_SECONDS:
            process_total_time-=PRIORITY_RECHECK_INTERVAL_SECONDS
            try:
                if win32process.GetPriorityClass(CURRENT_PROCESS_HANDLE)!=win32process.IDLE_PRIORITY_CLASS:
                    win32process.SetPriorityClass(CURRENT_PROCESS_HANDLE,win32process.IDLE_PRIORITY_CLASS)
                    report("m","Idle process priority set.")
            except:
                report("m","Error managing process priority.")

        if abs(time.time()-last_server_time_check)>=SERVER_TIME_RESYNC_INTERVAL_SECONDS:
            report("m","Performing automatic Internet time synchronization...")
            if Sync_Server_Time()==True:
                get_time_diff=local_machine_time_delta_str()
                set_general_data("time_difference",get_time_diff)
                report("m","Automatic time synchronization complete. Local clock bias is "+get_time_diff+" second(s).")
            else:
                report("m","Automatic time synchronization failed.")
            last_server_time_check=time.time()

    ListenerService.STOP()
    while ListenerService.IS_RUNNING()==True:
        time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
    ListenerService.listen_thread.join()
    del ListenerService

    while len(UserHandleInstances)>0:
        UserHandleInstances[0].bot_thread.join()
        del UserHandleInstances[0]

report("m","Program finished. Press ENTER to quit.")

Active_Screen.STOP()

while Active_Screen.exit_complete.is_set()==False:
    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)

Active_Screen.working_thread.join()
del Active_Screen
Active_Key_Input.working_thread.join()
del Active_Key_Input

cursor_color(7,0)
move_cursor(0,WINDOW_ROWS)
sys.stdout.flush()
wait_for_enter()
sys.stdout.write("\n")
sys.stdout.flush()
