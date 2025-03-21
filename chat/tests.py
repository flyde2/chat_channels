import asyncio

from channels.testing import WebsocketCommunicator, ChannelsLiveServerTestCase
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from django.urls import reverse
from django.contrib.auth.models import User
from chat.models import ChatRelation, ChatMessage
from chat_channels.asgi import application


class ChatAPITests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager',
            password='test12345',
            is_staff=True
        )
        self.client_user = User.objects.create_user(
            username='client',
            password='test12345',
            is_staff=False
        )

        # Создадим нескольких разных пользователей для усложнённого теста
        self.other_manager = User.objects.create_user(
            username='other_manager',
            password='test54321',
            is_staff=True
        )
        self.other_client = User.objects.create_user(
            username='other_client',
            password='test54321',
            is_staff=False
        )

        self.relation = ChatRelation.objects.create(
            manager=self.manager,
            client=self.client_user
        )
        # Связь между двумя "другими" пользователями
        self.other_relation = ChatRelation.objects.create(
            manager=self.other_manager,
            client=self.other_client
        )

        self.message1 = ChatMessage.objects.create(
            sender=self.manager,
            receiver=self.client_user,
            content='Привет от менеджера'
        )
        self.message2 = ChatMessage.objects.create(
            sender=self.client_user,
            receiver=self.manager,
            content='Ответ от клиента'
        )

        # Сообщения для другой пары
        self.message3 = ChatMessage.objects.create(
            sender=self.other_manager,
            receiver=self.other_client,
            content='Привет от другого менеджера'
        )
        self.message4 = ChatMessage.objects.create(
            sender=self.other_client,
            receiver=self.other_manager,
            content='Ответ другого клиента'
        )

        self.api_client = APIClient()

    def test_manager_can_see_relations(self):
        """
        Проверяем, что менеджер видит только свою связь
        """
        self.api_client.login(username='manager', password='test12345')
        url = reverse('relations-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['manager']['username'], 'manager')
        self.assertEqual(response.data[0]['client']['username'], 'client')

    def test_client_can_see_own_relation(self):
        """
        Проверяем, что клиент видит только свою связь
        """
        self.api_client.login(username='client', password='test12345')
        url = reverse('relations-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['manager']['username'], 'manager')
        self.assertEqual(response.data[0]['client']['username'], 'client')

    def test_anonymous_cannot_see_relations(self):
        """
        Неавторизованный пользователь не должен получать данные
        """
        url = reverse('relations-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_manager_can_see_messages(self):
        """
        Проверяем, что менеджер получает только те сообщения, где он отправитель/получатель
        """
        self.api_client.login(username='manager', password='test12345')
        url = reverse('messages-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        # Менеджер в 2 сообщениях: sender в первом, receiver во втором
        self.assertEqual(len(response.data), 2)

    def test_client_can_see_messages(self):
        """
        Клиент получает только свои сообщения
        """
        self.api_client.login(username='client', password='test12345')
        url = reverse('messages-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        # Клиент в 2 сообщениях: sender во втором, receiver в первом
        self.assertEqual(len(response.data), 2)

    def test_anonymous_cannot_see_messages(self):
        """
        Неавторизованный пользователь не может видеть сообщения
        """
        url = reverse('messages-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_manager_sees_only_his_relations(self):
        """
        Проверяем, что менеджер видит только свою связь и не видит связь другого менеджера.
        """
        self.api_client.login(username='manager', password='test12345')
        url = reverse('relations-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        # Менеджер должен видеть только 1 связь
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['manager']['username'], 'manager')
        self.assertEqual(response.data[0]['client']['username'], 'client')

    def test_client_sees_only_his_relation(self):
        """
        Клиент видит только свою связь, но не связь 'other_client'.
        """
        self.api_client.login(username='client', password='test12345')
        url = reverse('relations-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['manager']['username'], 'manager')
        self.assertEqual(response.data[0]['client']['username'], 'client')

    def test_manager_sees_only_his_messages(self):
        """
        Менеджер видит только свои сообщения (message1, message2), но не сообщения пользователя 'other_manager'/'other_client'.
        """
        self.api_client.login(username='manager', password='test12345')
        url = reverse('messages-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 200)
        # У менеджера 2 связанных сообщения, сообщения 3 и 4 - не принадлежат ему
        self.assertEqual(len(response.data), 2)
        self.assertFalse(any(
            msg["content"] == "Привет от другого менеджера" for msg in
            response.data))

    def test_send_message_anonymously_not_allowed(self):
        """
        Проверяем, что неавторизованный пользователь не может получить доступ к списку сообщений.
        """
        url = reverse('messages-list')
        response = self.api_client.get(url)
        self.assertEqual(response.status_code, 403)


@override_settings(
    CHANNEL_LAYERS={
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }
)
class ChatConsumerTests(ChannelsLiveServerTestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            username='manager',
            password='test123',
            is_staff=True
        )
        self.client_user = User.objects.create_user(
            username='client',
            password='test123',
            is_staff=False
        )
        self.relation = ChatRelation.objects.create(
            manager=self.manager,
            client=self.client_user
        )
        # Создадим "левого" менеджера/клиента без связи
        self.other_manager = User.objects.create_user(
            username='other_manager',
            password='test123',
            is_staff=True
        )
        self.other_client = User.objects.create_user(
            username='other_client',
            password='test123',
            is_staff=False
        )

    async def test_manager_client_communication(self):
        """
        Тестируем, что при подключении менеджера и клиента к правильному WS-адресу и
        отправке сообщения, оба получают корректное уведомление через consumer.
        """
        # Авторизуемся менеджером
        manager_communicator = WebsocketCommunicator(
            application=application,
            path=f"/ws/chat/{self.manager.id}/{self.client_user.id}/",
        )
        manager_communicator.scope["user"] = self.manager

        # Авторизуемся клиентом
        client_communicator = WebsocketCommunicator(
            application=application,
            path=f"/ws/chat/{self.manager.id}/{self.client_user.id}/"
        )
        client_communicator.scope["user"] = self.client_user

        # Менеджер подключается
        connected, _ = await manager_communicator.connect()
        self.assertTrue(connected)

        # Клиент подключается
        connected, _ = await client_communicator.connect()
        self.assertTrue(connected)

        # Менеджер отправляет сообщение
        await manager_communicator.send_json_to(
            {"message": "Привет от менеджера"}
        )

        # Проверяем, что клиент получит сообщение
        response = await client_communicator.receive_json_from()
        self.assertEqual(response["sender_id"], self.manager.id)
        self.assertEqual(response["message"], "Привет от менеджера")

        # Клиент отправляет сообщение
        await client_communicator.send_json_to(
            {"message": "Привет от клиента"})

        first_response = await manager_communicator.receive_json_from()
        second_response = await manager_communicator.receive_json_from()
        self.assertEqual(second_response["sender_id"], self.client_user.id)
        self.assertEqual(second_response["message"], "Привет от клиента")

        # Закрываем соединения
        await manager_communicator.disconnect()
        await client_communicator.disconnect()

    async def test_connection_without_relation(self):
        """
        Проверяем, что если Relation нет, то пользователь не сможет подключиться (ChatConsumer закроет соединение).
        """
        # Попытаемся подключиться "левым" менеджером и "левым" клиентом
        communicator = WebsocketCommunicator(
            application=application,
            path=f"/ws/chat/{self.other_manager.id}/{self.other_client.id}/"
        )
        communicator.scope["user"] = self.other_manager
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
        # Закрываем соединения
        await communicator.disconnect()

    async def test_empty_message(self):
        """
        Проверяем, что при отправке пустого сообщения оно не рассылается по группе.
        Менеджер отправит пустое сообщение, клиент не получит никаких данных.
        """

        # Создаем WebsocketCommunicator для менеджера
        manager_communicator = WebsocketCommunicator(
            application=application,
            path=f"/ws/chat/{self.manager.id}/{self.client_user.id}/"
        )
        manager_communicator.scope["user"] = self.manager

        # Создаем WebsocketCommunicator для клиента
        client_communicator = WebsocketCommunicator(
            application=application,
            path=f"/ws/chat/{self.manager.id}/{self.client_user.id}/"
        )
        client_communicator.scope["user"] = self.client_user

        # Подключаемся
        connected, _ = await manager_communicator.connect()
        self.assertTrue(connected, "Менеджер не смог подключиться к сокету.")

        connected, _ = await client_communicator.connect()
        self.assertTrue(connected, "Клиент не смог подключиться к сокету.")

        # Менеджер отправляет пустое сообщение
        await manager_communicator.send_json_to({"message": ""})
        with self.assertRaises(asyncio.TimeoutError):
            await client_communicator.receive_json_from(timeout=1)

        # Отключаемся
        await manager_communicator.disconnect()
        await client_communicator.disconnect()
