from rest_framework import viewsets, permissions
from .models import ChatMessage, ChatRelation
from .serializers import ChatMessageSerializer, ChatRelationSerializer


class ChatMessageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return ChatMessage.objects.filter(
            sender=user) | ChatMessage.objects.filter(receiver=user)


class ChatRelationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ChatRelationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return ChatRelation.objects.filter(manager=user)
        else:
            return ChatRelation.objects.filter(client=user)


# Пример реализации ChatRelationViewSet с использованием ModelViewSet для
# создания отношений между клиентом и менеджером.
# /relations/ отправить POST-запрос вида:
#
# {
#   "manager_id": 2,
#   "client_id": 5
# }
# чтобы создать связь (ChatRelation) между пользователями
# class ChatRelationViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet для управления (чтения/создания ChatRelation.
#     Условие: создавать отношения может только менеджер (пользователь с is_staff=True).
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
#
#     def create(self, request, *args, kwargs):
#         # Проверяем, что пользователь - менеджер
#         if not request.user.is_staff:
#             return Response(
#                 {"detail": "Только менеджер может создавать новые связи."},
#                 status=status.HTTP_403_FORBIDDEN
#             )
#         manager_id = request.data.get('manager_id')
#         client_id = request.data.get('client_id')
#         if not manager_id or not client_id:
#             return Response(
#                 {"detail": "Необходимо передать manager_id и client_id"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#
#         try:
#             manager = User.objects.get(pk=manager_id)
#             client = User.objects.get(pk=client_id)
#         except User.DoesNotExist:
#             return Response(
#                 {"detail": "Менеджер или клиент с указанными ID не найдены"},
#                 status=status.HTTP_404_NOT_FOUND
#             )
#         relation = ChatRelation.objects.create(manager=manager, client=client)
#         serializer = self.get_serializer(relation)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
