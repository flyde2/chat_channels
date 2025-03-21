from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, ChatRelationViewSet

router = DefaultRouter()
router.register(r'messages', ChatMessageViewSet, basename='messages')
router.register(r'relations', ChatRelationViewSet, basename='relations')

urlpatterns = [
    path('', include(router.urls)),
]
