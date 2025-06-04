"""
URL configuration for deep_match project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path
from users import views
from plagiarism import views as plagiarism_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    path("", views.index, name="index"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("welcome/", views.welcome, name="welcome"),
    path("logout/", views.logout_view, name="logout"), 
    path('upload/', plagiarism_views.upload_files, name='upload_files'),
    path('check/', plagiarism_views.check_single_file, name='check_file'),
    path("result/<str:file_name>/", plagiarism_views.display_highlighted_pdf, name="display_highlighted_pdf"),
    path('report/<str:report_id>/', plagiarism_views.result_view, name='view_report'),
    path('mulitple_check/', plagiarism_views.go_to_multiple_check, name='multiple_check'),
    path('check_multiple_files/', plagiarism_views.check_multiple_files, name='check_multiple_files'),
    path('check_mult_report', plagiarism_views.go_to_report, name='check_mult_report'),
    path('teacher_report/<str:session_id>/', plagiarism_views.multiple_report_view, name='multiple_report'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)