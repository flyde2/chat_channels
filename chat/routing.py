from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/chat/<int:manager_id>/<int:client_id>/',
         consumers.ChatConsumer.as_asgi()),
]
