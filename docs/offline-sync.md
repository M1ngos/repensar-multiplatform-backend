# Offline-First Sync Architecture

## Overview

The Repensar backend provides a complete offline-first synchronization system that enables desktop and mobile applications to work without an internet connection. When the connection is restored, local changes are automatically synchronized with the server.

### Key Features

- ✅ **Incremental Sync**: Only changed data is transferred
- ✅ **Conflict Detection**: Automatic detection of concurrent edits
- ✅ **Optimistic Locking**: Version-based conflict prevention
- ✅ **Soft Deletes**: Deleted items sync across devices
- ✅ **Device Management**: Register, track, and revoke devices
- ✅ **Per-Device Sync State**: Each device tracks its own sync status
- ✅ **Bandwidth Optimization**: Minimal data transfer with timestamps
- ✅ **Multi-Platform**: Android, iOS, Desktop (macOS, Windows, Linux), Web

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT APPLICATION                        │
│  (Android, iOS, Desktop - macOS/Windows/Linux)              │
├─────────────────────────────────────────────────────────────┤
│  1. Local SQLite Database (same schema as server)           │
│  2. Pending Operations Queue (CREATE/UPDATE/DELETE)         │
│  3. Sync Manager (handles push/pull)                        │
│  4. Conflict Resolver (UI + logic)                          │
│  5. JWT Token Storage (Keychain/Keystore)                   │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                    BACKEND SERVER                            │
│              FastAPI + PostgreSQL + Redis                    │
├─────────────────────────────────────────────────────────────┤
│  Device Model:        Track registered devices               │
│  DeviceSyncState:     Per-device, per-entity sync state     │
│  SyncConflict:        Conflict logging and resolution       │
│  Entity Models:       Volunteer, Project, Task, etc.        │
└─────────────────────────────────────────────────────────────┘
```

### Database Models

#### Device
Represents a registered client device.

```python
# app/models/sync.py
class Device(SQLModel, table=True):
    device_id: str           # UUID from client (primary key)
    user_id: int             # Foreign key to User
    device_name: str         # "John's iPhone"
    device_type: DeviceType  # android, ios, desktop, web
    platform: DevicePlatform # android, ios, macos, windows, linux, web
    os_version: str          # "iOS 17.2", "Windows 11"
    app_version: str         # "2.0.0"
    push_token: str          # FCM/APNS token
    last_sync_at: datetime   # When device last synced
    last_seen_at: datetime   # When device last connected
    is_active: bool          # For device revocation
    registered_at: datetime  # When device was registered
```

#### DeviceSyncState
Tracks sync state per device per entity type.

```python
class DeviceSyncState(SQLModel, table=True):
    device_id: str           # Foreign key to Device
    entity_type: str         # "volunteer", "project", "task", etc.
    last_synced_at: datetime # Last successful sync timestamp
    last_synced_version: int # Last synced version number
    sync_metadata: dict      # Custom filters, preferences
```

#### SyncConflict
Logs detected conflicts for debugging and manual resolution.

```python
class SyncConflict(SQLModel, table=True):
    device_id: str              # Foreign key to Device
    entity_type: str            # "volunteer", "project", etc.
    entity_id: str              # ID of conflicting entity
    conflict_type: str          # "version_mismatch"
    client_version: int         # Client's version
    server_version: int         # Server's version
    client_data: dict           # Client's data
    server_data: dict           # Server's data
    client_timestamp: datetime  # When client modified
    server_timestamp: datetime  # When server modified
    resolution: ConflictResolution  # client_wins, server_wins, manual
    resolved_at: datetime       # When resolved
```

---

## Authentication in Offline Mode

### JWT Token Management

The backend uses JWT tokens for authentication (`app/core/token_manager.py`):

- **Access Token**: 30 minutes (configurable)
- **Refresh Token**: 30 days (configurable)
- **Token Rotation**: New refresh token on each use
- **Token Blacklist**: Redis-backed revocation

### Offline Authentication Strategy

#### 1. Initial Authentication (Online Required)

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

#### 2. Store Tokens Securely

**iOS**: Keychain
```swift
let keychain = KeychainSwift()
keychain.set(accessToken, forKey: "access_token")
keychain.set(refreshToken, forKey: "refresh_token")
```

**Android**: Keystore + EncryptedSharedPreferences
```kotlin
val encryptedPrefs = EncryptedSharedPreferences.create(...)
encryptedPrefs.edit().putString("access_token", accessToken).apply()
```

**Desktop**: OS Credential Manager
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service (libsecret)

#### 3. Offline Token Validation

When offline, validate tokens locally without contacting the server:

```typescript
// Client-side pseudocode
async function validateOfflineAuth(): Promise<boolean> {
  const accessToken = await getStoredToken('access')

  if (!accessToken) return false

  try {
    // Decode JWT without signature verification (trust local storage)
    const payload = decodeJWT(accessToken, { verify: false })

    // Check if expired
    if (Date.now() < payload.exp * 1000) {
      // Token still valid, allow offline access
      return true
    }

    // Token expired, try refresh if online
    if (await isOnline()) {
      return await refreshToken()
    }

    // Offline and expired - show limited access or require login
    return false

  } catch (error) {
    return false
  }
}
```

#### 4. Security Considerations

**Offline Mode Limitations**:
- Cannot check token blacklist (revocation)
- Cannot detect token reuse attacks
- Cannot verify signature without server

**Mitigation Strategies**:
1. **Short Access Token Lifetime**: Default 30 minutes
2. **Sync on Reconnect**: Validate token blacklist when online
3. **Block Sensitive Operations**: Require online for:
   - Password changes
   - Account deletion
   - Permission changes
   - OAuth re-authentication

**Allowed Offline Operations**:
- View cached data
- Create/edit volunteers, projects, tasks
- Log time entries
- Most CRUD operations (queued for sync)

---

## API Endpoints

### Base URL
```
https://api.repensar.com/sync
```

### 1. Device Registration

#### POST /sync/device/register

Register or update a device for sync.

**Request**:
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_name": "John's iPhone",
  "device_type": "ios",
  "platform": "ios",
  "os_version": "17.2",
  "app_version": "2.0.0",
  "push_token": "fcm_token_or_apns_token"
}
```

**Response**:
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "registered_at": "2025-10-27T12:00:00Z",
  "last_sync_at": null,
  "message": "Device registered successfully"
}
```

**Headers**:
```
Authorization: Bearer <access_token>
```

---

### 2. List Devices

#### GET /sync/device/list

Get all devices for the authenticated user.

**Query Parameters**:
- `include_inactive` (bool): Include revoked devices (default: false)

**Response**:
```json
{
  "devices": [
    {
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "device_name": "John's iPhone",
      "device_type": "ios",
      "platform": "ios",
      "os_version": "17.2",
      "app_version": "2.0.0",
      "last_sync_at": "2025-10-27T12:00:00Z",
      "last_seen_at": "2025-10-27T12:05:00Z",
      "is_active": true,
      "registered_at": "2025-10-20T10:00:00Z"
    }
  ],
  "total": 1
}
```

---

### 3. Revoke Device

#### POST /sync/device/{device_id}/revoke

Revoke a device (e.g., lost phone). Forces re-authentication.

**Response**:
```json
{
  "message": "Device 'John's iPhone' revoked successfully",
  "device_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### 4. Pull Changes (Server → Client)

#### POST /sync/pull

Pull changes from server since last sync.

**Request**:
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "entity_types": ["volunteer", "project", "task"],
  "since": "2025-10-27T10:00:00Z",
  "limit": 100
}
```

**Parameters**:
- `device_id`: Your device UUID
- `entity_types`: Array of entity types to sync
- `since`: Timestamp of last sync (null = full sync)
- `limit`: Max changes per entity type (1-1000, default 100)

**Response**:
```json
{
  "changes": [
    {
      "entity_type": "volunteer",
      "entity_id": "456",
      "operation": "UPDATE",
      "data": {
        "id": 456,
        "name": "Jane Doe",
        "email": "jane@example.com",
        "updated_at": "2025-10-27T11:30:00Z"
      },
      "version": 10,
      "modified_at": "2025-10-27T11:30:00Z",
      "modified_by_device_id": "other-device-uuid"
    },
    {
      "entity_type": "project",
      "entity_id": "789",
      "operation": "DELETE",
      "data": {},
      "version": 5,
      "modified_at": "2025-10-27T11:45:00Z",
      "modified_by_device_id": null
    }
  ],
  "sync_token": "2025-10-27T12:00:00Z",
  "has_more": false,
  "total_changes": 2
}
```

**Client Logic After Pull**:
```typescript
async function handlePullResponse(response: SyncPullResponse) {
  const db = await getLocalDatabase()

  for (const change of response.changes) {
    if (change.operation === 'DELETE') {
      await db.delete(change.entity_type, change.entity_id)
    } else {
      await db.upsert(change.entity_type, change.data)
    }
  }

  // Store sync_token for next pull
  await setSyncToken(response.sync_token)

  // If has_more, fetch next page
  if (response.has_more) {
    await pullChanges({ since: response.sync_token })
  }
}
```

---

### 5. Push Changes (Client → Server)

#### POST /sync/push

Push local changes to server with conflict detection.

**Request**:
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "changes": [
    {
      "entity_type": "volunteer",
      "entity_id": "123",
      "operation": "UPDATE",
      "data": {
        "id": 123,
        "name": "John Smith",
        "email": "john.smith@example.com"
      },
      "version": 5,
      "modified_at": "2025-10-27T11:30:00Z",
      "modified_by_device_id": "550e8400-e29b-41d4-a716-446655440000"
    }
  ]
}
```

**Response (Success)**:
```json
{
  "applied": 1,
  "conflicts": [],
  "failed": 0,
  "sync_token": "2025-10-27T12:00:00Z"
}
```

**Response (With Conflicts)**:
```json
{
  "applied": 0,
  "conflicts": [
    {
      "conflict_id": "999",
      "entity_type": "volunteer",
      "entity_id": "123",
      "client_version": 5,
      "server_version": 8,
      "client_data": { "name": "John Smith" },
      "server_data": { "name": "Jonathan Smith" },
      "client_modified_at": "2025-10-27T11:30:00Z",
      "server_modified_at": "2025-10-27T11:45:00Z",
      "conflict_type": "version_mismatch",
      "suggested_resolution": "server_wins"
    }
  ],
  "failed": 0,
  "sync_token": "2025-10-27T12:00:00Z"
}
```

---

### 6. Get Conflicts

#### GET /sync/conflicts

Get all sync conflicts for user's devices.

**Query Parameters**:
- `device_id` (optional): Filter by device
- `unresolved_only` (bool): Only unresolved conflicts (default: true)

**Response**:
```json
{
  "conflicts": [
    {
      "conflict_id": "999",
      "entity_type": "volunteer",
      "entity_id": "123",
      "client_version": 5,
      "server_version": 8,
      "client_data": { "name": "John Smith" },
      "server_data": { "name": "Jonathan Smith" },
      "client_modified_at": "2025-10-27T11:30:00Z",
      "server_modified_at": "2025-10-27T11:45:00Z",
      "conflict_type": "version_mismatch",
      "suggested_resolution": "server_wins"
    }
  ],
  "total": 1,
  "unresolved": 1
}
```

---

### 7. Resolve Conflict

#### POST /sync/conflicts/{conflict_id}/resolve

Manually resolve a conflict.

**Request**:
```json
{
  "resolution": "client_wins",
  "merged_data": null
}
```

**Resolution Options**:
- `client_wins`: Use client data (overwrite server)
- `server_wins`: Keep server data (discard client changes)
- `manual`: Use custom merged data (provide `merged_data`)

**Response**:
```json
{
  "message": "Conflict resolved successfully",
  "conflict_id": "999",
  "resolution": "client_wins",
  "entity_type": "volunteer",
  "entity_id": "123"
}
```

---

### 8. Sync Status

#### GET /sync/status?device_id={device_id}

Get comprehensive sync status for a device.

**Response**:
```json
{
  "device": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_name": "John's iPhone",
    "device_type": "ios",
    "platform": "ios",
    "last_sync_at": "2025-10-27T12:00:00Z",
    "is_active": true
  },
  "sync_states": [
    {
      "entity_type": "volunteer",
      "last_synced_at": "2025-10-27T12:00:00Z",
      "last_synced_version": 150,
      "total_entities": null
    }
  ],
  "pending_conflicts": 0,
  "needs_sync": false,
  "last_successful_sync": "2025-10-27T12:00:00Z"
}
```

---

## Client Implementation Guide

### Sync Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    FULL SYNC FLOW                            │
└─────────────────────────────────────────────────────────────┘

1. App Launch / Connectivity Restored
   ↓
2. Register Device (if not registered)
   ↓
3. Pull Changes from Server
   ├─ For each entity type: volunteer, project, task, etc.
   ├─ Use last sync timestamp (stored locally)
   ├─ Apply changes to local DB
   └─ Update local sync timestamp
   ↓
4. Push Local Changes to Server
   ├─ Get pending operations from local queue
   ├─ Send to server
   ├─ Handle conflicts if any
   └─ Clear successful operations from queue
   ↓
5. Update Sync Status
   └─ Store last successful sync time
```

### Android (Kotlin) Example

```kotlin
// SyncManager.kt
class SyncManager(
    private val apiClient: ApiClient,
    private val localDatabase: AppDatabase,
    private val deviceInfo: DeviceInfo
) {
    suspend fun performSync(): SyncResult {
        try {
            // 1. Register device
            registerDevice()

            // 2. Pull changes from server
            val pullResult = pullChanges()
            applyChangesToLocalDB(pullResult.changes)

            // 3. Push local changes to server
            val pendingChanges = localDatabase.getPendingChanges()
            val pushResult = pushChanges(pendingChanges)

            // 4. Handle conflicts
            if (pushResult.conflicts.isNotEmpty()) {
                handleConflicts(pushResult.conflicts)
            }

            // 5. Update sync state
            updateSyncState(pullResult.sync_token)

            return SyncResult.Success

        } catch (e: Exception) {
            return SyncResult.Error(e.message)
        }
    }

    private suspend fun registerDevice() {
        val request = DeviceRegistration(
            device_id = getDeviceUUID(),
            device_name = "${Build.MANUFACTURER} ${Build.MODEL}",
            device_type = "android",
            platform = "android",
            os_version = Build.VERSION.RELEASE,
            app_version = BuildConfig.VERSION_NAME,
            push_token = getFCMToken()
        )

        apiClient.registerDevice(request)
    }

    private suspend fun pullChanges(): SyncPullResponse {
        val lastSyncTime = localDatabase.getLastSyncTime()

        val request = SyncPullRequest(
            device_id = getDeviceUUID(),
            entity_types = listOf("volunteer", "project", "task"),
            since = lastSyncTime,
            limit = 100
        )

        return apiClient.pullChanges(request)
    }

    private suspend fun applyChangesToLocalDB(changes: List<EntityChange>) {
        localDatabase.withTransaction {
            for (change in changes) {
                when (change.operation) {
                    Operation.DELETE -> {
                        localDatabase.delete(change.entity_type, change.entity_id)
                    }
                    Operation.UPDATE, Operation.CREATE -> {
                        localDatabase.upsert(change.entity_type, change.data)
                    }
                }
            }
        }
    }

    private suspend fun handleConflicts(conflicts: List<ConflictData>) {
        // Show UI to user for manual resolution
        // or apply automatic resolution strategy
        for (conflict in conflicts) {
            // Example: Server always wins
            resolveConflict(conflict.conflict_id, Resolution.SERVER_WINS)
        }
    }
}

// Usage in Activity/ViewModel
class MainActivity : AppCompatActivity() {
    private val syncManager: SyncManager by inject()

    override fun onResume() {
        super.onResume()

        // Sync when app comes to foreground
        lifecycleScope.launch {
            if (isNetworkAvailable()) {
                syncManager.performSync()
            }
        }
    }
}
```

### iOS (Swift) Example

```swift
// SyncManager.swift
class SyncManager {
    private let apiClient: APIClient
    private let localDatabase: Database
    private let deviceInfo: DeviceInfo

    func performSync() async throws -> SyncResult {
        // 1. Register device
        try await registerDevice()

        // 2. Pull changes
        let pullResponse = try await pullChanges()
        try await applyChangesToLocalDB(pullResponse.changes)

        // 3. Push local changes
        let pendingChanges = try await localDatabase.getPendingChanges()
        let pushResponse = try await pushChanges(pendingChanges)

        // 4. Handle conflicts
        if !pushResponse.conflicts.isEmpty {
            try await handleConflicts(pushResponse.conflicts)
        }

        // 5. Update sync state
        try await updateSyncState(pullResponse.syncToken)

        return .success
    }

    private func registerDevice() async throws {
        let request = DeviceRegistration(
            deviceId: getDeviceUUID(),
            deviceName: UIDevice.current.name,
            deviceType: "ios",
            platform: "ios",
            osVersion: UIDevice.current.systemVersion,
            appVersion: Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String,
            pushToken: getAPNSToken()
        )

        try await apiClient.registerDevice(request)
    }

    private func pullChanges() async throws -> SyncPullResponse {
        let lastSyncTime = try await localDatabase.getLastSyncTime()

        let request = SyncPullRequest(
            deviceId: getDeviceUUID(),
            entityTypes: ["volunteer", "project", "task"],
            since: lastSyncTime,
            limit: 100
        )

        return try await apiClient.pullChanges(request)
    }

    private func applyChangesToLocalDB(_ changes: [EntityChange]) async throws {
        try await localDatabase.transaction {
            for change in changes {
                switch change.operation {
                case .delete:
                    try await localDatabase.delete(change.entityType, id: change.entityId)
                case .update, .create:
                    try await localDatabase.upsert(change.entityType, data: change.data)
                }
            }
        }
    }
}

// Usage in App
@main
struct RepenserApp: App {
    @StateObject private var syncManager = SyncManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .task {
                    if NetworkMonitor.shared.isConnected {
                        try? await syncManager.performSync()
                    }
                }
                .onReceive(NetworkMonitor.shared.$isConnected) { isConnected in
                    if isConnected {
                        Task {
                            try? await syncManager.performSync()
                        }
                    }
                }
        }
    }
}
```

### Desktop (Electron/Tauri) Example

```typescript
// syncManager.ts
export class SyncManager {
  constructor(
    private apiClient: ApiClient,
    private localDB: Database,
    private deviceInfo: DeviceInfo
  ) {}

  async performSync(): Promise<SyncResult> {
    try {
      // 1. Register device
      await this.registerDevice()

      // 2. Pull changes
      const pullResponse = await this.pullChanges()
      await this.applyChangesToLocalDB(pullResponse.changes)

      // 3. Push local changes
      const pendingChanges = await this.localDB.getPendingChanges()
      const pushResponse = await this.pushChanges(pendingChanges)

      // 4. Handle conflicts
      if (pushResponse.conflicts.length > 0) {
        await this.handleConflicts(pushResponse.conflicts)
      }

      // 5. Update sync state
      await this.updateSyncState(pullResponse.sync_token)

      return { success: true }
    } catch (error) {
      return { success: false, error }
    }
  }

  private async registerDevice() {
    const request: DeviceRegistration = {
      device_id: await this.getDeviceUUID(),
      device_name: os.hostname(),
      device_type: 'desktop',
      platform: process.platform, // 'darwin', 'win32', 'linux'
      os_version: os.release(),
      app_version: app.getVersion(),
      push_token: null
    }

    await this.apiClient.registerDevice(request)
  }

  private async pullChanges(): Promise<SyncPullResponse> {
    const lastSyncTime = await this.localDB.getLastSyncTime()

    const request: SyncPullRequest = {
      device_id: await this.getDeviceUUID(),
      entity_types: ['volunteer', 'project', 'task'],
      since: lastSyncTime,
      limit: 100
    }

    return await this.apiClient.pullChanges(request)
  }

  private async applyChangesToLocalDB(changes: EntityChange[]) {
    await this.localDB.transaction(async (tx) => {
      for (const change of changes) {
        if (change.operation === 'DELETE') {
          await tx.delete(change.entity_type, change.entity_id)
        } else {
          await tx.upsert(change.entity_type, change.data)
        }
      }
    })
  }

  private async handleConflicts(conflicts: ConflictData[]) {
    // Show dialog to user for manual resolution
    for (const conflict of conflicts) {
      const resolution = await showConflictDialog(conflict)
      await this.apiClient.resolveConflict(conflict.conflict_id, resolution)
    }
  }
}

// Usage in main app
import { app } from 'electron'

app.on('ready', async () => {
  const syncManager = new SyncManager(apiClient, localDB, deviceInfo)

  // Sync on startup
  await syncManager.performSync()

  // Sync every 5 minutes if online
  setInterval(async () => {
    if (navigator.onLine) {
      await syncManager.performSync()
    }
  }, 5 * 60 * 1000)
})
```

---

## Conflict Resolution Strategies

### 1. Last-Write-Wins (LWW)

Use timestamp to determine winner.

```typescript
function resolveConflictLWW(conflict: ConflictData): Resolution {
  if (conflict.client_modified_at > conflict.server_modified_at) {
    return 'client_wins'
  } else {
    return 'server_wins'
  }
}
```

**Pros**: Simple, automatic
**Cons**: Can lose data if timestamps are close

### 2. Server Always Wins

Default strategy for safety.

```typescript
function resolveConflictServerWins(conflict: ConflictData): Resolution {
  return 'server_wins'
}
```

**Pros**: Never overwrites server data
**Cons**: Client changes lost

### 3. Client Always Wins

Useful for user-initiated changes.

```typescript
function resolveConflictClientWins(conflict: ConflictData): Resolution {
  return 'client_wins'
}
```

**Pros**: User changes preserved
**Cons**: Can overwrite important server updates

### 4. Manual Resolution (Recommended)

Show UI to user.

```typescript
async function resolveConflictManual(conflict: ConflictData): Promise<Resolution> {
  const userChoice = await showConflictDialog({
    title: 'Sync Conflict',
    message: `Conflict detected for ${conflict.entity_type}`,
    clientData: conflict.client_data,
    serverData: conflict.server_data,
    options: [
      { label: 'Keep My Changes', value: 'client_wins' },
      { label: 'Use Server Version', value: 'server_wins' },
      { label: 'Merge Manually', value: 'manual' }
    ]
  })

  if (userChoice === 'manual') {
    const mergedData = await showMergeEditor(
      conflict.client_data,
      conflict.server_data
    )
    return { resolution: 'manual', merged_data: mergedData }
  }

  return { resolution: userChoice }
}
```

---

## Best Practices

### 1. Sync Frequency

- **On App Launch**: Always sync when app starts
- **On Resume**: Sync when app comes to foreground
- **On Connectivity Change**: Sync when network restored
- **Periodic**: Every 5-15 minutes when active
- **On User Action**: Option to manually trigger sync

### 2. Bandwidth Optimization

- **Incremental Sync**: Always use `since` parameter
- **Pagination**: Limit to 100-500 items per request
- **Compression**: Enable gzip on HTTP client
- **Delta Sync**: Only send changed fields (future enhancement)

### 3. Error Handling

```typescript
async function performSyncWithRetry(maxRetries = 3): Promise<void> {
  let attempt = 0

  while (attempt < maxRetries) {
    try {
      await syncManager.performSync()
      return
    } catch (error) {
      attempt++

      if (error.status === 401) {
        // Token expired, try refresh
        await refreshToken()
      } else if (error.status === 403) {
        // Device revoked, force re-authentication
        await logout()
        return
      } else if (attempt >= maxRetries) {
        // Max retries exceeded
        throw error
      }

      // Exponential backoff
      await sleep(Math.pow(2, attempt) * 1000)
    }
  }
}
```

### 4. Local Database Schema

Keep the same schema as server:

```sql
-- SQLite local database

CREATE TABLE volunteers (
  id INTEGER PRIMARY KEY,
  user_id INTEGER,
  name TEXT,
  email TEXT,
  -- ... other fields
  version INTEGER DEFAULT 1,
  updated_at TIMESTAMP,
  is_deleted BOOLEAN DEFAULT 0,
  _local_modified BOOLEAN DEFAULT 0  -- Track local changes
);

CREATE TABLE pending_sync_operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  operation TEXT NOT NULL,  -- CREATE, UPDATE, DELETE
  data TEXT NOT NULL,        -- JSON
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  retry_count INTEGER DEFAULT 0
);

CREATE INDEX idx_pending_sync ON pending_sync_operations(created_at);
CREATE INDEX idx_volunteers_updated ON volunteers(updated_at);
CREATE INDEX idx_volunteers_deleted ON volunteers(is_deleted);
```

### 5. Testing

Test these scenarios:

- ✅ Concurrent edits on two devices
- ✅ Delete on one device, edit on another
- ✅ Network failure during sync
- ✅ Token expiration during sync
- ✅ Device revocation
- ✅ Large dataset sync (1000+ items)
- ✅ Offline for extended period (days)

---

## Troubleshooting

### Issue: "Device not registered or inactive"

**Solution**: Call `POST /sync/device/register` before syncing

### Issue: Conflicts on every sync

**Cause**: Version numbers not updating properly

**Solution**: Ensure local DB increments version on each edit

### Issue: Deleted items reappearing

**Cause**: Soft deletes not handled

**Solution**: Check `is_deleted` field and hide in UI

### Issue: Sync taking too long

**Solutions**:
- Reduce `limit` parameter
- Only sync needed entity types
- Implement background sync (not blocking UI)

### Issue: Token expired offline

**Solutions**:
- Increase refresh token lifetime
- Show "Limited offline mode" banner
- Queue sensitive operations for online

---

## Security Considerations

### 1. Data Encryption

- **In Transit**: Always use HTTPS
- **At Rest (Mobile)**: Enable SQLCipher for local database
- **At Rest (Desktop)**: Encrypt database file

### 2. Token Storage

- **Never** store tokens in plain text
- Use OS-provided secure storage
- Clear tokens on logout

### 3. Device Revocation

- Implement device management UI
- Allow users to revoke lost devices
- Auto-revoke after password change (optional)

### 4. Audit Logging

Track sync operations:
```python
# Server-side
audit_log.log_event(
    user_id=current_user.id,
    event_type="SYNC_COMPLETED",
    device_id=request.device_id,
    details={
        "changes_pulled": len(pull_response.changes),
        "changes_pushed": len(push_response.applied),
        "conflicts": len(push_response.conflicts)
    }
)
```

---

## Future Enhancements

1. **Delta Sync**: Only send changed fields, not entire entities
2. **Selective Sync**: Let users choose which projects/volunteers to sync
3. **Conflict Merging**: Automatic field-level merge
4. **Real-time Sync**: WebSocket-based push notifications
5. **Attachment Sync**: Handle file uploads/downloads
6. **Batch Operations**: Group related changes for atomicity
7. **Sync Analytics**: Track sync performance and issues

---

## Related Documentation

- [Authentication](./authentication.md) - JWT token management
- [Google Sign-In](./google-signin.md) - OAuth integration
- [Quick Reference](./QUICK_REFERENCE.md) - API overview
- [Deployment Checklist](./DEPLOYMENT_CHECKLIST.md) - Production setup

---

## Support

For questions or issues:
- GitHub Issues: https://github.com/your-org/repensar-backend
- API Docs: https://api.repensar.com/docs
- Email: support@repensar.com
