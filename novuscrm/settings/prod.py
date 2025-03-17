from base import *
import os

DEBUG = False
SECRET_KEY = os.getenv('SECRET_KEY')
ALLOWED_HOSTS = ['127.0.0.1', 'crm.unimrkt.com',]