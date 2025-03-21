from django.db import models
from django.contrib.auth.models import User


class ChatRelation(models.Model):
    """
    Модель для связи между менеджером и клиентом.
    """
    manager = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='manager_relations')
    client = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='client_relations')

    def __str__(self):
        return f"{self.client.username} -> {self.manager.username}"


class ChatMessage(models.Model):
    """
    Модель для хранения сообщений.
    """
    sender = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"От {self.sender} к {self.receiver}: {self.content[:20]}"
