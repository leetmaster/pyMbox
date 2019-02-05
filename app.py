###############################################################################
#                                                                             #
# Automatic MBOX MONITOR & SUPPORT script                                     #
# Version 1.3.1                                                               #
# Auth jgarciar                                                               #
# Date 2019/02/01                                                             #
#                                                                             #
###############################################################################

# Required for formatting the mail
from email.mime.text import MIMEText
# Requiered to access SFTP using port 22
import pysftp
# Required to display the date and time
import datetime
# Required to send mails
import smtplib 
# Required for time
import time

# nicely declare variables for easy maintenance
mailHost = 'smtp.gmail.com'
port = 587
mailUser = 'pymbox.ms@gmail.com'
mailPasswd= 'ylkrlhfwvofybvpx'

# Users to nag with the notification
to = ['DL-MDDMX-Monitoring-Team@ITS.JNJ.com']
cc = ['jgarciar@its.jnj.com','sapoloni@its.jnj.com']

# sending to me as test
# to = ['jgarciar@its.jnj.com']
# cc = ['josegarcia@grupoassa.com']

# Cool variable to save current time 
current_time = datetime.datetime.today()
# No need to adjust TMZ
now = datetime.datetime.now()

# Nicely declare the host values for easy maintenance
HOST = "mboxnaprd.jnj.com"
USER = "LFSGB_SUPPORT"
PASSWORD = "Lf5jde18!"

# Create a cool function for writing the file inside the cycles
def fileWrite(a,b):
        f.write(a)
        f.write("\n")
        temp = str(b).split(" ",)
        f.write(temp[30])
        f.write("\n")
        return;


# Override hostkey although it will still send a warning
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

# Setting an appropriate waiting time (6 hours)
segs = 21600

print("This is going to be legen... wait for it")

# Open the file
f = open("body.txt","w+")

# Write the title to the file
f.write("Mbox Monitor & Support\n")
f.write("Version 1.3.1\n")

# Printing value of today. 
f.write ("Current time is: ") 
f.write (str(current_time)) 
f.write("\n")
f.write("\n")
# Execute actual SFTP connection
srv = pysftp.Connection(host=HOST, username=USER, password=PASSWORD, cnopts=cnopts)

# Space for automation code
# TO DO:
# 1. Read the directories and save them in 'data' variable
# 1.1 current directory /

data = srv.listdir()

# 2. Open each directory 
for i in data:
        srv.cwd(i)

# 2.1 If there's a "working" directory open it
        if srv.listdir():       
                srv.cwd("working")
                f.write(srv.pwd)
                f.write("\n")

# 2.3 Patiently look for files in each directory
                wrkdir = srv.listdir_attr()

# 2.3.1 Inform if there are files waiting to be processed
                if not wrkdir: f.write("All files have been processed\n")

                else:
                        for j in wrkdir:
                                writeFile(j,i)
                                

# 2.1.1 If there's no "working" directory smartly do the same one level above
        else:
                f.write(srv.pwd)
                f.write("\n")
                wrkdir = srv.listdir_attr()
		
                if not wrkdir: f.write("All files have been processed\n")

                else:
                        for j in wrkdir:
                                writeFile(j,i)

# 2.4 Efficiently return to root directory to star again
        srv.cwd("/")

# Support
f.write("App support: jgarciar@its.jnj.com/\")

# Politely close the SFTP connection
srv.close()


# creates SMTP session 
s = smtplib.SMTP(mailHost, port)

s.ehlo()  
# start TLS for security  
s.starttls() 
#s.connect(host,port)
# Authentication 
s.login(mailUser, mailPasswd) 
  
# return to beginning of the file
f.seek(0)

# building the message like LEGO bricks
msg = MIMEText(f.read())

# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = 'Mbox Monitor and Support'
msg['From'] = 'Mbox Monitor and Support'
msg['To'] = ", ".join(to)
msg['Cc'] = ", ".join(cc)

  
# sending the mail 
s.sendmail(mailUser, (to+cc) , msg.as_string())

# terminating the SMTP session 
s.close() 

# Close the file
f.close()

# Stop the application for 6 hours
print("dary!")
time.sleep(segs)
