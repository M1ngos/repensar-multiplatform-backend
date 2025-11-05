# Notifications API Reference

## Base URL

```
https://api.repensar.com/notifications
```

## Authentication

All endpoints require Bearer token authentication:

```
Authorization: Bearer {access_token}
```

---

## REST Endpoints

### List Notifications

Get paginated list of notifications for the current user.

```http
GET /notifications
```

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `unread_only` | boolean | `false` | Only return unread notifications |
| `limit` | integer | `50` | Maximum notifications to return (max: 100) |
| `offset` | integer | `0` | Offset for pagination |

**Response 200:**

```json
{
  "notifications": [
    {
      "id": 1,
      "user_id": 123,
      "title": "Task Assigned",
      "message": "You have been assigned to task: \"Build API\"",
      "type": "info",
      "related_project_id": 789,
      "related_task_id": 456,
      "is_read": false,
      "read_at": null,
      "created_at": "2025-11-05T10:00:00Z"
    }
  ],
  "total": 10,
  "limit": 50,
  "offset": 0,
  "unread_count": 3
}
```

**Notification Types:**
- `info` - General information
- `success` - Positive events (approval, completion)
- `warning` - Caution required (rejection, conflict)
- `error` - Error notifications

---

### Get Notification by ID

Get a specific notification.

```http
GET /notifications/{notification_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | integer | Notification ID |

**Response 200:**

```json
{
  "id": 1,
  "user_id": 123,
  "title": "Task Assigned",
  "message": "You have been assigned to task: \"Build API\"",
  "type": "info",
  "related_project_id": 789,
  "related_task_id": 456,
  "is_read": false,
  "read_at": null,
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Response 404:**

```json
{
  "detail": "Notification not found or access denied"
}
```

---

### Get Unread Count

Get the count of unread notifications.

```http
GET /notifications/unread-count
```

**Response 200:**

```json
{
  "unread_count": 3
}
```

---

### Mark Notification as Read

Mark a specific notification as read.

```http
PATCH /notifications/{notification_id}/read
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | integer | Notification ID |

**Response 200:**

```json
{
  "id": 1,
  "user_id": 123,
  "title": "Task Assigned",
  "message": "You have been assigned to task: \"Build API\"",
  "type": "info",
  "related_project_id": 789,
  "related_task_id": 456,
  "is_read": true,
  "read_at": "2025-11-05T10:30:00Z",
  "created_at": "2025-11-05T10:00:00Z"
}
```

**Response 404:**

```json
{
  "detail": "Notification not found or access denied"
}
```

---

### Mark All Notifications as Read

Mark all notifications as read for the current user.

```http
POST /notifications/mark-all-read
```

**Response 200:**

```json
{
  "marked_as_read": 3
}
```

---

### Delete Notification

Delete a specific notification.

```http
DELETE /notifications/{notification_id}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `notification_id` | integer | Notification ID |

**Response 200:**

```json
{
  "message": "Notification deleted successfully"
}
```

**Response 404:**

```json
{
  "detail": "Notification not found or access denied"
}
```

---

## Server-Sent Events (SSE)

### Stream Notifications

Establish a persistent connection to receive real-time notifications.

```http
GET /notifications/stream
```

**Headers:**

```
Accept: text/event-stream
Authorization: Bearer {access_token}
Cache-Control: no-cache
Connection: keep-alive
```

**Response (Streaming):**

The server sends events in the following format:

```
event: {event_type}
data: {json_data}

```

#### Event Types

##### 1. Connected Event

Sent immediately upon successful connection.

```
event: connected
data: {"user_id": 123, "connection_id": "abc-123-def-456"}

```

##### 2. Notification Event

Sent when a new notification is created.

```
event: notification
data: {
  "notification_id": 1,
  "user_id": 123,
  "title": "Task Assigned",
  "message": "You have been assigned to task: \"Build API\"",
  "type": "info",
  "related_project_id": 789,
  "related_task_id": 456,
  "created_at": "2025-11-05T10:00:00Z"
}

```

##### 3. Ping Event

Heartbeat sent every 30 seconds to keep connection alive.

```
event: ping
data: {"timestamp": "2025-11-05T10:00:00Z"}

```

---

## Client Examples

### JavaScript (Vanilla)

```javascript
// Create EventSource connection
const eventSource = new EventSource('/notifications/stream', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

// Handle connection
eventSource.addEventListener('connected', (event) => {
  const data = JSON.parse(event.data);
  console.log('Connected with ID:', data.connection_id);
});

// Handle notifications
eventSource.addEventListener('notification', (event) => {
  const notification = JSON.parse(event.data);

  // Display notification
  displayNotification(notification);

  // Update unread badge
  updateUnreadBadge();
});

// Handle heartbeat
eventSource.addEventListener('ping', (event) => {
  console.log('Connection alive');
});

// Handle errors
eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
  // Implement reconnection with exponential backoff
};

// Close when done
window.addEventListener('beforeunload', () => {
  eventSource.close();
});
```

### React Hook

```typescript
import { useEffect, useState, useCallback } from 'react';

interface Notification {
  notification_id: number;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  created_at: string;
}

export function useRealtimeNotifications(accessToken: string | null) {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!accessToken) return;

    let eventSource: EventSource | null = null;

    const connect = () => {
      eventSource = new EventSource('/notifications/stream', {
        headers: { Authorization: `Bearer ${accessToken}` }
      });

      eventSource.addEventListener('connected', () => {
        setIsConnected(true);
        console.log('SSE connected');
      });

      eventSource.addEventListener('notification', (event) => {
        const notification: Notification = JSON.parse(event.data);
        setNotifications(prev => [notification, ...prev]);

        // Show browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification(notification.title, {
            body: notification.message,
            icon: '/logo.png',
            tag: `notification-${notification.notification_id}`
          });
        }
      });

      eventSource.onerror = () => {
        setIsConnected(false);
        eventSource?.close();
        // Reconnect after 3 seconds
        setTimeout(connect, 3000);
      };
    };

    connect();

    return () => {
      eventSource?.close();
    };
  }, [accessToken]);

  return { notifications, isConnected };
}
```

### Python Client

```python
import sseclient
import requests
import json

def stream_notifications(access_token: str):
    """Stream notifications using SSE."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'text/event-stream'
    }

    response = requests.get(
        'http://localhost:8000/notifications/stream',
        headers=headers,
        stream=True
    )

    client = sseclient.SSEClient(response)

    for event in client.events():
        if event.event == 'connected':
            data = json.loads(event.data)
            print(f"Connected: {data['connection_id']}")

        elif event.event == 'notification':
            notification = json.loads(event.data)
            print(f"New notification: {notification['title']}")
            print(f"  {notification['message']}")

        elif event.event == 'ping':
            print("Heartbeat received")

# Usage
stream_notifications('your-access-token-here')
```

### curl (Testing)

```bash
# Stream notifications
curl -N -H "Accept: text/event-stream" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/notifications/stream

# List notifications
curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:8000/notifications?unread_only=true&limit=10"

# Mark as read
curl -X PATCH \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/notifications/1/read
```

---

## Rate Limits

| Endpoint | Rate Limit |
|----------|------------|
| `/notifications` (GET) | 100 requests/minute |
| `/notifications/stream` (GET) | 10 connections/user |
| `/notifications/{id}/read` (PATCH) | 100 requests/minute |
| `/notifications/mark-all-read` (POST) | 10 requests/minute |

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Not authorized to access resource |
| 404 | Not Found - Resource does not exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

---

## WebSocket Alternative (Future)

Currently, the system uses SSE for simplicity. If bidirectional communication is needed in the future, WebSocket support can be added:

```javascript
// Future WebSocket implementation
const ws = new WebSocket('ws://api.repensar.com/ws/notifications');

ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  console.log('Received:', notification);
};

// Send acknowledgment
ws.send(JSON.stringify({
  type: 'ack',
  notification_id: 123
}));
```

---

## Best Practices

### Client-Side

1. **Reconnection Strategy:**
   ```javascript
   let retryCount = 0;
   const maxRetries = 5;
   const baseDelay = 1000;

   function connect() {
     const eventSource = new EventSource('/notifications/stream');

     eventSource.onerror = () => {
       eventSource.close();

       if (retryCount < maxRetries) {
         const delay = baseDelay * Math.pow(2, retryCount);
         setTimeout(connect, delay);
         retryCount++;
       }
     };
   }
   ```

2. **Handle Network Changes:**
   ```javascript
   window.addEventListener('online', () => {
     // Reconnect when network comes back
     connect();
   });

   window.addEventListener('offline', () => {
     eventSource?.close();
   });
   ```

3. **Battery Optimization (Mobile):**
   ```javascript
   // Reduce heartbeat frequency when on battery
   if ('getBattery' in navigator) {
     navigator.getBattery().then(battery => {
       if (battery.charging === false && battery.level < 0.2) {
         // Close SSE and fall back to polling
         eventSource.close();
         startPolling();
       }
     });
   }
   ```

### Server-Side

1. **Use sticky sessions** for load balancing SSE endpoints
2. **Set nginx timeout** to > 5 minutes for SSE
3. **Monitor active connections** to prevent resource exhaustion
4. **Implement connection limits** per user (default: 10)

---

## Testing

### Manual Testing

```bash
# Terminal 1: Start SSE stream
curl -N -H "Accept: text/event-stream" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/notifications/stream

# Terminal 2: Trigger notification (assign task, update project, etc.)
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"volunteer_id": 1}' \
     http://localhost:8000/tasks/1/volunteers

# Terminal 1 should receive notification immediately
```

### Automated Testing

```python
import pytest
from fastapi.testclient import TestClient

def test_sse_stream(client: TestClient, auth_headers):
    """Test SSE notification streaming."""
    with client.stream("GET", "/notifications/stream", headers=auth_headers) as response:
        # Should receive connected event
        for line in response.iter_lines():
            if b"event: connected" in line:
                break

        # Create notification in another thread/process
        # Should receive notification event
        for line in response.iter_lines():
            if b"event: notification" in line:
                break
```
