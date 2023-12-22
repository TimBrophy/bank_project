"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from public.views import home
from onlinebanking.views import landing, transactions, search
from envmanager.views import manager, clear_data, generate_data, process_data_action, execute_backend_command, cluster, export_data

from django.conf.urls.static import static
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('onlinebanking/', landing, name='landing'),
    path('onlinebanking/transactions/<int:bank_account_id>', transactions, name='transactions'),
    path('onlinebanking/search', search, name='search'),
    path('envmanager/', manager, name='manager'),
    path('envmanager/clear_data', clear_data, name='clear_data'),
    path('envmanager/generate_data', generate_data, name='generate_data'),
    path('envmanager/action', process_data_action, name='action'),
    path('envmanager/command', execute_backend_command, name='command'),
    path('envmanager/cluster', cluster, name='cluster'),
    path('envmanager/export', export_data, name='export'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)