
from django.urls import path
from deliveryboy import deliveryboy_views

urlpatterns = [
    path('register/', deliveryboy_views.delivery_register, name='delivery_register'),
    path('login/', deliveryboy_views.delivery_login, name='delivery_login'),
    path('logout/', deliveryboy_views.delivery_logout, name='delivery_logout'),
    path('dashboard/', deliveryboy_views.delivery_dashboard, name='delivery_dashboard'),
    path('edit-profile/', deliveryboy_views.edit_profile, name='edit__profile'),
    path('toggle-status/', deliveryboy_views.toggle_status, name='toggle_status'),
    path('update-status/<int:order_id>/<int:new_status>/', deliveryboy_views.update_delivery_status, name='update_status'),
]