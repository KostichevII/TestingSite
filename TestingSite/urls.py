"""
URL configuration for TestingSite project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.views.generic import TemplateView
from MainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("TestIt/TestGeneration", TemplateView.as_view(template_name="TestGeneration.html"), name="quiz_create"),
    path("TestIt/TestLoad", views.quiz_upload, name="quiz_upload"),
    path("TestIt/solveTest/<str:token>/", views.quiz_solve, name="quiz_solve"),
    path("TestIt/TestEdit", views.quiz_edit_upload, name="quiz_edit_upload"),
    path("TestIt/TestEdit/<str:token>", views.quiz_edit, name="quiz_edit"),
    path("TestIt/TestEdit/exit/", views.quiz_edit, name="quiz_edit_exit"),
    path("set-theme/", views.set_theme, name="set_theme"),
]
