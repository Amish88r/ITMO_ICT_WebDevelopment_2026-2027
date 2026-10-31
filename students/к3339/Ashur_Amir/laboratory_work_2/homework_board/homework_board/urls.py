from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Доска домашних заданий — администрирование'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('board.urls')),
]
