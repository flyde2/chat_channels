from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ChatMessage, ChatRelation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'is_staff', 'email']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp']


class ChatRelationSerializer(serializers.ModelSerializer):
    manager = UserSerializer(read_only=True)
    client = UserSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source='client',
        queryset=User.objects.all(),
        write_only=True
    )

    class Meta:
        model = ChatRelation
        fields = ['id', 'manager', 'client', 'client_id']
