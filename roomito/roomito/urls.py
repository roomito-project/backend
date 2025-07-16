from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui'),
    path('api/', include('students.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='swagger-ui-alt'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)