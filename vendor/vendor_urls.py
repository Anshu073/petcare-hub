
from django.urls import path
from vendor import vendor_views

urlpatterns = [
    path('register/',vendor_views.vendor_register,name='vendor_register'),
    path('login/', vendor_views.vendor_login, name='vendor_login'),
    path('dashboard/', vendor_views.vendor_dashboard, name='vendor_dashboard'),
    path('logout/', vendor_views.vendor_logout, name='vendor_logout'),
    path('vendor/db-status/<int:db_id>/<int:new_status>/', vendor_views.update_db_status, name='db_status'),
    path('vendor/assign-order/', vendor_views.assign_order, name='assign_order'),
    path('contact/', vendor_views.vendor_contact, name='vendor_contact'),
]