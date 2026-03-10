
from django.urls import path
from deliveryboy import deliveryboy_views

urlpatterns = [
    path('register/', deliveryboy_views.delivery_register, name='delivery_register'),
    path('login/', deliveryboy_views.delivery_login, name='delivery_login'),
    path('logout/', deliveryboy_views.delivery_logout, name='delivery_logout'),
    path('dashboard/', deliveryboy_views.delivery_dashboard, name='delivery_dashboard'),
    path('edit-profile/', deliveryboy_views.edit_profile, name='edit_profile'),
    path('toggle-status/', deliveryboy_views.toggle_status, name='toggle_status'),
    path('deliver-order/<int:order_id>/', deliveryboy_views.deliver_order, name='deliver_order'),
]