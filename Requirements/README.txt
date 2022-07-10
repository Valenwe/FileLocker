Requirements to setup the server

Install TKDND :
https://sourceforge.net/projects/tkdnd/
Paste the folder tkdndX.X in <root python folder>/tcl

Change PHP.ini :
post_max_size=1000M
upload_max_filesize=1000M

Change httpd.conf :
AllowOverride All
LoadModule rewrite_module modules/mod_rewrite.so

Ajouter un fichier .htaccess :

RewriteEngine On
Options All -Indexes
RewriteRule ^BACKEND\.* /index.php