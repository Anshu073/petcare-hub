
from django.urls import path
from deliveryboy import deliveryboy_views

urlpatterns = [
   path('register/', deliveryboy_views.delivery_register, name='delivery_register'),
   path('login/', deliveryboy_views.delivery_login, name='delivery_login'),
]