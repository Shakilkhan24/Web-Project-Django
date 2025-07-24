from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from tasks import views as task_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tasks.urls')),
    # Custom login view
    path('login/', task_views.login_view, name='login'),
    # Custom logout view that handles both GET and POST
    path('logout/', task_views.logout_view, name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)