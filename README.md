# README по эндпоинтам и WebSocket чату


## Структура приложения

Проект построен с использованием Django REST Framework и Django Channels для реализации вебсокетов. Основные сущности:
1. **ChatRelation** – описывает связь между менеджером и клиентом.
2. **ChatMessage** – модель для хранения сообщений между пользователями.
3. **ChatMessageViewSet** и **ChatRelationViewSet** – viewset'ы для работы с соответствующими моделями через API.
4. **ChatConsumer** – класс для обработки WebSocket-соединений.


## ViewSet'ы (эндпоинты)

### ChatMessageViewSet

Эндпоинты для работы с сообщениями:
- `GET /messages/`
  - Возвращает список всех сообщений текущего пользователя (где он отправитель или получатель).
- `GET /messages/<int:id>/`
  - Возвращает конкретное сообщение текущего пользователя по `id`.

### ChatRelationViewSet

Эндпоинты для работы со связями:
- `GET /relations/`
  - Возвращает список всех связей для текущего пользователя (в зависимости от роли).
- `GET /relations/<int:id>/`
  - Возвращает конкретную связь по `id`.


## WebSocket (ChatConsumer)

Для обмена сообщениями в реальном времени используется класс `ChatConsumer`.  
Подключение происходит по следующему адресу:  
```
ws://<ваш-домен>/ws/chat/<manager_id>/<client_id>/
```
Либо:
```
wss://<ваш-домен>/ws/chat/<manager_id>/<client_id>/
```


Этот consumer:
1. Проверяет, может ли пользователь присоединиться к чату (существует ли связь `ChatRelation`).
2. При получении сообщения от клиента создает запись `ChatMessage` в базе.
3. Отправляет сообщение всем подключенным клиентам в заданной комнате.



## Пример взаимодействия

### 1. Получение списка сообщений (REST)
```bash
GET /messages/
Authorization: Token <ваш_токен>
```
Ответ (JSON):
```json
[
  {
    "id": 1,
    "sender": {
      "id": 2,
      "username": "manager",
      "is_staff": true,
      "email": "manager@example.com"
    },
    "receiver": {
      "id": 3,
      "username": "client",
      "is_staff": false,
      "email": "client@example.com"
    },
    "content": "Привет!",
    "timestamp": "2023-01-01T12:00:00Z"
  },
  ...
]
```

### 2. Получение своих связей (REST)
```bash
GET /relations/
Authorization: Token <ваш_токен>
```
Ответ (JSON):
```json
[
  {
    "id": 1,
    "manager": {
      "id": 2,
      "username": "manager",
      "is_staff": true,
      "email": "manager@example.com"
    },
    "client": {
      "id": 3,
      "username": "client",
      "is_staff": false,
      "email": "client@example.com"
    }
  },
  ...
]
```


При каждом новом сообщении клиент (или менеджер) отправляет JSON вида:
```json
{ "message": "Привет!" }
```
И получатель получает от сервера:
```json
{
  "sender_id": 3,
  "message": "Привет!"
}
```
где `sender_id` – идентификатор отправителя.

## Требования к аутентификации
- Rest API требует авторизации (по умолчанию `permissions.IsAuthenticated`).
- WebSocket соединение использует `AuthMiddlewareStack`, поэтому пользователь должен быть авторизован через сессию Django или другой метод аутентификации, поддерживаемый Channels.

## Запуск тестов
```bash
python manage.py test
```

## Что делают тесты

1. Проверяют REST API для чата:
   - Проверка доступа к списку диалогов (ChatRelation) для менеджера и клиента.
   - Проверка видимости сообщений (ChatMessage) в зависимости от роли пользователя.
   - Проверка отказа доступа неавторизованным пользователям.

2. Тестируют WebSocket-подключение (Channels):
   - Возможность отправки сообщений между менеджером и клиентом.
   - Проверка недоступности чата, если нет соответствующей связи (ChatRelation).
   - Проверка игнорирования пустых сообщений.
