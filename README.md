# FileLocker

## Team
This project is a six member team work as EFREI Paris students,
I personally took care of the software using Python and Tkinter,
and parts of the server using PHP and several other packages.

The website, including the structure and the design, was developped
by the other part of the team.

# Requirements to setup the server and use the program source code

## Setup the database
You have to import filelocker.sql in a local SQL server.
You can change the credentials required to connect to this server
in ~/Server/BACKEND/db.php

## Change PHP.ini:
post_max_size=1000M
upload_max_filesize=1000M

## Change httpd.conf:
AllowOverride All
LoadModule rewrite_module modules/mod_rewrite.so

## Add a .htaccess file:
RewriteEngine On
Options All -Indexes
RewriteRule ^BACKEND\.* /index.php

## Install TKDND (only if you want to use the source code):
Download here https://sourceforge.net/projects/tkdnd/
Paste the folder tkdndX.X in ~/python root folder/tcl
