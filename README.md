# FileBot - Telegram file server bot for Windows 7 and higher written in Python 3.7

7-ZIP (C) Igor Pavlov; distributed under GNU LGPL license; https://www.7-zip.org/

The bot serves files from the host machine to allowed users. Folder navigation and listing with filters are also possible. Users with write privileges can also upload their own files, create and delete files and folders, and archive files and folders.

Type "help" in the console for a list of commands.

Formatting info for token and allowed users + paths is available at console startup.

In-chat help is available by typing "/help" to the bot.

Set read or read/write permissions on a per-user basis.

Initiate or cancel archival tasks for files or folders to later retrieve them within service file size limits.

File size limits enforced on bots by the Telegram service still apply. As of the last update to this document, the limit for uploading files to chat is 50MB and the limit for downloading files from chat is 20MB.

NOTE: This program requires PyQt5 to be installed. If you intend to compile to an executable using PyInstaller, be advised that a bug in Qt5 requires version 5.12.2 or prior to be installed in order for the compiled program to work.
