from django.contrib import admin

# Register your models here.
from api.user.models import *

admin.site.register(CustomUser)