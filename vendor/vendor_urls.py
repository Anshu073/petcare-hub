
from django.urls import path
from vendor import vendor_views

urlpatterns = [
    path('register/',vendor_views.vendor_register,name='vendor_register'),
    path('login/', vendor_views.vendor_login, name='vendor_login'),
    path('vendor/dashboard/', vendor_views.vendor_dashboard, name='vendor_dashboard'),
    path('vendor/logout/', vendor_views.vendor_logout, name='vendor_logout'),
]