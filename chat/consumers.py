import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatRelation, ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket-консьюмер для чата между клиентом и менеджером.
    """
    async def connect(self):
        """
        Метод, вызываемый при подключении пользователя к WebSocket.
        """
        self.manager_id = self.scope['url_route']['kwargs']['manager_id']
        self.client_id = self.scope['url_route']['kwargs']['client_id']
        self.room_group_name = f"chat_{self.manager_id}_{self.client_id}"

        user = self.scope["user"]

        allowed = await self.user_can_join(
            user, self.manager_id, self.client_id
        )
        if allowed:
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    @database_sync_to_async
    def user_can_join(self, user, manager_id, client_id):
        """
        Проверяет, может ли пользователь присоединиться к чату.
        """
        relation_exists = ChatRelation.objects.filter(
            manager_id=manager_id,
            client_id=client_id
        ).exists()

        if not relation_exists:
            return False

        return (user.id == int(manager_id)) or (user.id == int(client_id))


    @database_sync_to_async
    def create_chat_message(self, user, receiver_id, content):
        """
        Синхронно создаём сообщение в БД.
        """
        return ChatMessage.objects.create(
            sender=user,
            receiver_id=receiver_id,
            content=content
        )

    async def disconnect(self, close_code):
        """
        Метод, вызываемый при отключении пользователя от WebSocket.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        """
        Метод, вызываемый при получении сообщения от клиента.
        """
        data = json.loads(text_data)
        message = data.get('message')
        user = self.scope['user']
        if not message:
            await self.send(text_data=json.dumps({
                'error': 'Сообщение не может быть пустым.'
            }))
            return

        if user.id == int(self.manager_id):
            receiver_id = self.client_id
        else:
            receiver_id = self.manager_id

        chat_message = await self.create_chat_message(
            user, receiver_id, message
        )

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'sender_id': user.id,
                'message': message,
            }
        )

    async def chat_message(self, event):
        """
        Метод, вызываемый при отправке сообщения клиенту.
        """
        await self.send(text_data=json.dumps({
            'sender_id': event['sender_id'],
            'message': event['message'],
        }))
