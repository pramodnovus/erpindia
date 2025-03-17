from django.shortcuts import render
from django.http import HttpResponse
# Create your views here.

# def login_views(request):
#     pass

def home(request):
    return HttpResponse("api ok")