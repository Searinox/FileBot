If Not WScript.Arguments.Named.Exists("elevate") Then
CreateObject("Shell.Application").ShellExecute WScript.FullName,""""&WScript.ScriptFullName&""" /elevate","","runas",1
WScript.Quit
End If

Set objFso=CreateObject("Scripting.FileSystemObject")
Set objShell=CreateObject("Wscript.Shell")
Current_Dir=objFso.GetParentFolderName(wscript.ScriptFullName)
objShell.CurrentDirectory=Current_Dir
objShell.Run """"&Current_Dir&"\FileBot.exe"&"""",8,False
