# Messaging System

Two-way communication system for the Farm Management System with role-based permissions.

## Communication Rules

The system enforces the following communication hierarchy:

- **Owner ↔ Manager** (bidirectional)
- **Manager ↔ Field Officer** (bidirectional)
- **Field Officer ↔ Manager ↔ Owner** (Field Officer can message both Manager and Owner)
- **Field Officer ↔ Farmer** (bidirectional)
- **Farmer ↔ Field Officer** (bidirectional)

Additionally:
- **Manager ↔ Farmer** (Manager can message farmers through field officers)
- **Owner ↔ Farmer** (Owner can message farmers through hierarchy)

## API Endpoints

### Conversations

#### List All Conversations
```
GET /api/conversations/
```
Returns all conversations for the authenticated user.

#### Get Conversation with Specific User
```
GET /api/conversations/with-user/{user_id}/
```
Get or create a conversation with a specific user.

#### Get Messages in Conversation
```
GET /api/conversations/{id}/messages/
```
Get all messages in a specific conversation.

#### Mark Conversation as Read
```
POST /api/conversations/{id}/mark-read/
```
Mark all unread messages in a conversation as read.

### Messages

#### Send a Message
```
POST /api/messages/
Body: {
    "recipient_id": 123,
    "content": "Your message here"
}
```
Send a new message to a user. Creates a conversation if it doesn't exist.

#### List All Messages
```
GET /api/messages/
```
Get all messages for the authenticated user (across all conversations).

#### Get Unread Count
```
GET /api/messages/unread-count/
```
Get total count of unread messages.

#### Get Unread Messages
```
GET /api/messages/unread/
```
Get all unread messages.

#### Mark Message as Read
```
POST /api/messages/{id}/mark-read/
```
Mark a specific message as read.

## Example Usage

### Send a Message
```python
import requests

url = "http://localhost:8000/api/messages/"
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "recipient_id": 5,
    "content": "Hello, how are you?"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Get Conversations
```python
url = "http://localhost:8000/api/conversations/"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

response = requests.get(url, headers=headers)
conversations = response.json()
print(conversations)
```

### Get Messages in a Conversation
```python
url = "http://localhost:8000/api/conversations/1/messages/"
headers = {"Authorization": "Bearer YOUR_JWT_TOKEN"}

response = requests.get(url, headers=headers)
messages = response.json()
print(messages)
```

## Response Format

### Conversation Object
```json
{
    "id": 1,
    "participant1": {
        "id": 1,
        "username": "owner1",
        "first_name": "John",
        "last_name": "Doe",
        "email": "owner@example.com",
        "role_name": "owner",
        "role_display": "Owner"
    },
    "participant2": {
        "id": 2,
        "username": "manager1",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "manager@example.com",
        "role_name": "manager",
        "role_display": "Manager"
    },
    "other_participant": {
        "id": 2,
        "username": "manager1",
        ...
    },
    "last_message": {
        "id": 10,
        "sender": {...},
        "content": "Latest message",
        "is_read": false,
        "created_at": "2025-11-18T10:30:00Z"
    },
    "unread_count": 3,
    "created_at": "2025-11-18T09:00:00Z",
    "updated_at": "2025-11-18T10:30:00Z",
    "last_message_at": "2025-11-18T10:30:00Z"
}
```

### Message Object
```json
{
    "id": 1,
    "conversation": 1,
    "sender": {
        "id": 1,
        "username": "owner1",
        "first_name": "John",
        "last_name": "Doe",
        "role_name": "owner"
    },
    "content": "Hello, this is a message",
    "read_at": null,
    "is_read": false,
    "created_at": "2025-11-18T10:00:00Z",
    "updated_at": "2025-11-18T10:00:00Z"
}
```

## Permissions

The system automatically enforces communication rules based on user roles. If a user tries to send a message to someone they're not allowed to communicate with, they will receive a `403 Forbidden` response.

## Admin Interface

The messaging system is available in the Django admin interface at `/admin/`:
- View all conversations
- View all messages
- Filter by read/unread status
- Search by user or content

