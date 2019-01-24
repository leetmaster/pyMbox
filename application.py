###############################################################################
#                                                                             #
# Automatic MBOX MONITOR & SUPPORT script                                     #
# Version 0.1                                                                 #
# Auth jgarciar                                                               #
# Date 2019/01/24                                                             #
#                                                                             #
###############################################################################


# Requires pysftp instead of FTPlib module due to port 22
import pysftp

#pip install pysftp
from flask import Flask
app = Flask(__name__)

@app.route("/")

def application():
	# Nicely declare values for easy maintenance
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
		return (i)

	# 2. Open each directory 

	# 2.1 Open "working" directory

	# 2.3 Look for files in each directory

	# 2.4 If file exists send and e-mail with folder and file name

	# 3.1 If timestamp > 6 hrs send an "escalation" e-mail

	# Politely close the connection
	srv.close()

if __name__ == __"main"__:
	app.run()
