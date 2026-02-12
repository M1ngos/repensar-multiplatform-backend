# Manual Testing Playbook

Quick reference for QA testing. Each section lists actions and expected results.

---

## 1. Authentication

### Register
| Action | Verify |
|--------|--------|
| POST `/auth/register` with valid data | 201, user created, verification email sent | ✅
| Register with existing email | 400 error "Email already registered" |
| Register with invalid email format | 422 validation error |
| Register with weak password | 400 error about password requirements |

### Login
| Action | Verify |
|--------|--------|
| POST `/auth/login` with valid credentials | 200, returns access_token + refresh_token |
| Login with wrong password | 401 "Invalid credentials" |
| Login with non-existent email | 401 "Invalid credentials" |
| Login 5+ times with wrong password | Account locked, 423 error |
| Login after lockout period (30 min) | Login works again |

### Token Management
| Action | Verify |
|--------|--------|
| POST `/auth/refresh` with valid refresh token | 200, new access_token |
| Refresh with expired token | 401 error |
| POST `/auth/logout` | 200, token blacklisted |
| Use access token after logout | 401 error |

### Password Reset
| Action | Verify |
|--------|--------|
| POST `/auth/forgot-password` with valid email | 200, reset email sent |
| POST `/auth/reset-password` with valid token | 200, password changed |
| Reset with expired token (>1hr) | 400 error |

### Email Verification
| Action | Verify |
|--------|--------|
| GET `/auth/verify-email?token=xxx` | 200, email verified |
| Verify with invalid/expired token | 400 error |

---

## 2. Users (Admin)

| Action | Verify |
|--------|--------|
| GET `/users` as admin | 200, paginated user list |
| GET `/users` as volunteer | 403 forbidden |
| GET `/users/{id}` | 200, user details |
| PUT `/users/{id}` as admin | 200, user updated |
| POST `/users/{id}/deactivate` | 200, user deactivated |
| POST `/users/{id}/activate` | 200, user reactivated |
| GET `/users/me` | 200, current user profile |
| GET `/users/types/all` | 200, list of user types |

---

## 3. Projects

### CRUD
| Action | Verify |
|--------|--------|
| POST `/projects` as admin/PM | 201, project created |
| POST `/projects` as volunteer | 403 forbidden |
| GET `/projects` | 200, paginated list |
| GET `/projects/{id}` | 200, project details |
| PUT `/projects/{id}` as owner/admin | 200, updated |
| DELETE `/projects/{id}` as admin | 204, deleted |
| DELETE `/projects/{id}` as PM | 403 forbidden |

### Team Management
| Action | Verify |
|--------|--------|
| GET `/projects/{id}/team` | 200, team members list |
| POST `/projects/{id}/team` with user_id | 201, member added |
| DELETE `/projects/{id}/team/{user_id}` | 204, member removed |

### Milestones
| Action | Verify |
|--------|--------|
| POST `/projects/{id}/milestones` | 201, milestone created |
| PUT `/projects/{id}/milestones/{mid}` | 200, updated |
| DELETE `/projects/{id}/milestones/{mid}` | 204, deleted |

### Stats
| Action | Verify |
|--------|--------|
| GET `/projects/stats` | 200, project statistics |
| GET `/projects/dashboard` | 200, dashboard data |

---

## 4. Tasks

### CRUD
| Action | Verify |
|--------|--------|
| POST `/tasks` with project_id | 201, task created |
| GET `/tasks?project_id=X` | 200, filtered tasks |
| GET `/tasks/{id}` | 200, task details |
| PUT `/tasks/{id}` | 200, task updated |
| DELETE `/tasks/{id}` | 204, deleted |

### Volunteer Assignment
| Action | Verify |
|--------|--------|
| POST `/tasks/{id}/volunteers` | 201, volunteer assigned |
| GET `/tasks/{id}/volunteers` | 200, assigned volunteers |
| DELETE `/tasks/{id}/volunteers/{vid}` | 204, unassigned |
| GET `/tasks/volunteers/available` | 200, available tasks |

### Dependencies
| Action | Verify |
|--------|--------|
| POST `/tasks/{id}/dependencies` | 201, dependency added |
| GET `/tasks/{id}/dependencies` | 200, dependency list |
| DELETE dependency | 204, removed |

---

## 5. Volunteers

### Profile
| Action | Verify |
|--------|--------|
| POST `/volunteers/register` | 201, volunteer profile created |
| GET `/volunteers/profile` (own) | 200, own profile |
| GET `/volunteers/{id}` as admin/staff | 200, volunteer details |
| PUT `/volunteers/{id}` | 200, profile updated |

### Skills
| Action | Verify |
|--------|--------|
| GET `/volunteers/skills` | 200, skills list |
| POST `/volunteers/skills` | 201, skill created |
| Assign skill to volunteer | 200, skill assigned |

### Time Logs
| Action | Verify |
|--------|--------|
| POST `/volunteers/time-logs` | 201, time log created |
| GET `/volunteers/time-logs?volunteer_id=X` | 200, filtered logs |
| PUT time log (before approval) | 200, updated |
| Approve time log as admin/staff | 200, status=approved |

---

## 6. Blog

### Posts
| Action | Verify |
|--------|--------|
| POST `/blog/posts` as admin | 201, post created |
| GET `/blog/posts` | 200, published posts |
| GET `/blog/posts?status=draft` as admin | 200, includes drafts |
| GET `/blog/posts/{id}` | 200, post details |
| PUT `/blog/posts/{id}` | 200, updated |
| DELETE `/blog/posts/{id}` | 204, deleted |

### Categories & Tags
| Action | Verify |
|--------|--------|
| GET `/blog/categories` | 200, category list |
| POST `/blog/categories` as admin | 201, created |
| GET `/blog/tags` | 200, tag list |
| POST `/blog/tags` as admin | 201, created |

---

## 7. Newsletter

### Contact Form (Public)
| Action | Verify |
|--------|--------|
| POST `/contact` with valid data | 201, submission saved |
| Check admin email | Admin notification received |
| Check user email | Auto-reply received |

### Subscription (Public)
| Action | Verify |
|--------|--------|
| POST `/newsletter/subscribe` | 200, confirmation email sent |
| GET `/newsletter/confirm/{token}` | 200, subscription confirmed |
| POST `/newsletter/unsubscribe/{token}` | 200, unsubscribed |

### Admin
| Action | Verify |
|--------|--------|
| GET `/contact/submissions` as admin | 200, submissions list |
| GET `/newsletter/subscribers` as admin | 200, subscribers list |
| POST `/newsletter/campaigns` | 201, campaign created |
| POST `/newsletter/campaigns/{id}/send-now` | 200, campaign sending |

---

## 8. Gamification

### Badges
| Action | Verify |
|--------|--------|
| GET `/gamification/badges` | 200, badge list |
| POST `/gamification/badges` as admin | 201, badge created |
| Award badge to volunteer | 200, badge awarded |
| GET `/gamification/volunteers/{id}/badges` | 200, volunteer's badges |

### Achievements
| Action | Verify |
|--------|--------|
| GET `/gamification/achievements` | 200, achievement list |
| Check auto-awarded achievements | Triggered when criteria met |

### Points & Leaderboards
| Action | Verify |
|--------|--------|
| POST `/gamification/points/award` | 200, points awarded |
| GET `/gamification/points/summary` | 200, points breakdown |
| GET `/gamification/leaderboards/points` | 200, ranked volunteers |

---

## 9. Files

| Action | Verify |
|--------|--------|
| POST `/files/upload` with file | 201, file uploaded |
| GET `/files` | 200, file list |
| GET `/files/download/{id}` | 200, file downloaded |
| DELETE `/files/{id}` | 204, file deleted |
| Upload file >10MB | 413 error |
| Upload invalid file type | 400 error |

---

## 10. Notifications (SSE)

| Action | Verify |
|--------|--------|
| GET `/notifications/stream` | SSE connection established |
| Trigger notification event | Real-time notification received |
| GET `/notifications` | 200, notification list |
| PUT `/notifications/{id}/read` | 200, marked as read |
| DELETE `/notifications/{id}` | 204, deleted |

---

## 11. Search

| Action | Verify |
|--------|--------|
| GET `/search/full-text?q=keyword` | 200, results from projects/tasks/volunteers |
| GET `/search/advanced` with filters | 200, filtered results |

---

## 12. Sync (Offline-First)

| Action | Verify |
|--------|--------|
| POST `/sync/pull` with last_sync timestamp | 200, changes since timestamp |
| POST `/sync/push` with local changes | 200, changes merged |
| Conflict scenario | Conflict resolution applied |

---

## Quick Smoke Test Checklist

- [ ] Register new user
- [ ] Verify email
- [ ] Login
- [ ] Create project (as admin/PM)
- [ ] Create task in project
- [ ] Assign volunteer to task
- [ ] Log volunteer hours
- [ ] Approve time log
- [ ] Check gamification points updated
- [ ] Submit contact form
- [ ] Subscribe to newsletter
- [ ] Upload a file
- [ ] Verify SSE notifications work
- [ ] Logout
