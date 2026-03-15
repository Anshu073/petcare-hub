
from django.urls import path
from vendor import vendor_views

urlpatterns = [
    path('register/',vendor_views.vendor_register,name='vendor_register'),
    path('vendor/login/', vendor_views.vendor_login, name='vendor_login'),
]