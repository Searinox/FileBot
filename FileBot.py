VERSION_NUMBER=1.15


"""
INIT
"""


import os
import sys
import time
import datetime
import threading
import telepot
import subprocess
import win32api
import win32con
import win32process
import win32pdh
import _winreg
import urllib2

MAINTHREAD_HEARTBEAT_SECONDS=1
SERVER_TIME_RESYNC_INTERVAL_SECONDS=60*60*24
PRIORITY_RECHECK_INTERVAL_SECONDS=60
BOT_WORKTHREAD_HEARTBEAT_SECONDS=1
PENDING_ACTIVITY_HEARTBEAT_SECONDS=0.2

BOTS_MAX_ALLOWED_FILESIZE_BYTES=50*1024*1024
MAX_IM_SIZE_BYTES=4096


"""
DEFS
"""


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
        source_literal="BOT_WRK"
    elif source_literal=="b":
        source_literal="BOT_OBJ"
    elif source_literal=="c":
        source_literal="CONSOLE"
    elif source_literal=="m":
        source_literal="MAINTRD"
    if source_literal!="":
        source_literal=" ["+source_literal+"] "
    else:
        source_literal=" "
    msg=str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))+source_literal+input_literal
    sys.stdout.write(msg+"\n")
    sys.stdout.flush()

    LOG_LOCK.acquire()

    try:
        log_handle=open("log.txt","a")
        log_handle.write(msg+"\n")
        log_handle.close()
    except:
        pass

    LOG_LOCK.release()
    return

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
        return str(int(round(input_size/1024.0,2)))+" KB"
    if input_size<1024**3:
        return str(int(round(input_size/1024.0**2,2)))+" MB"
    if input_size<1024**4:
        return str(int(round(input_size/1024.0**3,2)))+" GB"

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

def OS_uptime():
    path=win32pdh.MakeCounterPath((None,"System",None,None,0,"System Up Time"))
    query=win32pdh.OpenQuery()
    handle=win32pdh.AddCounter(query,path)
    win32pdh.CollectQueryData(query)
    return win32pdh.GetFormattedCounterValue(handle,win32pdh.PDH_FMT_LONG|win32pdh.PDH_FMT_NOSCALE)[1]

def Live_UTC_Time():
    response=urllib2.urlopen("http://time.gov/actualtime.cgi")
    timestr=response.read()
    quot1=timestr.find("\"")
    quot2=quot1+1+timestr[quot1+1:].find("\"")
    return int(round(int(timestr[quot1+1:quot2-3])/1000.0))

def Sync_Telegram_Server_Time():
    global TELEGRAM_SERVER_TIMER_DELTA
    begin_sync=OS_uptime()
    TIMER_LOCK.acquire()
    try:
        TELEGRAM_SERVER_TIMER_DELTA=Live_UTC_Time()-OS_uptime()
        end_sync=OS_uptime()
        TELEGRAM_SERVER_TIMER_DELTA+=end_sync-begin_sync
    except:
        TIMER_LOCK.release()
        return False
    TIMER_LOCK.release()
    return True

def telegram_time():
    global TELEGRAM_SERVER_TIMER_DELTA
    global TIMER_LOCK
    TIMER_LOCK.acquire()
    retval=OS_uptime()+TELEGRAM_SERVER_TIMER_DELTA
    TIMER_LOCK.release()
    return retval

class user_fbot(object):
    def __init__(self,input_token,input_root,input_user,input_write):
        self.name=""
        self.bot_thread=threading.Thread(target=self.bot_thread_work)
        self.bot_thread.daemon=True
        self.token=input_token
        self.keep_running=threading.Event()
        self.keep_running.clear()
        self.bot_has_exited=threading.Event()
        self.bot_has_exited.set()
        self.last_ID_checked=-1
        self.start_time=0
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
            report("w","<"+self.allowed_user+"> "+"Bot instance was unable to respond.")
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
                    test_path=win32api.GetLongPathNameW(win32api.GetShortPathName(newpath))
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
            report("w","<"+self.allowed_user+"> "+"Bot instance unlocked by console.")
        return

    def bot_thread_work(self):
        self.bot_handle=telepot.Bot(self.token)
        last_check_status=False
        bot_get_ok=False
        activation_fail_announced=False
        while bot_get_ok==False:
            try:
                self.name=self.bot_handle.getMe()[u"username"]
                bot_get_ok=True
            except:
                if activation_fail_announced==False:
                    report("w","<"+self.allowed_user+"> "+"Bot instance activation error. Will keep trying...")
                    activation_fail_announce=True
                time.sleep(BOT_WORKTHREAD_HEARTBEAT_SECONDS)

        report("w","<"+self.allowed_user+"> "+"Bot instance for \""+self.allowed_user+"\" is now online.")
        self.catch_up_IDs()

        while self.keep_running.is_set()==True:
            time.sleep(BOT_WORKTHREAD_HEARTBEAT_SECONDS)
            self.check_tasks()
            if self.listen_flag.is_set()==True:
                response=[]

                try:
                    response=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                    check_status=True
                except:
                    check_status=False

                if check_status!=last_check_status:
                    last_check_status=check_status
                    if check_status==True:
                        report("w","<"+self.allowed_user+"> "+"Message retrieval is now online.")
                    else:
                        report("w","<"+self.allowed_user+"> "+"Stopped being able to retrieve messages.")

                if len(response)>0:
                    self.process_messages(response)

        report("w","<"+self.allowed_user+"> "+"Bot instance exited.")
        self.bot_has_exited.set()
        return

    def catch_up_IDs(self):
        retrieved=False
        responses=[]
        announced_fail=False
        while retrieved==False:
            try:
                responses=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                retrieved=True
                report("w","<"+self.allowed_user+"> "+"Caught up with messages.")
            except:
                if announced_fail==False:
                    report("w","<"+self.allowed_user+"> "+"Failed to catch up with messages. Will keep trying...")
                    announced_fail=True
                time.sleep(BOT_WORKTHREAD_HEARTBEAT_SECONDS)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=telegram_time()
        return

    def START(self):
        report("b","<"+self.allowed_user+"> "+"Bot instance start issued, home path is \""+self.allowed_root+"\", allow writing: "+str(self.allow_writing).upper()+".")
        self.bot_has_exited.clear()
        self.keep_running.set()
        self.bot_thread.start()
        return

    def LISTEN(self,new_state):
        if new_state==True:
            report("b","<"+self.allowed_user+"> "+"Listen started.")
            if self.allowed_root=="*":
                self.last_folder="C:\\"
            else:
                self.last_folder=self.allowed_root
            self.catch_up_IDs()
            self.listen_flag.set()
        else:
            report("b","<"+self.allowed_user+"> "+"Listen stopped.")
            self.listen_flag.clear()

    def STOP(self):
        report("b","<"+self.allowed_user+"> "+"Bot instance stop issued.")
        self.listen_flag.clear()
        self.keep_running.clear()
        return

    def IS_RUNNING(self):
        return self.bot_has_exited.is_set()==False

    def process_messages(self,input_msglist):
        collect_new_messages=[]
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
                    if telegram_time()-msg_send_time<=30:
                        if input_msglist[i][u"message"][u"from"][u"username"]==self.allowed_user:
                            if input_msglist[i][u"message"][u"chat"][u"type"]=="private":
                                collect_new_messages.insert(0,input_msglist[i][u"message"])
            else:
                break
        self.last_ID_checked=newest_ID

        for m in collect_new_messages:
            if telegram_time()-m[u"date"]<=30:
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

        self.sendmsg(sid,"Putting file \""+filename+"\" at \""+self.last_folder+"\"...")
        if os.path.exists(self.last_folder+filename)==False or (os.path.exists(self.last_folder+filename)==True and os.path.isfile(self.last_folder+filename)==False):
            try:
                self.bot_handle.download_file(fid,self.last_folder+filename)
                self.sendmsg(sid,"Finished putting file \""+filename+"\" in folder \""+self.last_folder+"\".")
            except:
                self.sendmsg(sid,"File \""+filename+"\" could not be placed.")
        else:
            self.sendmsg(sid,"File \""+filename+"\" already exists at the location.")

    def process_instructions(self,sid,msg,cid):
        global BOTS_MAX_ALLOWED_FILESIZE_BYTES
        global MAX_IM_SIZE_BYTES
        if self.bot_lock_pass!="":
            if msg.lower().find("/unlock ")==0:
                if msg[len("/unlock "):].strip()==self.bot_lock_pass:
                    self.bot_lock_pass=""
                    self.lock_status.clear()
                    self.sendmsg(sid,"Bot unlocked.")
                    report("w","<"+self.allowed_user+"> "+"Bot instance unlocked by user.")
                    return
                else:
                    return
            else:
                return

        report("w","<"+self.allowed_user+"> "+"New message processed.")
        if msg[0]!="/":
            return
        cmd_end=msg.find(" ")
        if cmd_end==-1:
            cmd_end=len(msg)
        command_type=msg[1:cmd_end].strip().lower()
        command_args=msg[cmd_end+1:].strip()
        response=""
        
        if command_type=="start":
            report("w","<"+self.allowed_user+"> "+"Bot instance start requested.")
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
                report("w","<"+self.allowed_user+"> "+"Requested get file \""+newpath+"\".")
                self.sendmsg(sid,"Getting file, please wait...")
                try:
                    fsize=os.path.getsize(newpath)
                    if fsize<=BOTS_MAX_ALLOWED_FILESIZE_BYTES and fsize!=0:
                        self.bot_handle.sendDocument(cid,open(newpath,"rb"))
                    else:
                        if fsize!=0:
                            response="Bots cannot upload files larger than "+readable_size(BOTS_MAX_ALLOWED_FILESIZE_BYTES)+"."
                        else:
                            response="File is empty."
                except:
                    response="Problem getting file."
                    report("w","<"+self.allowed_user+"> "+"File send error.")
            else:
                response="File not found or inaccessible."
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
                        os.remove(newpath)
                        self.sendmsg(sid,"File deleted.")
                    except:
                        response="Problem deleting file."
                        report("w","<"+self.allowed_user+"> "+"File delete error.")
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
        elif command_type=="zip" and self.allow_writing==True:
            if PATH_7ZIP!="":
                newpath=self.rel_to_abs(command_args)
            else:
                response="7ZIP install was not found."
                report("w","<"+self.allowed_user+"> "+"Attempted to call 7ZIP but install is missing.")
            if os.path.exists(newpath)==False and newpath[-1]=="\\":
                newpath=newpath[:-1]
            if self.usable_path(newpath)==True and PATH_7ZIP!="":
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
                report("w","<"+self.allowed_user+"> "+"Bot instance was locked down with password.")
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
    def __init__(self,bot_list):
        self.working_thread=threading.Thread(target=self.process_input)
        self.working_thread.daemon=True
        self.bot_list=bot_list
        self.finished_work=threading.Event()
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
                    report("c","Bot instance for user \""+i.allowed_user+"\":\nHome path=\""+i.allowed_root+"\"\nWrite mode: "+str(i.allow_writing).upper()+"\nLocked: "+str(i.lock_status.is_set()).upper()+"\nListening: "+str(i.listen_flag.is_set()).upper()+"\n\n")
        elif input_command=="unlock":
            for i in self.bot_list:
                if i.allowed_user.lower()==input_argument or input_argument=="":
                    i.pending_lockclear.set()
        elif input_command=="sync":
            report("c","Manual time sync requested...")
            if Sync_Telegram_Server_Time():
                report("c","Time sync successful. Local machine time difference is "+str(int(int(time.time())-telegram_time()))+" second(s).")
            else:
                report("c","Time sync failed.")
        elif input_command=="help":
            report("c","AVAILABLE CONSOLE COMMANDS:\n")
            report("c","start [USER]: start listening to messages for user; leave blank to apply to all instances")
            report("c","stop [USER]: stop listening to messages for user; leave blank to apply to all instances")
            report("c","unlock [USER]: unlock the bot for user; leave blank to apply to all instances")
            report("c","stats [USER]: list bot stats; leave blank to list all instances")
            report("c","sync: manually resynchronize bot timer with internet world time")
            report("c","help: display help\n")
        else:
            report("c","Unrecognized command. Type \"help\" for a list of commands.")
        return

    def process_input(self):
        loop_input=True
        for i in self.bot_list:
            i.START()
            i.LISTEN(True)
        report("c","User console activated.")
        report("c","Type \"help\" in the console for available commands.")
        while loop_input==True:
            command=raw_input("[CONSOL] Input Commands: ")
            if command.lower().strip()=="exit" or self.bots_running()==0:
                loop_input=False
                for i in self.bot_list:
                    i.STOP()
                while self.bots_running()>0:
                    time.sleep(PENDING_ACTIVITY_HEARTBEAT_SECONDS)
                self.finished_work.set()
            else:
                self.process_command(command)
        return

class user_entry(object):
    def __init__(self,from_string):
        try:
            segments=from_string.split("|")
            for i in range(len(segments)):
                segments[i]=segments[i].strip()
        
            self.username=segments[0]
            self.home=segments[1]
            self.allow_write=False

            if len(self.home)>0:
                if self.home[0]==">":
                    self.allow_write=True
                    self.home=self.home[1:]
            if len(self.home)==0:
                raise ValueError("Home path was empty.")
        except:
            report("m","WARNING: User list \""+from_string+"\" was not validly formatted.")
            self.username=""
            self.home=""
            self.allow_write=False
        return


"""
MAIN
"""


TELEGRAM_SERVER_TIMER_DELTA=-1
LOG_LOCK=threading.Lock()
TIMER_LOCK=threading.Lock()

report("==========================FileBot==========================")
report("Author: Searinox Navras")
report("Version: "+str(float(VERSION_NUMBER)))
report("===========================================================\n")
report("\n\nRequirements:\n-bot token in \"token.txt\"\n-users list in \"userlist.txt\" with one entry per line, formatted as such: <USERNAME>|<HOME PATH>\n\n7-Zip x64 will be needed for /zip functionality.\nBegin home path with \">\" to allow writing. To allow access to all drives, set the path to \"*\".\n")

CURRENT_PROCESS_ID=win32api.GetCurrentProcessId()
CURRENT_PROCESS_HANDLE=win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,True,CURRENT_PROCESS_ID)

PATH_7ZIP=""

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

report("m","Synchronizing with internet time...")
time_synced=False
while time_synced==False:
    time_synced=Sync_Telegram_Server_Time()
    if time_synced==False:
        time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)
report("m","Sync completed. Local machine time difference is "+str(int(int(time.time())-telegram_time()))+" second(s).")

BotInstances=[]

if fatal_error==False:
    report("m","Bot instances starting up...")
    for i in collect_allowed_senders:
        BotInstances.append(user_fbot(collect_api_token,i.home,i.username,i.allow_write))
    Console=user_console(BotInstances)

    server_time_check=0
    process_total_time=PRIORITY_RECHECK_INTERVAL_SECONDS
    while Console.IS_DONE()==False:
        time.sleep(MAINTHREAD_HEARTBEAT_SECONDS)
        sys.stdout.flush()
        process_total_time+=MAINTHREAD_HEARTBEAT_SECONDS
        if process_total_time>=PRIORITY_RECHECK_INTERVAL_SECONDS:
            process_total_time-=PRIORITY_RECHECK_INTERVAL_SECONDS
            try:
                if win32process.GetPriorityClass(CURRENT_PROCESS_HANDLE)!=win32process.IDLE_PRIORITY_CLASS:
                    win32process.SetPriorityClass(CURRENT_PROCESS_HANDLE,win32process.IDLE_PRIORITY_CLASS)
                    report("m","Idle process priority set.")
            except:
                report("m","Error managing process priority.")

        if server_time_check>=SERVER_TIME_RESYNC_INTERVAL_SECONDS:
            if Sync_Telegram_Server_Time()==True:
                report("m","Automatic time synchronization was performed.")
            else:
                report("m","Automatic time synchronization failed.")
            server_time_check-=SERVER_TIME_RESYNC_INTERVAL_SECONDS

while len(BotInstances)>0:
    del BotInstances[0]

report("m","Program finished. Press ENTER to exit.")
raw_input()
