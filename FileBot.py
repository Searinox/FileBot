VERSION_NUMBER=1.02


"""
INIT
"""


import os
import sys
import time
import datetime
import threading
import telepot
import win32api
import _winreg

BOTS_MAX_ALLOWED_FILESIZE_BYTES=50*1024*1024
MAX_IM_SIZE_BYTES=4096
PATH_7ZIP=""
API_TOKEN=""
ALLOWED_SENDERS=[]
ALLOWED_ROOT=""
LOG_LOCK=threading.Lock()


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
        source_literal="BOTWRK"
    elif source_literal=="b":
        source_literal="BOTOBJ"
    elif source_literal=="c":
        source_literal="CONSOL"
    elif source_literal=="m":
        source_literal="MAINTD"
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

def allowed_path(input_path):
    global ALLOWED_ROOT
    if input_path.lower().find(ALLOWED_ROOT.lower())==0 or ALLOWED_ROOT=="*":
        return True
    else:
        return False

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

class bot(object):
    def __init__(self,input_token):
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
        self.listen_flag=threading.Event()
        self.listen_flag.clear()
        self.last_send_time=0
        self.lastsent_timers=[]
        self.bot_lock_pass=""
        self.pending_lockclear=threading.Event()
        self.pending_lockclear.clear()
        return

    def sendmsg(self,sid,msg):
        for i in reversed(range(len(self.lastsent_timers))):
            if time.time()-self.lastsent_timers[i]>=30:
                del self.lastsent_timers[i]
        second_delay=time.time()-self.last_send_time
        if second_delay<1:
            second_delay=1-second_delay
        else:
            second_delay=0
        if len(self.lastsent_timers)>0:
            extra_sleep=(len(self.lastsent_timers)**1.5)/12.0
        else:
            extra_sleep=0
        throttle_time=second_delay+extra_sleep
        time.sleep(throttle_time)
        try:
            self.bot_handle.sendMessage(sid,msg)
            self.last_send_time=time.time()
            self.lastsent_timers.append(self.last_send_time)
            excess_entries=max(0,len(self.lastsent_timers)-30)
            for i in range(excess_entries):
                del self.lastsent_timers[0]
            return True
        except:
            report("w","Bot was unable to respond.")
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
            report("w","Bot unlocked by console.")

    def bot_thread_work(self):
        self.bot_handle=telepot.Bot(self.token)
        bot_get_ok=False
        while bot_get_ok==False:
            try:
                self.name=self.bot_handle.getMe()[u"username"]
                bot_get_ok=True
            except:
                report("w","Bot activation error.")
                time.sleep(1)

        report("w","Bot \""+self.name+"\" is now online.")
        self.catch_up_IDs()
        report("w","Contact the bot from an allowed user and type \"/help\" for usage information.")

        while self.keep_running.is_set()==True:
            time.sleep(1)
            self.check_tasks()
            if self.listen_flag.is_set()==True:
                response=[]
                try:
                    response=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                except:
                    report("w","Error retrieving messages.")
                if len(response)>0:
                    self.process_messages(response)

        report("w","Bot exited.")
        self.bot_has_exited.set()
        return

    def catch_up_IDs(self):
        retrieved=False
        responses=[]
        while retrieved==False:
            try:
                responses=self.bot_handle.getUpdates(offset=self.last_ID_checked+1)
                retrieved=True
                report("w","Caught up with messages.")
            except:
                report("w","Failed to catch up with messages.")
                time.sleep(1)
        if len(responses)>0:
            self.last_ID_checked=responses[-1][u"update_id"]
        responses=[]
        self.start_time=time.time()
        return

    def START(self):
        report("b","Bot start issued.")
        self.bot_has_exited.clear()
        self.keep_running.set()
        self.bot_thread.start()
        return
        
    def LISTEN(self,new_state):
        global ALLOWED_ROOT
        if new_state==True:
            report("b","Listen started.")
            if ALLOWED_ROOT=="*":
                self.last_folder="C:\\"
            else:
                self.last_folder=ALLOWED_ROOT
                self.catch_up_IDs()
                self.listen_flag.set()
        else:
            report("b","Listen stopped.")
            self.listen_flag.clear()

    def STOP(self):
        report("b","Bot stop issued.")
        self.listen_flag.clear()
        self.keep_running.clear()
        while self.bot_has_exited.is_set()==False:
            time.sleep(0.2)
        return

    def IS_RUNNING(self):
        return self.bot_has_exited.is_set()==False

    def process_messages(self,input_msglist):
        global ALLOWED_SENDERS
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
                    if time.time()-msg_send_time<=60:
                        if input_msglist[i][u"message"][u"from"][u"username"] in ALLOWED_SENDERS:
                            if input_msglist[i][u"message"][u"chat"][u"type"]=="private":
                                collect_new_messages.insert(0,input_msglist[i][u"message"])
            else:
                break
        self.last_ID_checked=newest_ID

        for m in collect_new_messages:
            if time.time()-m[u"date"]<=60:
                if u"text" in m:
                    self.process_instructions(m[u"from"][u"id"],m[u"text"],m[u"chat"][u"id"])
                else:
                    if u"document" in m:
                        print self.bot_handle.getFile(m[u"document"][u"file_id"])
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
                    self.sendmsg(sid,"Bot unlocked.")
                    report("w","Bot unlocked by user.")
                    return
                else:
                    return
            else:
                return

        report("w","New message processed.")
        if msg[0]!="/":
            return
        cmd_end=msg.find(" ")
        if cmd_end==-1:
            cmd_end=len(msg)
        command_type=msg[1:cmd_end].strip().lower()
        command_args=msg[cmd_end+1:].strip()
        response=""
        
        if command_type=="start":
            report("w","Bot start requested.")
        elif command_type=="stopbot":
            response="Bot stopped."
            self.listen_flag.clear()
            report("w","Bot stopped listening on user command.")
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

            report("w","Listing requested for path \""+command_args+"\" with search string \""+extra_search+"\", folders only="+str(folders_only)+".")

            if command_args=="":
                use_folder=self.last_folder
            else:
                use_folder=command_args
            use_folder=self.rel_to_abs(command_args)
            if allowed_path(use_folder)==True:
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
                if os.path.isdir(newpath)==True and allowed_path(newpath)==True:
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
                        report("w","Current folder changed to \""+self.last_folder+"\".")
                else:
                    response="Bad path."
            else:
                response="Current folder is \""+self.last_folder+"\"."
        elif command_type=="get":
            newpath=self.rel_to_abs(command_args,True)
            if os.path.exists(newpath)==True and allowed_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","Requested get file \""+newpath+"\".")
                self.sendmsg(sid,"Getting file, please wait...")
                try:
                    fsize=os.path.getsize(newpath)
                    if fsize<=BOTS_MAX_ALLOWED_FILESIZE_BYTES and fsize!=0:
                        self.bot_handle.sendDocument(cid,open(newpath,"rb"))
                    else:
                        if fsize!=0:
                            response="Bots cannot upload files larger than 50MB."
                        else:
                            response="File is empty."
                except:
                    response="Problem getting file."
                    report("w","File send error.")
            else:
                response="File not found."
        elif command_type=="eat":
            newpath=self.rel_to_abs(command_args,True)
            if os.path.exists(newpath)==True and allowed_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","Requested eat file \""+newpath+"\".")
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
                    report("w","File send error.")
                if success==True:
                    try:
                        os.remove(newpath)
                        self.sendmsg(sid,"File deleted.")
                    except:
                        response="Problem deleting file."
                        report("w","File delete error.")
            else:
                response="File not found."
        elif command_type=="del":
            newpath=self.rel_to_abs(command_args,True)
            if os.path.exists(newpath)==True and allowed_path(newpath)==True:
                newpath=str(win32api.GetLongPathNameW(win32api.GetShortPathName(newpath)))
                report("w","Requested delete file \""+newpath+"\".")
                try:
                    os.remove(newpath)
                    self.sendmsg(sid,"File deleted.")
                except:
                    response="Problem deleting file."
                    report("w","File delete error.")
            else:
                response="File not found."
        elif command_type=="up":
            if self.last_folder.count("\\")>1:
                newpath=self.last_folder[:-1]
                newpath=newpath[:newpath.rfind("\\")+1]
                if allowed_path(newpath)==True:
                    self.last_folder=newpath
                    response="Current folder is now \""+self.last_folder+"\"."
                    report("w","Current folder changed to \""+self.last_folder+"\".")
                else:
                    response="Already at top folder."
            else:
                response="Already at top folder."
        elif command_type=="zip":
            if PATH_7ZIP!="":
                newpath=self.rel_to_abs(command_args)
            else:
                response="7ZIP install was not found."
                report("w","Attempted to call 7ZIP but install is missing.")
            if os.path.exists(newpath)==False and newpath[-1]=="\\":
                newpath=newpath[:-1]
            if os.path.exists(newpath)==True and PATH_7ZIP!="" and allowed_path(newpath)==True:
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
                    run_commands="start cmd /c \""+prompt_commands+"\""
                    os.system(run_commands)
                    response="Issued zip command."
                    report("w","Zip command issued on \""+folder_path+archive_filename+"\".")
                except:
                    response="Problem getting file."
                    report("w","Zip \""+command_args+"\" failed.")
            else:
                response="File not found."
                report("w","[BOTWRK] Zip \""+command_args+"\" file not found.")
        elif command_type=="lock":
            if command_args.strip()!="" and len(command_args.strip())<=32:
                self.bot_lock_pass=command_args.strip()
                response="Bot locked."
                report("w","Bot was locked down with password.")
            else:
                response="Bad password for locking."
        elif command_type=="help":
            response="AVAILABLE COMMANDS:\n\n"
            response+="/help: display this help screen\n"
            response+="/cd [PATH]: change path(eg: /cd c:\windows); leave blank to check current\n"
            response+="/dir [PATH] [?f:<filter>] [?d]: list files/folders, filter optional(/dir c:\windows ?f:.exe), use ?d for directories only\n"
            response+="/zip [PATH]: make a 7ZIP archive, extension will be .7z.TMP until finished\n"
            response+="/up: move up one folder from current path\n"
            response+="/get [[PATH]FILE]: retrieve the file at the location to Telegram\n"
            response+="/eat [[PATH]FILE]: upload the file at the location to Telegram, then delete it from its original location\n"
            response+="/del [[PATH]FILE]: delete the file at the location\n"
            response+="/lock <password>: lock the bot from responding to messages\n"
            response+="/unlock <password>: unlock the bot\n"
            response+="/stopbot: deactivate bot listening permanently\n"
            response+="\nSlashes work both ways in paths (/cd c:/windows, /cd c:\windows)"
            report("w","Help requested.")
        else:
            self.sendmsg(sid,"Command unknown. Type \"/help\" for a list of commands.")

        if response!="":
            self.sendmsg(sid,response)
        return
                
class user_console(object):
    def __init__(self,bot_object):
        self.working_thread=threading.Thread(target=self.process_input)
        self.working_thread.daemon=True
        self.bot_object=bot_object
        self.finished_work=threading.Event()
        self.finished_work.clear()
        self.working_thread.start()
        return
        
    def IS_DONE(self):
        return self.finished_work.is_set()==True
    
    def process_command(self,input_command):
        if input_command.lower().strip()=="start":
            self.bot_object.LISTEN(True)
        if input_command.lower().strip()=="stop":
            self.bot_object.LISTEN(False)
        if input_command.lower().strip()=="unlock":
            self.bot_object.pending_lockclear.set()
        if input_command.lower().strip()=="help":
            report("c","AVAILABLE COMMANDS:\n")
            report("c","start: start listening to messages")
            report("c","stop: stop the bot from listening")
            report("c","unlock: unlock the bot")
            report("c","help: display help\n")
            report("c","Use \"*\" as a home path to allow access to all drives.")

    def process_input(self):
        loop_input=True
        self.bot_object.START()
        self.bot_object.LISTEN(True)
        report("c","User console activated.")
        report("c","Type \"help\" in the console for available commands.")
        while loop_input==True:
            command=raw_input("[CONSOL] Input Commands: ")
            if command.lower().strip()=="exit" or self.bot_object.IS_RUNNING()==False:
                loop_input=False
                self.bot_object.STOP()
                self.finished_work.set()
            else:
                self.process_command(command)
        return


"""
MAIN
"""


report("==========================FileBot==========================")
report("Author: Searinox Navras")
report("Version: "+str(float(VERSION_NUMBER)))
report("===========================================================\n")
report("\n\nStore:\n-allowed users in allowed_users.txt\n-root directory in home.txt\n-bot token in token.txt in the same folder\n\n7-Zip x64 must be installed for /zip functionality.\n")

fatal_error=False
users_array=[]

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
    report("m","WARNING: 7ZIP path not found in registry. /zip functionality will not be available.")

try:
    file_handle=open("token.txt","r")
    API_TOKEN=file_handle.readline()
    file_handle.close()
except:
    report("m","Token error. Make sure the file \"token.txt\" exists in the same folder and contains the bot token.")
    fatal_error=True

if len(API_TOKEN)==0:
    report("m","Token missing. Make sure the token is correctly written in \"token.txt\".")
    fatal_error=True

if fatal_error==False:
    try:
        file_handle=open("allowed_users.txt","r")
        users_array=file_handle.readlines()
        file_handle.close()
    except:
        report("m","Users error. Make sure the file \"allowed_users.txt\" exists in the same folder and contains one allowed user per each line.")
        fatal_error=True

for i in users_array:
    ALLOWED_SENDERS.append(i.strip())

users_array=[]

try:
    file_handle=open("home.txt","r")
    ALLOWED_ROOT=file_handle.readline()
    ALLOWED_ROOT=ALLOWED_ROOT.strip()
    ALLOWED_ROOT=ALLOWED_ROOT.replace("/","\\")
    file_handle.close()
except:
    report("m","The file \"home.txt\" could not be found. No root path can be set.")
    fatal_error=True

if len(ALLOWED_ROOT)==0:
    report("m","No home folder specified. Please make sure one is specified in \"home.txt\".")
    fatal_error=True
else:
    if ALLOWED_ROOT[-1]!="\\" and ALLOWED_ROOT.find("*")==-1:
        ALLOWED_ROOT+="\\"
    ALLOWED_ROOT=ALLOWED_ROOT[0].upper()+ALLOWED_ROOT[1:]

if len(ALLOWED_SENDERS)==0:
    report("m","No allowed users have been specified. Please make sure the intended users are in \"allowed_users.txt\".")
    fatal_error=True

if fatal_error==False:
    report("m","Program starting. Home folder is \""+ALLOWED_ROOT+"\".")
    FileBotObject=bot(API_TOKEN)
    Console=user_console(FileBotObject)

    while Console.IS_DONE()==False:
        time.sleep(0.2)
        sys.stdout.flush()

report("m","Program finished. Press ENTER to exit.")
raw_input()
