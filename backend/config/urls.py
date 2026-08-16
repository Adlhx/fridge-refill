from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from .views import health_check, status_page

urlpatterns = [
    path('', status_page, name='status-page'),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
