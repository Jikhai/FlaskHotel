import sys
import pwd
import os

#get username
username = pwd.getpwuid(os.geteuid()).pw_name
#path to the flask-scripts directory
path = "/net/www/" + username + "/flask-scripts/"
#add path to sys.path
sys.path.append(path)
#run web application
from webapp import app as application

