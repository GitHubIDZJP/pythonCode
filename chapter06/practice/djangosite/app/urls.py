from django.conf.urls import re_path
from . import views

urlpatterns = [
    re_path(r'moments_input', views.moments_input),
    re_path(r'', views.welcome, name='first-url'),
]
