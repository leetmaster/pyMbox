###############################################################################
#                                                                             #
# Automatic MBOX MONITOR & SUPPORT script                                     #
# Version 0.1                                                                 #
# Auth jgarciar                                                               #
# Date 2019/01/24                                                             #
#                                                                             #
###############################################################################

#pip install pysftp

# Requires pysftp instead of FTP module due to port 22
import pysftp

# Nicely declare values for easy maintenance
#HOST = "mboxnaprd.jnj.com"
#USER = "LFSGB_SUPPORT"
#PASSWORD = "Lf5jde18!"

HOST = "jruben.ga"
USER = "eztigma"
PASSWORD = "Z0ge0057"

# Override hostkey although it will still send a warning
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None

# Execute actual SFTP connection
srv = pysftp.Connection(host=HOST, username=USER, password=PASSWORD, cnopts=cnopts)

# Space for automation code
# TO DO:
# 1. Read the directories and save them in 'data' variable
data = srv.listdir()

# 1.1 List the directories
for i in data:
    print (i)

# 2. Open each directory 

# 2.1 Open "working" directory

# 2.3 Look for files in each directory

# 2.4 If file exists send and e-mail with folder and file name

# 3.1 If timestamp > 6 hrs send an "escalation" e-mail

# Politely close the connection
srv.close()
