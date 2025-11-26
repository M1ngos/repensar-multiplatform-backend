# Newsletter Module - Frontend Implementation Spec

## Overview

This document outlines the frontend implementation for the newsletter and contact form module.

---

## Public Pages

### 1. Contact Form (Landing Page)

**Location:** Landing page section or `/contact`

**Form Fields:**
```typescript
interface ContactForm {
  name: string;      // required, max 100 chars
  email: string;     // required, valid email
  message: string;   // required, min 10 chars, max 5000 chars
}
```

**API Call:**
```typescript
POST /contact
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "message": "Hello, I would like to..."
}
```

**Response:** `201 Created`
```json
{
  "message": "Thank you for your message. We'll get back to you soon!",
  "id": 123
}
```

**UI Behavior:**
- Show success toast/message on submission
- Clear form after successful submission
- Display validation errors inline

---

### 2. Newsletter Subscribe (Landing Page)

**Location:** Footer, sidebar, or dedicated section

**Form Fields:**
```typescript
interface SubscribeForm {
  email: string;     // required, valid email
  name?: string;     // optional, max 100 chars
}
```

**API Call:**
```typescript
POST /newsletter/subscribe
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "Jane Doe"
}
```

**Response:** `200 OK`
```json
{
  "message": "Please check your email to confirm your subscription.",
  "requires_confirmation": true
}
```

**UI Behavior:**
- Show success message prompting user to check email
- Handle "already subscribed" case gracefully

---

### 3. Subscription Confirmation Page

**Route:** `/newsletter/confirm/:token`

**API Call:**
```typescript
GET /newsletter/confirm/{token}
```

**Response:** `200 OK`
```json
{
  "message": "Your subscription has been confirmed. Thank you!",
  "email": "user@example.com"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "detail": "Invalid or expired confirmation link. Please try subscribing again."
}
```

**UI:**
- Success: Show confirmation message with checkmark
- Error: Show error message with link to re-subscribe

---

### 4. Unsubscribe Page

**Route:** `/newsletter/unsubscribe/:token`

**Step 1 - Get Info:**
```typescript
GET /newsletter/unsubscribe/{token}
```

**Response:**
```json
{
  "email": "user@example.com",
  "status": "active",
  "message": "Are you sure you want to unsubscribe?"
}
```

**Step 2 - Confirm Unsubscribe:**
```typescript
POST /newsletter/unsubscribe/{token}
```

**Response:**
```json
{
  "message": "You have been successfully unsubscribed.",
  "email": "user@example.com"
}
```

**UI:**
- Show confirmation prompt before unsubscribing
- Display success message after unsubscribe
- Optional: Offer feedback form or re-subscribe button

---

## Admin Dashboard Pages

### 5. Contact Submissions Management

**Route:** `/admin/contacts`

**Features:**
- List all submissions with pagination
- Filter by read/unread status
- Mark as read
- View submission details
- Delete submissions

**API Endpoints:**
```typescript
GET  /contact/submissions?skip=0&limit=50&unread_only=false
GET  /contact/submissions/{id}
PATCH /contact/submissions/{id}/read
DELETE /contact/submissions/{id}
```

**List Item Display:**
- Name, email, message preview
- Timestamp
- Read/unread indicator
- Quick actions (view, mark read, delete)

---

### 6. Subscriber Management

**Route:** `/admin/newsletter/subscribers`

**Features:**
- List subscribers with search and filters
- Filter by status (active, pending, unsubscribed)
- Filter by tag
- Add subscriber manually
- Edit subscriber details
- Manage subscriber tags
- Bulk import/export (future)

**API Endpoints:**
```typescript
GET    /newsletter/subscribers?status=active&tag_id=1&search=john
POST   /newsletter/subscribers
GET    /newsletter/subscribers/{id}
PATCH  /newsletter/subscribers/{id}
DELETE /newsletter/subscribers/{id}
POST   /newsletter/subscribers/{id}/tags
DELETE /newsletter/subscribers/{id}/tags/{tag_id}
```

**Subscriber Statuses:**
- `pending` - Awaiting confirmation (yellow)
- `active` - Confirmed subscriber (green)
- `unsubscribed` - Opted out (gray)
- `bounced` - Email bounced (red)

---

### 7. Tag Management

**Route:** `/admin/newsletter/tags`

**Features:**
- CRUD for subscriber tags
- Color picker for tag color
- View subscriber count per tag

**API Endpoints:**
```typescript
GET    /newsletter/tags
POST   /newsletter/tags
PATCH  /newsletter/tags/{id}
DELETE /newsletter/tags/{id}
```

**Tag Schema:**
```typescript
interface NewsletterTag {
  id: number;
  name: string;
  slug: string;
  description?: string;
  color?: string;        // hex color, e.g., "#5ABEA4"
  subscriber_count: number;
}
```

---

### 8. Email Templates

**Route:** `/admin/newsletter/templates`

**Features:**
- List all templates
- Create/edit templates with HTML editor
- Preview templates with sample data
- Activate/deactivate templates

**API Endpoints:**
```typescript
GET    /newsletter/templates
POST   /newsletter/templates
GET    /newsletter/templates/{id}
PATCH  /newsletter/templates/{id}
DELETE /newsletter/templates/{id}
POST   /newsletter/templates/{id}/preview
```

**Template Editor:**
- Rich text / HTML editor
- Variable placeholders: `{{ subscriber_name }}`, `{{ unsubscribe_url }}`
- Preview with test data

---

### 9. Campaign Management

**Route:** `/admin/newsletter/campaigns`

**Features:**
- List campaigns with status filtering
- Create new campaign
- Edit draft campaigns
- Schedule campaigns
- Send campaigns immediately
- Cancel scheduled campaigns
- Send test emails
- View campaign statistics

**API Endpoints:**
```typescript
GET    /newsletter/campaigns?status=draft
POST   /newsletter/campaigns
GET    /newsletter/campaigns/{id}
PATCH  /newsletter/campaigns/{id}
DELETE /newsletter/campaigns/{id}
POST   /newsletter/campaigns/{id}/schedule
POST   /newsletter/campaigns/{id}/send-now
POST   /newsletter/campaigns/{id}/cancel
POST   /newsletter/campaigns/{id}/test
GET    /newsletter/campaigns/{id}/stats
GET    /newsletter/campaigns/{id}/recipients
```

**Campaign Statuses:**
- `draft` - Can be edited (gray)
- `scheduled` - Scheduled for future (blue)
- `sending` - Currently sending (yellow/animated)
- `sent` - Completed (green)
- `cancelled` - Cancelled (red)

**Campaign Statistics:**
```typescript
interface CampaignStats {
  total_recipients: number;
  total_sent: number;
  total_delivered: number;
  total_opened: number;
  total_clicked: number;
  total_bounced: number;
  total_unsubscribed: number;
  open_rate: number;      // percentage
  click_rate: number;     // percentage
  bounce_rate: number;
  unsubscribe_rate: number;
}
```

---

## UI Components Needed

### Forms
- `ContactForm` - Landing page contact form
- `SubscribeForm` - Newsletter subscription form
- `SubscriberForm` - Admin subscriber create/edit
- `TagForm` - Admin tag create/edit
- `TemplateForm` - Admin template editor
- `CampaignForm` - Admin campaign editor

### Lists/Tables
- `ContactSubmissionsList` - Admin contacts table
- `SubscribersList` - Admin subscribers table
- `TagsList` - Admin tags grid/list
- `TemplatesList` - Admin templates list
- `CampaignsList` - Admin campaigns table
- `CampaignRecipientsList` - Campaign recipients table

### Detail Views
- `ContactSubmissionDetail` - View full submission
- `SubscriberDetail` - View/edit subscriber with tags
- `CampaignDetail` - View campaign with stats

### Misc
- `CampaignStats` - Statistics cards/charts
- `TagBadge` - Colored tag badge component
- `StatusBadge` - Status indicator component

---

## Color Scheme (Match Existing)

```css
--primary: #5ABEA4;
--primary-dark: #4AA896;
--background: #f5f5f5;
--surface: #ffffff;
--footer: #fafafa;
--border: #e5e5e5;
--text-primary: #333333;
--text-secondary: #555555;
--text-muted: #666666;
--text-disabled: #999999;

/* Status colors */
--status-pending: #FFC107;
--status-active: #5ABEA4;
--status-inactive: #9E9E9E;
--status-error: #F44336;
--status-sending: #2196F3;
```

---

## Authentication

- **Public endpoints:** `/contact`, `/newsletter/subscribe`, `/newsletter/confirm/*`, `/newsletter/unsubscribe/*`
- **Admin endpoints:** All others require JWT auth with admin/staff role

---

## Notes

1. **Double Opt-in:** Users must confirm email before receiving newsletters
2. **Unsubscribe:** Every email contains unsubscribe link (CAN-SPAM compliance)
3. **Tracking:** Open/click tracking is automatic via backend
4. **Rate Limiting:** Contact form should have client-side throttling
