from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import ChatMessage, ChatRelation
from .serializers import ChatMessageSerializer, ChatRelationSerializer


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для чтения сообщений чата.
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        )


# class ChatRelationViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     ViewSet для чтения отношений между клиентами и менеджерами.
#     """
#     serializer_class = ChatRelationSerializer
#     permission_classes = [permissions.IsAuthenticated]
#
#     def get_queryset(self):
#         user = self.request.user
#         if user.is_staff:
#             return ChatRelation.objects.filter(manager=user)
#         else:
#             return ChatRelation.objects.filter(client=user)


# Пример реализации ChatRelationViewSet с использованием ModelViewSet для
# создания отношений между клиентом и менеджером.
# /relations/ отправить POST-запрос вида:
#
# {
#   "manager_id": 2,
#   "client_id": 5
# }
# чтобы создать связь (ChatRelation) между пользователями
class ChatRelationViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления (чтения/создания/изменения/удаления) ChatRelation.
    Условие: создавать, изменять и удалять отношения (чаты) может только менеджер (пользователь с is_staff=True).
    """
    serializer_class = ChatRelationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ChatRelation.objects.filter(manager=user)
        else:
            return ChatRelation.objects.filter(client=user)

    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response(
                {"detail": "Только менеджер может создавать новые связи."},
                status=status.HTTP_403_FORBIDDEN
            )
        manager_id = request.data.get('manager_id')
        client_id = request.data.get('client_id')
        if not manager_id or not client_id:
            return Response(
                {"detail": "Необходимо передать manager_id и client_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            manager = User.objects.get(pk=manager_id)
            client = User.objects.get(pk=client_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Менеджер или клиент с указанными ID не найдены"},
                status=status.HTTP_404_NOT_FOUND
            )
        relation = ChatRelation.objects.create(manager=manager, client=client)
        serializer = self.get_serializer(relation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Обновление (изменение) существующего чата. Можно менять только
        клиента.
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Только менеджер может изменять чат."},
                status=status.HTTP_403_FORBIDDEN
            )
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """
        Удаление чата.
        """
        if not request.user.is_staff:
            return Response(
                {"detail": "Только менеджер может удалять чат."},
                status=status.HTTP_403_FORBIDDEN
            )
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
