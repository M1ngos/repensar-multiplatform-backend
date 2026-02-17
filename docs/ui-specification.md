# UI Specification Document - Role-Based Design

## Overview

This document maps all 247 API endpoints to user interface screens organized by user role. Each screen specification includes the shadcn components needed, API endpoints used, and implementation patterns.

### Purpose
- Guide frontend developers in building role-specific interfaces
- Map API endpoints to UI screens systematically
- Define reusable component patterns
- Ensure consistent UX across user types

### Tech Stack
- **Framework**: Next.js 14+ with App Router
- **UI Library**: shadcn/ui components
- **Styling**: Tailwind CSS
- **State**: React hooks + server components
- **API**: REST with fetch/axios

### Design Principles
1. **Role-first navigation** - Each user sees only relevant features
2. **Progressive disclosure** - Show essential info first, details on demand
3. **Consistent patterns** - Reuse components and layouts
4. **Mobile-responsive** - All screens work on mobile devices
5. **Accessible** - WCAG 2.1 AA compliance

---

## Design System

### Status Badge Colors

```typescript
// Status → Badge variant mapping
const statusVariants = {
  // Approval states
  'pending': 'warning',      // yellow
  'approved': 'success',     // green
  'rejected': 'destructive', // red

  // Activity states
  'active': 'success',       // green
  'inactive': 'secondary',   // gray
  'archived': 'secondary',   // gray

  // Progress states
  'not_started': 'secondary', // gray
  'in_progress': 'default',   // blue
  'completed': 'success',     // green
  'cancelled': 'destructive', // red

  // Priority levels
  'low': 'secondary',        // gray
  'medium': 'default',       // blue
  'high': 'warning',         // yellow
  'urgent': 'destructive',   // red
}
```

### Layout Pattern

All portal pages follow this structure:

```tsx
<div className="flex min-h-screen">
  <AppSidebar /> {/* Role-based navigation */}

  <main className="flex-1 p-6 lg:p-8">
    <PageHeader
      title="Page Title"
      description="Brief description"
      actions={<Button>Primary Action</Button>}
    />

    {/* Stats Cards (optional) */}
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
      <StatCard />
      <StatCard />
      <StatCard />
      <StatCard />
    </div>

    {/* Main Content */}
    <Card>
      <CardHeader>
        <CardTitle>Section Title</CardTitle>
        <CardDescription>Description</CardDescription>
      </CardHeader>
      <CardContent>
        {/* Content here */}
      </CardContent>
    </Card>
  </main>
</div>
```

### Common Component Library

#### StatCard
```tsx
<Card>
  <CardHeader className="flex flex-row items-center justify-between pb-2">
    <CardTitle className="text-sm font-medium">Total Hours</CardTitle>
    <Clock className="h-4 w-4 text-muted-foreground" />
  </CardHeader>
  <CardContent>
    <div className="text-2xl font-bold">120.5</div>
    <p className="text-xs text-muted-foreground">+12% from last month</p>
  </CardContent>
</Card>
```

#### PageHeader
```tsx
<div className="flex items-center justify-between mb-6">
  <div>
    <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
    <p className="text-muted-foreground">{description}</p>
  </div>
  <div className="flex gap-2">{actions}</div>
</div>
```

#### EmptyState
```tsx
<div className="flex flex-col items-center justify-center py-12 text-center">
  <Icon className="h-12 w-12 text-muted-foreground mb-4" />
  <h3 className="text-lg font-semibold mb-2">{title}</h3>
  <p className="text-sm text-muted-foreground mb-4">{description}</p>
  <Button>{action}</Button>
</div>
```

#### DataTable with Filters
```tsx
<div className="space-y-4">
  {/* Filters */}
  <div className="flex gap-2">
    <Input placeholder="Search..." className="max-w-sm" />
    <Select><SelectTrigger>Filter by Status</SelectTrigger></Select>
    <Button variant="outline">Clear Filters</Button>
  </div>

  {/* Table */}
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Column 1</TableHead>
        <TableHead>Column 2</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {/* Rows */}
    </TableBody>
  </Table>

  {/* Pagination */}
  <div className="flex items-center justify-between">
    <div className="text-sm text-muted-foreground">
      Showing 1-10 of 50 results
    </div>
    <div className="flex gap-2">
      <Button variant="outline" size="sm">Previous</Button>
      <Button variant="outline" size="sm">Next</Button>
    </div>
  </div>
</div>
```

---

## User Roles & Access Levels

| Role | Access Level | Primary Focus |
|------|-------------|---------------|
| **Volunteer** | Personal data only | Track tasks, log hours, view achievements |
| **Staff Member** | Operational data | Manage volunteers, approve hours, assign tasks |
| **Project Manager** | Project-scoped | Manage projects, teams, tasks, and resources |
| **Admin** | Full system | Configure system, manage all entities, view analytics |
| **Collaborator** | Limited read | View projects and resources (external partner) |

---

## VOLUNTEER

### Sidebar Navigation

```typescript
// components/app-sidebar.tsx - Volunteer section
const volunteerNav = [
  {
    title: t('nav.overview'),
    href: `/${locale}/portal`,
    icon: LayoutDashboard,
    roles: ['volunteer'],
  },
  {
    title: t('nav.myTasks'),
    href: `/${locale}/portal/my-tasks`,
    icon: CheckSquare,
    roles: ['volunteer'],
  },
  {
    title: t('nav.myHours'),
    href: `/${locale}/portal/my-hours`,
    icon: Clock,
    roles: ['volunteer'],
  },
  {
    title: t('nav.availableTasks'),
    href: `/${locale}/portal/available-tasks`,
    icon: Search,
    roles: ['volunteer'],
  },
  {
    title: t('nav.myAchievements'),
    href: `/${locale}/portal/achievements`,
    icon: Award,
    roles: ['volunteer'],
  },
  {
    title: t('nav.leaderboards'),
    href: `/${locale}/portal/leaderboards`,
    icon: Trophy,
    roles: ['volunteer'],
  },
]
```

---

### Dashboard (Home)

**Route:** `/[locale]/portal`
**File:** `src/app/[locale]/portal/page.tsx`

**API Endpoints:**
- `GET /volunteers/{volunteer_id}` - Get profile
- `GET /gamification/stats/volunteer/{volunteer_id}` - Get gamification summary
- `GET /tasks/volunteers/{volunteer_id}/assignments` - Get current tasks
- `GET /volunteers/{volunteer_id}/hours/summary` - Get hours summary

**Features:**
- Personal stats overview
- Current tasks widget
- Recent badges display
- Hours trend chart

**Layout:**

```tsx
<div>
  <PageHeader
    title="Welcome back, {name}!"
    description="Here's your volunteer activity overview"
  />

  {/* Stats Cards */}
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
    <StatCard title="Total Points" value={stats.total_points} icon={Star} />
    <StatCard title="Hours This Month" value={stats.hours_this_month} icon={Clock} />
    <StatCard title="Badges Earned" value={stats.badges_count} icon={Award} />
    <StatCard title="Active Tasks" value={stats.active_tasks} icon={CheckSquare} />
  </div>

  {/* Current Tasks */}
  <div className="grid gap-6 md:grid-cols-2 mb-6">
    <Card>
      <CardHeader>
        <CardTitle>Current Tasks</CardTitle>
        <CardDescription>Your ongoing assignments</CardDescription>
      </CardHeader>
      <CardContent>
        {tasks.map(task => (
          <TaskCard key={task.id} task={task} />
        ))}
      </CardContent>
      <CardFooter>
        <Button variant="link" asChild>
          <Link href="/portal/my-tasks">View all tasks →</Link>
        </Button>
      </CardFooter>
    </Card>

    {/* Recent Badges */}
    <Card>
      <CardHeader>
        <CardTitle>Recent Badges</CardTitle>
        <CardDescription>Latest achievements</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4">
          {badges.slice(0, 6).map(badge => (
            <BadgeIcon key={badge.id} badge={badge} />
          ))}
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="link" asChild>
          <Link href="/portal/achievements">View all →</Link>
        </Button>
      </CardFooter>
    </Card>
  </div>

  {/* Hours Chart */}
  <Card>
    <CardHeader>
      <CardTitle>Hours Logged (Last 6 Months)</CardTitle>
    </CardHeader>
    <CardContent>
      <BarChart data={hoursData} />
    </CardContent>
  </Card>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Link
- Custom: StatCard, TaskCard, BadgeIcon, BarChart

**API Calls:**
- Load all data on page mount
- Refresh stats every 5 minutes

---

### My Tasks

**Route:** `/[locale]/portal/my-tasks`
**File:** `src/app/[locale]/portal/my-tasks/page.tsx`

**API Endpoints:**
- `GET /tasks/volunteers/{volunteer_id}/assignments` - List assigned tasks
- `PUT /tasks/{task_id}/volunteers/{volunteer_id}` - Update task status

**Features:**
- Filter by status
- Task cards with details
- Update task status
- View task details

**Layout:**

```tsx
<div>
  <PageHeader
    title="My Tasks"
    description="Tasks assigned to you"
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Tabs value={statusFilter} onValueChange={setStatusFilter}>
          <TabsList>
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="not_started">Not Started</TabsTrigger>
            <TabsTrigger value="in_progress">In Progress</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
          </TabsList>
        </Tabs>

        <Select value={sortBy} onValueChange={setSortBy}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Sort by" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="due_date">Due Date</SelectItem>
            <SelectItem value="priority">Priority</SelectItem>
            <SelectItem value="project">Project</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Task List */}
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {filteredTasks.map(task => (
      <Card key={task.id}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{task.title}</CardTitle>
            <Badge variant={statusVariants[task.status]}>
              {task.status}
            </Badge>
          </div>
          <CardDescription>{task.project_name}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              <span>Due: {formatDate(task.due_date)}</span>
            </div>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              <Badge variant={statusVariants[task.priority]} size="sm">
                {task.priority}
              </Badge>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => viewTaskDetails(task.id)}
          >
            View Details
          </Button>
          {task.status === 'not_started' && (
            <Button
              size="sm"
              onClick={() => updateStatus(task.id, 'in_progress')}
            >
              Start Task
            </Button>
          )}
          {task.status === 'in_progress' && (
            <Button
              size="sm"
              onClick={() => updateStatus(task.id, 'completed')}
            >
              Complete
            </Button>
          )}
        </CardFooter>
      </Card>
    ))}
  </div>

  {/* Empty State */}
  {filteredTasks.length === 0 && (
    <EmptyState
      icon={CheckSquare}
      title="No tasks found"
      description="You don't have any tasks matching these filters"
      action={<Button onClick={clearFilters}>Clear Filters</Button>}
    />
  )}
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Badge
- Tabs, TabsList, TabsTrigger
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Icons: Calendar, AlertCircle, CheckSquare
- Custom: EmptyState

**API Calls:**
- Load tasks on mount: `GET /tasks/volunteers/{volunteer_id}/assignments`
- Update status: `PUT /tasks/{task_id}/volunteers/{volunteer_id}` with body `{ status: 'in_progress' }`
- Refresh after status update

---

### My Hours

**Route:** `/[locale]/portal/my-hours`
**File:** `src/app/[locale]/portal/my-hours/page.tsx`

**API Endpoints:**
- `GET /volunteers/{volunteer_id}/hours` - List time logs
- `GET /volunteers/{volunteer_id}/hours/summary` - Get hours summary
- `POST /volunteers/{volunteer_id}/hours` - Log new hours
- `PUT /volunteers/hours/{time_log_id}` - Update time log
- `DELETE /volunteers/hours/{time_log_id}` - Delete time log

**Features:**
- Hours summary cards
- Time log history
- Filter by date range and status
- Log new hours (modal)
- Edit/delete pending logs

**Layout:**

```tsx
<div>
  <PageHeader
    title="My Hours"
    description="Track and manage your volunteer hours"
    actions={
      <Button onClick={() => setLogHoursOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        Log Hours
      </Button>
    }
  />

  {/* Summary Cards */}
  <div className="grid gap-4 md:grid-cols-3 mb-6">
    <StatCard
      title="Total Hours"
      value={summary.total_hours}
      icon={Clock}
      trend="+12 this month"
    />
    <StatCard
      title="This Month"
      value={summary.current_month_hours}
      icon={Calendar}
    />
    <StatCard
      title="Pending Approval"
      value={summary.pending_hours}
      icon={AlertCircle}
      variant="warning"
    />
  </div>

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange ? formatDateRange(dateRange) : "Select date range"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar mode="range" selected={dateRange} onSelect={setDateRange} />
          </PopoverContent>
        </Popover>

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Time Logs Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Date</TableHead>
          <TableHead>Project</TableHead>
          <TableHead>Task</TableHead>
          <TableHead>Hours</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {timeLogs.map(log => (
          <TableRow key={log.id}>
            <TableCell>{formatDate(log.date)}</TableCell>
            <TableCell>{log.project_name}</TableCell>
            <TableCell>{log.task_title}</TableCell>
            <TableCell>{log.hours}h</TableCell>
            <TableCell>
              <Badge variant={statusVariants[log.status]}>
                {log.status}
              </Badge>
            </TableCell>
            <TableCell>
              {log.status === 'pending' && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => editLog(log)}>
                      Edit
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => deleteLog(log.id)}
                      className="text-destructive"
                    >
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>

  {/* Log Hours Dialog */}
  <Dialog open={logHoursOpen} onOpenChange={setLogHoursOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Log Volunteer Hours</DialogTitle>
        <DialogDescription>
          Record time spent on a task or project
        </DialogDescription>
      </DialogHeader>
      <Form>
        <FormField name="date" label="Date">
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline">
                {date ? formatDate(date) : "Pick a date"}
              </Button>
            </PopoverTrigger>
            <PopoverContent>
              <Calendar mode="single" selected={date} onSelect={setDate} />
            </PopoverContent>
          </Popover>
        </FormField>

        <FormField name="project_id" label="Project">
          <Select value={projectId} onValueChange={setProjectId}>
            <SelectTrigger>
              <SelectValue placeholder="Select project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map(p => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>

        <FormField name="task_id" label="Task (optional)">
          <Select value={taskId} onValueChange={setTaskId}>
            <SelectTrigger>
              <SelectValue placeholder="Select task" />
            </SelectTrigger>
            <SelectContent>
              {tasks.map(t => (
                <SelectItem key={t.id} value={t.id}>{t.title}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>

        <FormField name="hours" label="Hours">
          <Input type="number" step="0.5" min="0.5" max="24" />
        </FormField>

        <FormField name="description" label="Description">
          <Textarea placeholder="What did you work on?" />
        </FormField>
      </Form>
      <DialogFooter>
        <Button variant="outline" onClick={() => setLogHoursOpen(false)}>
          Cancel
        </Button>
        <Button onClick={submitHours}>Log Hours</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge
- Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
- Form, FormField, Input, Textarea
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Popover, PopoverTrigger, PopoverContent
- Calendar
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem
- Icons: Plus, Clock, Calendar, AlertCircle, MoreHorizontal
- Custom: StatCard

**API Calls:**
- Load summary: `GET /volunteers/{volunteer_id}/hours/summary`
- Load time logs: `GET /volunteers/{volunteer_id}/hours?status={filter}&start_date={start}&end_date={end}`
- Create log: `POST /volunteers/{volunteer_id}/hours` with body:
  ```json
  {
    "project_id": "uuid",
    "task_id": "uuid",
    "date": "2024-01-15",
    "hours": 4.5,
    "description": "Worked on..."
  }
  ```
- Update log: `PUT /volunteers/hours/{time_log_id}`
- Delete log: `DELETE /volunteers/hours/{time_log_id}`

---

### Available Tasks

**Route:** `/[locale]/portal/available-tasks`
**File:** `src/app/[locale]/portal/available-tasks/page.tsx`

**API Endpoints:**
- `GET /tasks/volunteers/available` - List open tasks
- `POST /tasks/{task_id}/volunteers` - Sign up for task

**Features:**
- Browse open tasks
- Filter by skills and project
- View task requirements
- Sign up for tasks

**Layout:**

```tsx
<div>
  <PageHeader
    title="Available Tasks"
    description="Browse and sign up for open volunteer opportunities"
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input
          placeholder="Search tasks..."
          className="max-w-sm"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />

        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <MultiSelect
          options={skillOptions}
          selected={skillFilters}
          onChange={setSkillFilters}
          placeholder="Filter by skills"
        />
      </div>
    </CardContent>
  </Card>

  {/* Task Cards */}
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {tasks.map(task => (
      <Card key={task.id}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{task.title}</CardTitle>
            <Badge variant={statusVariants[task.priority]}>
              {task.priority}
            </Badge>
          </div>
          <CardDescription>{task.project_name}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground line-clamp-3">
              {task.description}
            </p>

            {task.required_skills?.length > 0 && (
              <div>
                <p className="text-sm font-medium mb-1">Skills needed:</p>
                <div className="flex flex-wrap gap-1">
                  {task.required_skills.map(skill => (
                    <Badge key={skill} variant="outline" className="text-xs">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                <span>Due {formatDate(task.due_date)}</span>
              </div>
              <div className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                <span>{task.volunteers_needed - task.volunteers_assigned} spots left</span>
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => viewDetails(task.id)}
          >
            View Details
          </Button>
          <Button
            size="sm"
            onClick={() => signUpForTask(task.id)}
            disabled={task.volunteers_assigned >= task.volunteers_needed}
          >
            Sign Up
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>

  {/* Empty State */}
  {tasks.length === 0 && (
    <EmptyState
      icon={Search}
      title="No tasks available"
      description="There are no open tasks matching your filters"
      action={<Button onClick={clearFilters}>Clear Filters</Button>}
    />
  )}
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Badge, Input
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Icons: Calendar, Users, Search
- Custom: EmptyState, MultiSelect

**API Calls:**
- Load tasks: `GET /tasks/volunteers/available?project_id={filter}&skills={skills}`
- Sign up: `POST /tasks/{task_id}/volunteers` with body:
  ```json
  {
    "volunteer_id": "current_user_volunteer_id"
  }
  ```

---

### My Achievements

**Route:** `/[locale]/portal/achievements`
**File:** `src/app/[locale]/portal/achievements/page.tsx`

**API Endpoints:**
- `GET /gamification/stats/volunteer/{volunteer_id}` - Full summary
- `GET /gamification/volunteers/{volunteer_id}/badges` - Badges list
- `PUT /gamification/volunteers/{volunteer_id}/badges/{badge_id}/showcase` - Toggle showcase
- `GET /gamification/volunteers/{volunteer_id}/points` - Points & streak
- `GET /gamification/volunteers/{volunteer_id}/points/history` - Points history
- `GET /gamification/volunteers/{volunteer_id}/achievements` - Achievements list

**Features:**
- Tabs for Badges | Points | Achievements
- Badge showcase toggle
- Points history timeline
- Achievement progress bars

**Layout:**

```tsx
<div>
  <PageHeader
    title="My Achievements"
    description="Track your badges, points, and accomplishments"
  />

  {/* Summary Cards */}
  <div className="grid gap-4 md:grid-cols-4 mb-6">
    <StatCard
      title="Total Points"
      value={stats.total_points}
      icon={Star}
    />
    <StatCard
      title="Badges Earned"
      value={stats.badges_earned}
      icon={Award}
    />
    <StatCard
      title="Current Streak"
      value={`${stats.current_streak} days`}
      icon={Flame}
    />
    <StatCard
      title="Rank"
      value={`#${stats.rank}`}
      icon={Trophy}
    />
  </div>

  {/* Tabs */}
  <Tabs defaultValue="badges">
    <TabsList className="mb-6">
      <TabsTrigger value="badges">Badges</TabsTrigger>
      <TabsTrigger value="points">Points</TabsTrigger>
      <TabsTrigger value="achievements">Achievements</TabsTrigger>
    </TabsList>

    {/* Badges Tab */}
    <TabsContent value="badges">
      <Card>
        <CardHeader>
          <CardTitle>My Badges</CardTitle>
          <CardDescription>
            Toggle showcase to display badges on your profile
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
            {badges.map(badge => (
              <Card key={badge.id} className="relative">
                <CardContent className="pt-6 text-center">
                  {badge.showcased && (
                    <div className="absolute top-2 right-2">
                      <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    </div>
                  )}

                  <div className="mx-auto w-20 h-20 mb-3">
                    <img
                      src={badge.icon_url}
                      alt={badge.name}
                      className="w-full h-full object-contain"
                    />
                  </div>

                  <h3 className="font-semibold mb-1">{badge.name}</h3>
                  <p className="text-xs text-muted-foreground mb-3">
                    {badge.description}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Earned {formatDate(badge.earned_at)}
                  </p>

                  <Button
                    variant="outline"
                    size="sm"
                    className="mt-3"
                    onClick={() => toggleShowcase(badge.id, !badge.showcased)}
                  >
                    {badge.showcased ? 'Remove from Showcase' : 'Add to Showcase'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>

          {badges.length === 0 && (
            <EmptyState
              icon={Award}
              title="No badges yet"
              description="Complete tasks and contribute to earn badges"
            />
          )}
        </CardContent>
      </Card>
    </TabsContent>

    {/* Points Tab */}
    <TabsContent value="points">
      <div className="grid gap-6 md:grid-cols-2">
        {/* Points Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Points Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground">Total Points</p>
              <p className="text-3xl font-bold">{pointsData.total_points}</p>
            </div>
            <Separator />
            <div>
              <p className="text-sm text-muted-foreground">Current Rank</p>
              <p className="text-2xl font-bold">#{pointsData.rank}</p>
            </div>
            <Separator />
            <div>
              <p className="text-sm text-muted-foreground">Current Streak</p>
              <div className="flex items-center gap-2">
                <Flame className="h-5 w-5 text-orange-500" />
                <p className="text-2xl font-bold">{pointsData.current_streak} days</p>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Longest: {pointsData.longest_streak} days
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Points</CardTitle>
            <CardDescription>Your latest point activities</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pointsHistory.slice(0, 10).map(entry => (
                <div key={entry.id} className="flex items-start justify-between">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">{entry.reason}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatDateTime(entry.earned_at)}
                    </p>
                  </div>
                  <Badge variant="success">
                    +{entry.points}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="link" onClick={() => setShowAllHistory(true)}>
              View all history →
            </Button>
          </CardFooter>
        </Card>
      </div>
    </TabsContent>

    {/* Achievements Tab */}
    <TabsContent value="achievements">
      <Card>
        <CardHeader>
          <CardTitle>Achievements</CardTitle>
          <CardDescription>
            Track your progress toward major milestones
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {achievements.map(achievement => (
            <div key={achievement.id} className="space-y-2">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{achievement.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {achievement.description}
                  </p>
                </div>
                {achievement.completed && (
                  <Badge variant="success">Completed</Badge>
                )}
              </div>

              <div className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span>Progress</span>
                  <span className="text-muted-foreground">
                    {achievement.progress} / {achievement.target}
                  </span>
                </div>
                <Progress
                  value={(achievement.progress / achievement.target) * 100}
                />
              </div>

              {achievement.completed && (
                <p className="text-xs text-muted-foreground">
                  Completed {formatDate(achievement.completed_at)}
                </p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </TabsContent>
  </Tabs>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Tabs, TabsList, TabsTrigger, TabsContent
- Button, Badge, Progress, Separator
- Icons: Star, Award, Flame, Trophy
- Custom: StatCard, EmptyState

**API Calls:**
- Load summary: `GET /gamification/stats/volunteer/{volunteer_id}`
- Load badges: `GET /gamification/volunteers/{volunteer_id}/badges`
- Toggle showcase: `PUT /gamification/volunteers/{volunteer_id}/badges/{badge_id}/showcase`
- Load points: `GET /gamification/volunteers/{volunteer_id}/points`
- Load points history: `GET /gamification/volunteers/{volunteer_id}/points/history?limit=50`
- Load achievements: `GET /gamification/volunteers/{volunteer_id}/achievements`

---

### Leaderboards

**Route:** `/[locale]/portal/leaderboards`
**File:** `src/app/[locale]/portal/leaderboards/page.tsx`

**API Endpoints:**
- `GET /gamification/leaderboards/{type}?timeframe={timeframe}` - Get leaderboard
- `GET /gamification/leaderboards/volunteer/{volunteer_id}/position` - Get user position

**Features:**
- Leaderboard type tabs (Points, Hours, Projects)
- Timeframe filter (All Time, Monthly, Weekly)
- Ranking table
- Highlight current user

**Layout:**

```tsx
<div>
  <PageHeader
    title="Leaderboards"
    description="See how you rank among other volunteers"
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Select value={timeframe} onValueChange={setTimeframe}>
          <SelectTrigger className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all_time">All Time</SelectItem>
            <SelectItem value="monthly">This Month</SelectItem>
            <SelectItem value="weekly">This Week</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Leaderboard Tabs */}
  <Tabs value={leaderboardType} onValueChange={setLeaderboardType}>
    <TabsList className="mb-6">
      <TabsTrigger value="points">Points</TabsTrigger>
      <TabsTrigger value="hours">Hours</TabsTrigger>
      <TabsTrigger value="projects">Projects</TabsTrigger>
    </TabsList>

    <TabsContent value={leaderboardType}>
      {/* Top 3 Podium */}
      {rankings.length >= 3 && (
        <div className="grid gap-4 md:grid-cols-3 mb-6">
          {/* 2nd Place */}
          <Card className="md:order-1">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-100 mb-3">
                <span className="text-2xl font-bold text-slate-600">2</span>
              </div>
              <Avatar className="mx-auto w-16 h-16 mb-2">
                <AvatarImage src={rankings[1].avatar_url} />
                <AvatarFallback>{rankings[1].name[0]}</AvatarFallback>
              </Avatar>
              <h3 className="font-semibold">{rankings[1].name}</h3>
              <p className="text-2xl font-bold text-muted-foreground mt-2">
                {formatValue(rankings[1].value)}
              </p>
            </CardContent>
          </Card>

          {/* 1st Place */}
          <Card className="md:order-2 border-yellow-400 border-2">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-yellow-100 mb-3">
                <Trophy className="h-10 w-10 text-yellow-600" />
              </div>
              <Avatar className="mx-auto w-20 h-20 mb-2">
                <AvatarImage src={rankings[0].avatar_url} />
                <AvatarFallback>{rankings[0].name[0]}</AvatarFallback>
              </Avatar>
              <h3 className="font-bold text-lg">{rankings[0].name}</h3>
              <p className="text-3xl font-bold text-yellow-600 mt-2">
                {formatValue(rankings[0].value)}
              </p>
            </CardContent>
          </Card>

          {/* 3rd Place */}
          <Card className="md:order-3">
            <CardContent className="pt-6 text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-100 mb-3">
                <span className="text-2xl font-bold text-amber-600">3</span>
              </div>
              <Avatar className="mx-auto w-16 h-16 mb-2">
                <AvatarImage src={rankings[2].avatar_url} />
                <AvatarFallback>{rankings[2].name[0]}</AvatarFallback>
              </Avatar>
              <h3 className="font-semibold">{rankings[2].name}</h3>
              <p className="text-2xl font-bold text-muted-foreground mt-2">
                {formatValue(rankings[2].value)}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Full Rankings Table */}
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-16">Rank</TableHead>
              <TableHead>Volunteer</TableHead>
              <TableHead className="text-right">
                {leaderboardType === 'points' && 'Points'}
                {leaderboardType === 'hours' && 'Hours'}
                {leaderboardType === 'projects' && 'Projects'}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rankings.map((entry, index) => (
              <TableRow
                key={entry.volunteer_id}
                className={entry.volunteer_id === currentUserId ? 'bg-muted' : ''}
              >
                <TableCell className="font-medium">
                  {index + 1}
                  {index < 3 && (
                    <Trophy className="inline ml-1 h-3 w-3 text-yellow-600" />
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarImage src={entry.avatar_url} />
                      <AvatarFallback>{entry.name[0]}</AvatarFallback>
                    </Avatar>
                    <span className="font-medium">{entry.name}</span>
                    {entry.volunteer_id === currentUserId && (
                      <Badge variant="outline">You</Badge>
                    )}
                  </div>
                </TableCell>
                <TableCell className="text-right font-semibold">
                  {formatValue(entry.value)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </TabsContent>
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarImage, AvatarFallback
- Badge
- Icons: Trophy
- Custom: None

**API Calls:**
- Load leaderboard: `GET /gamification/leaderboards/{type}?timeframe={timeframe}`
  - Types: `points`, `hours`, `projects`
  - Timeframes: `all_time`, `monthly`, `weekly`
- Load user position: `GET /gamification/leaderboards/volunteer/{volunteer_id}/position`
- Refresh on type or timeframe change

---

## PROJECT MANAGER

### Sidebar Navigation

```typescript
// components/app-sidebar.tsx - Project Manager section
const projectManagerNav = [
  {
    title: t('nav.overview'),
    href: `/${locale}/portal`,
    icon: LayoutDashboard,
    roles: ['project_manager'],
  },
  {
    title: t('nav.myProjects'),
    href: `/${locale}/portal/my-projects`,
    icon: Folder,
    roles: ['project_manager'],
  },
  {
    title: t('nav.tasks'),
    href: `/${locale}/portal/tasks`,
    icon: CheckSquare,
    roles: ['project_manager'],
  },
  {
    title: t('nav.team'),
    href: `/${locale}/portal/team`,
    icon: Users,
    roles: ['project_manager'],
  },
  {
    title: t('nav.timeApprovals'),
    href: `/${locale}/portal/time-approvals`,
    icon: ClipboardCheck,
    roles: ['project_manager'],
  },
  {
    title: t('nav.reports'),
    href: `/${locale}/portal/reports`,
    icon: BarChart,
    roles: ['project_manager'],
  },
]
```

---

### Dashboard (PM Home)

**Route:** `/[locale]/portal`
**File:** `src/app/[locale]/portal/page.tsx`

**API Endpoints:**
- `GET /projects/dashboard` - Projects overview
- `GET /volunteers/hours/{time_log_id}` (filtered by PM's projects) - Pending approvals
- `GET /tasks/stats` (filtered by PM's projects) - Task statistics

**Features:**
- Projects summary cards
- Pending approvals count
- Recent project activity
- Task completion rates

**Layout:**

```tsx
<div>
  <PageHeader
    title="Project Manager Dashboard"
    description="Manage your projects and team"
  />

  {/* Stats Cards */}
  <div className="grid gap-4 md:grid-cols-4 mb-6">
    <StatCard
      title="Active Projects"
      value={stats.active_projects}
      icon={Folder}
    />
    <StatCard
      title="Total Tasks"
      value={stats.total_tasks}
      icon={CheckSquare}
    />
    <StatCard
      title="Team Members"
      value={stats.team_members}
      icon={Users}
    />
    <StatCard
      title="Pending Approvals"
      value={stats.pending_approvals}
      icon={ClipboardCheck}
      variant="warning"
    />
  </div>

  {/* Main Content Grid */}
  <div className="grid gap-6 md:grid-cols-2">
    {/* Projects Overview */}
    <Card>
      <CardHeader>
        <CardTitle>My Projects</CardTitle>
        <CardDescription>Projects you manage</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {projects.slice(0, 5).map(project => (
            <div key={project.id} className="flex items-center justify-between">
              <div>
                <p className="font-medium">{project.name}</p>
                <p className="text-sm text-muted-foreground">
                  {project.tasks_completed}/{project.tasks_total} tasks
                </p>
              </div>
              <Progress value={(project.tasks_completed / project.tasks_total) * 100} className="w-24" />
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="link" asChild>
          <Link href="/portal/my-projects">View all →</Link>
        </Button>
      </CardFooter>
    </Card>

    {/* Pending Approvals */}
    <Card>
      <CardHeader>
        <CardTitle>Pending Time Approvals</CardTitle>
        <CardDescription>Hours awaiting your review</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {pendingApprovals.slice(0, 5).map(log => (
            <div key={log.id} className="flex items-start justify-between">
              <div>
                <p className="font-medium">{log.volunteer_name}</p>
                <p className="text-sm text-muted-foreground">
                  {log.hours}h on {log.project_name}
                </p>
              </div>
              <div className="flex gap-2">
                <Button size="sm" variant="outline" onClick={() => approveHours(log.id)}>
                  Approve
                </Button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
      <CardFooter>
        <Button variant="link" asChild>
          <Link href="/portal/time-approvals">View all →</Link>
        </Button>
      </CardFooter>
    </Card>
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Progress, Link
- Icons: Folder, CheckSquare, Users, ClipboardCheck
- Custom: StatCard

**API Calls:**
- Load dashboard: `GET /projects/dashboard` (returns PM-scoped data)
- Load pending approvals: `GET /volunteers/hours?status=pending&project_manager_id={pm_id}`

---

### My Projects

**Route:** `/[locale]/portal/my-projects`
**File:** `src/app/[locale]/portal/my-projects/page.tsx`

**API Endpoints:**
- `GET /projects/?project_manager_id={pm_id}` - List PM's projects
- `POST /projects/` - Create project
- `PUT /projects/{project_id}` - Update project
- `GET /projects/{project_id}` - View project details
- `GET /projects/{project_id}/activity` - Project activity

**Features:**
- List of managed projects
- Create new project
- Edit project details
- View project activity
- Filter by status

**Layout:**

```tsx
<div>
  <PageHeader
    title="My Projects"
    description="Projects you manage"
    actions={
      <Button onClick={() => setCreateProjectOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Project
      </Button>
    }
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <Tabs value={statusFilter} onValueChange={setStatusFilter}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="active">Active</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="on_hold">On Hold</TabsTrigger>
        </TabsList>
      </Tabs>
    </CardContent>
  </Card>

  {/* Projects Grid */}
  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
    {projects.map(project => (
      <Card key={project.id}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{project.name}</CardTitle>
            <Badge variant={statusVariants[project.status]}>
              {project.status}
            </Badge>
          </div>
          <CardDescription className="line-clamp-2">
            {project.description}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span className="text-muted-foreground">
                  {project.completion_percentage}%
                </span>
              </div>
              <Progress value={project.completion_percentage} />
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <p className="text-muted-foreground">Tasks</p>
                <p className="font-medium">
                  {project.tasks_completed}/{project.tasks_total}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Team</p>
                <p className="font-medium">{project.team_size} members</p>
              </div>
            </div>

            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4" />
              <span>Due {formatDate(project.end_date)}</span>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href={`/portal/projects/${project.id}`}>View</Link>
          </Button>
          <Button variant="outline" size="sm" onClick={() => editProject(project)}>
            Edit
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Badge, Progress
- Tabs, TabsList, TabsTrigger
- Icons: Plus, Calendar
- Custom: None

**API Calls:**
- Load projects: `GET /projects/?project_manager_id={pm_id}&status={filter}`
- Create project: `POST /projects/` with project data
- Update project: `PUT /projects/{project_id}`

---

### Tasks Management (PM)

**Route:** `/[locale]/portal/tasks`
**File:** `src/app/[locale]/portal/tasks/page.tsx`

**API Endpoints:**
- `GET /tasks/?project_id={filter}&status={filter}&priority={filter}` - List tasks for PM's projects
- `POST /tasks/` - Create new task
- `PUT /tasks/{task_id}` - Update task
- `DELETE /tasks/{task_id}` - Cancel task
- `GET /tasks/{task_id}/volunteers` - Get assigned volunteers
- `POST /tasks/{task_id}/volunteers` - Assign volunteer
- `DELETE /tasks/{task_id}/volunteers/{volunteer_id}` - Remove volunteer

**Features:**
- Task list filtered to PM's projects
- Create/edit tasks with project, due date, priority
- Assign/unassign volunteers
- Filter by project, status, priority
- Cancel tasks

**Layout:**

```tsx
<div>
  <PageHeader
    title="Tasks"
    description="Manage tasks across your projects"
    actions={
      <Button onClick={() => setCreateTaskOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Task
      </Button>
    }
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="not_started">Not Started</SelectItem>
            <SelectItem value="in_progress">In Progress</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="All Priorities" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="low">Low</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="urgent">Urgent</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Tasks Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Task</TableHead>
          <TableHead>Project</TableHead>
          <TableHead>Assigned To</TableHead>
          <TableHead>Priority</TableHead>
          <TableHead>Due Date</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tasks.map(task => (
          <TableRow key={task.id}>
            <TableCell>
              <p className="font-medium">{task.title}</p>
              <p className="text-sm text-muted-foreground line-clamp-1">{task.description}</p>
            </TableCell>
            <TableCell>{task.project_name}</TableCell>
            <TableCell>
              <div className="flex -space-x-2">
                {task.volunteers.slice(0, 3).map(v => (
                  <Avatar key={v.id} className="w-7 h-7 border-2 border-background">
                    <AvatarFallback>{v.name[0]}</AvatarFallback>
                  </Avatar>
                ))}
                {task.volunteers.length > 3 && (
                  <div className="w-7 h-7 rounded-full bg-muted border-2 border-background flex items-center justify-center text-xs">
                    +{task.volunteers.length - 3}
                  </div>
                )}
              </div>
            </TableCell>
            <TableCell>
              <Badge variant={statusVariants[task.priority]}>{task.priority}</Badge>
            </TableCell>
            <TableCell>{formatDate(task.due_date)}</TableCell>
            <TableCell>
              <Badge variant={statusVariants[task.status]}>{task.status}</Badge>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => editTask(task)}>Edit</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => assignVolunteer(task.id)}>Assign Volunteer</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => cancelTask(task.id)}
                    className="text-destructive"
                  >
                    Cancel Task
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarFallback
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: Plus, MoreHorizontal

**API Calls:**
- Load tasks: `GET /tasks/?project_id={filter}&status={filter}&priority={filter}`
- Create: `POST /tasks/` with body:
  ```json
  {
    "project_id": "uuid",
    "title": "Task title",
    "description": "...",
    "priority": "medium",
    "due_date": "2024-03-01",
    "volunteers_needed": 2
  }
  ```
- Update: `PUT /tasks/{task_id}`
- Assign volunteer: `POST /tasks/{task_id}/volunteers` with `{ "volunteer_id": "uuid" }`
- Remove volunteer: `DELETE /tasks/{task_id}/volunteers/{volunteer_id}`

---

### Team Management

**Route:** `/[locale]/portal/team`
**File:** `src/app/[locale]/portal/team/page.tsx`

**API Endpoints:**
- `GET /projects/{project_id}/team` - Get team members
- `POST /projects/{project_id}/team` - Add team member
- `PUT /projects/{project_id}/team/{user_id}` - Update team member role
- `DELETE /projects/{project_id}/team/{user_id}` - Remove team member
- `GET /volunteers/?search={query}&status=active` - Search volunteers to add

**Features:**
- View team per project (project selector)
- Add/remove members
- Update member roles
- See hours contributed and tasks assigned per member

**Layout:**

```tsx
<div>
  <PageHeader
    title="Team"
    description="Manage team members across your projects"
  />

  {/* Project Selector */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <Select value={selectedProject} onValueChange={setSelectedProject}>
        <SelectTrigger className="w-[280px]">
          <SelectValue placeholder="Select a project" />
        </SelectTrigger>
        <SelectContent>
          {projects.map(p => (
            <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </CardContent>
  </Card>

  {selectedProject && (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Team Members</CardTitle>
          <Button size="sm" onClick={() => setAddMemberOpen(true)}>
            <UserPlus className="mr-2 h-4 w-4" />
            Add Member
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Member</TableHead>
              <TableHead>Role</TableHead>
              <TableHead>Hours Contributed</TableHead>
              <TableHead>Tasks Assigned</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {teamMembers.map(member => (
              <TableRow key={member.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarImage src={member.avatar_url} />
                      <AvatarFallback>{member.name[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{member.name}</p>
                      <p className="text-sm text-muted-foreground">{member.email}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{member.role}</Badge>
                </TableCell>
                <TableCell>{member.hours_contributed}h</TableCell>
                <TableCell>{member.tasks_assigned}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => editRole(member)}>Edit Role</DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => removeMember(member.id)}
                        className="text-destructive"
                      >
                        Remove
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )}
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarImage, AvatarFallback
- Button, Badge
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: UserPlus, MoreHorizontal

**API Calls:**
- Load team: `GET /projects/{project_id}/team`
- Add member: `POST /projects/{project_id}/team` with `{ "user_id": "uuid", "role": "volunteer" }`
- Update role: `PUT /projects/{project_id}/team/{user_id}` with `{ "role": "lead" }`
- Remove: `DELETE /projects/{project_id}/team/{user_id}`

---

### Time Approvals (PM)

**Route:** `/[locale]/portal/time-approvals`
**File:** `src/app/[locale]/portal/time-approvals/page.tsx`

**API Endpoints:**
- `GET /volunteers/hours?status={filter}&project_id={pm_project_ids}` - List time logs for PM's projects
- `POST /volunteers/hours/{time_log_id}/approve` - Approve or reject a log

**Features:**
- Pending time logs scoped to PM's projects
- Approve/reject with optional rejection reason
- Filter by project and status
- Summary counts (pending, approved this month, rejected this month)

**Layout:**

```tsx
<div>
  <PageHeader
    title="Time Approvals"
    description="Review and approve volunteer hours"
  />

  {/* Summary */}
  <div className="grid gap-4 md:grid-cols-3 mb-6">
    <StatCard title="Pending" value={counts.pending} icon={Clock} variant="warning" />
    <StatCard title="Approved This Month" value={counts.approved} icon={CheckCircle} variant="success" />
    <StatCard title="Rejected This Month" value={counts.rejected} icon={XCircle} />
  </div>

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Select value={projectFilter} onValueChange={setProjectFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Projects" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Projects</SelectItem>
            {projects.map(p => (
              <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Tabs value={statusFilter} onValueChange={setStatusFilter}>
          <TabsList>
            <TabsTrigger value="pending">Pending</TabsTrigger>
            <TabsTrigger value="approved">Approved</TabsTrigger>
            <TabsTrigger value="rejected">Rejected</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>
    </CardContent>
  </Card>

  {/* Approvals Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Volunteer</TableHead>
          <TableHead>Project</TableHead>
          <TableHead>Task</TableHead>
          <TableHead>Date</TableHead>
          <TableHead>Hours</TableHead>
          <TableHead>Description</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {timeLogs.map(log => (
          <TableRow key={log.id}>
            <TableCell>
              <div className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarFallback>{log.volunteer_name[0]}</AvatarFallback>
                </Avatar>
                <span className="font-medium">{log.volunteer_name}</span>
              </div>
            </TableCell>
            <TableCell>{log.project_name}</TableCell>
            <TableCell>{log.task_title || '-'}</TableCell>
            <TableCell>{formatDate(log.date)}</TableCell>
            <TableCell className="font-medium">{log.hours}h</TableCell>
            <TableCell>
              <p className="text-sm text-muted-foreground line-clamp-2">{log.description}</p>
            </TableCell>
            <TableCell>
              {log.status === 'pending' ? (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => approveLog(log.id)}>Approve</Button>
                  <Button size="sm" variant="outline" onClick={() => rejectLog(log.id)}>Reject</Button>
                </div>
              ) : (
                <Badge variant={statusVariants[log.status]}>{log.status}</Badge>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>

  {/* Reject Dialog */}
  <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Reject Time Log</DialogTitle>
        <DialogDescription>Provide a reason for rejection (optional)</DialogDescription>
      </DialogHeader>
      <Textarea
        placeholder="Reason for rejection..."
        value={rejectionReason}
        onChange={e => setRejectionReason(e.target.value)}
      />
      <DialogFooter>
        <Button variant="outline" onClick={() => setRejectDialogOpen(false)}>Cancel</Button>
        <Button variant="destructive" onClick={confirmReject}>Reject</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Tabs, TabsList, TabsTrigger
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarFallback
- Button, Badge
- Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter
- Textarea
- Icons: Clock, CheckCircle, XCircle
- Custom: StatCard

**API Calls:**
- Load logs: `GET /volunteers/hours?status={filter}&project_id={filter}&page={page}&limit={limit}`
- Approve: `POST /volunteers/hours/{time_log_id}/approve` with `{ "status": "approved" }`
- Reject: `POST /volunteers/hours/{time_log_id}/approve` with `{ "status": "rejected", "rejection_reason": "..." }`

---

### Reports (PM)

**Route:** `/[locale]/portal/reports`
**File:** `src/app/[locale]/portal/reports/page.tsx`

**API Endpoints:**
- `GET /reports/projects` - Project completion and hours summary
- `GET /reports/volunteers` - Volunteer activity breakdown
- `GET /reports/tasks` - Task status summary
- `GET /reports/export/projects/csv` - Export projects CSV
- `GET /reports/export/volunteers/csv` - Export volunteers CSV
- `GET /reports/export/tasks/csv` - Export tasks CSV
- `GET /reports/export/hours/csv` - Export hours CSV

**Features:**
- Tabbed reports: Projects | Volunteers | Tasks
- Date range filter
- CSV export per report type
- Progress and completion metrics

**Layout:**

```tsx
<div>
  <PageHeader
    title="Reports"
    description="View performance and activity summaries"
  />

  {/* Date Range Filter */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange ? formatDateRange(dateRange) : "Select date range"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar mode="range" selected={dateRange} onSelect={setDateRange} />
          </PopoverContent>
        </Popover>
      </div>
    </CardContent>
  </Card>

  <Tabs defaultValue="projects">
    <TabsList className="mb-6">
      <TabsTrigger value="projects">Projects</TabsTrigger>
      <TabsTrigger value="volunteers">Volunteers</TabsTrigger>
      <TabsTrigger value="tasks">Tasks</TabsTrigger>
    </TabsList>

    <TabsContent value="projects">
      <div className="flex justify-end mb-4">
        <Button variant="outline" onClick={() => exportCSV('projects')}>
          <Download className="mr-2 h-4 w-4" />
          Export CSV
        </Button>
      </div>
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Project</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Tasks Completed</TableHead>
              <TableHead>Volunteers</TableHead>
              <TableHead>Hours Logged</TableHead>
              <TableHead>Completion</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {projectReport.map(row => (
              <TableRow key={row.id}>
                <TableCell className="font-medium">{row.name}</TableCell>
                <TableCell>
                  <Badge variant={statusVariants[row.status]}>{row.status}</Badge>
                </TableCell>
                <TableCell>{row.tasks_completed}/{row.tasks_total}</TableCell>
                <TableCell>{row.volunteer_count}</TableCell>
                <TableCell>{row.total_hours}h</TableCell>
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Progress value={row.completion_percentage} className="w-16" />
                    <span className="text-sm">{row.completion_percentage}%</span>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </TabsContent>

    {/* Volunteers tab: name, projects involved, hours logged, tasks completed */}
    {/* Tasks tab: title, project, status, assigned volunteers, hours spent */}
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge, Progress
- Popover, PopoverTrigger, PopoverContent, Calendar
- Icons: CalendarIcon, Download

**API Calls:**
- Projects report: `GET /reports/projects?start_date={start}&end_date={end}`
- Volunteers report: `GET /reports/volunteers?start_date={start}&end_date={end}`
- Tasks report: `GET /reports/tasks?start_date={start}&end_date={end}`
- Export CSV: `GET /reports/export/{type}/csv?start_date={start}&end_date={end}` (triggers file download)

---

## STAFF MEMBER

### Sidebar Navigation

```typescript
// components/app-sidebar.tsx - Staff Member section
const staffNav = [
  {
    title: t('nav.overview'),
    href: `/${locale}/portal`,
    icon: LayoutDashboard,
    roles: ['staff_member'],
  },
  {
    title: t('nav.volunteers'),
    href: `/${locale}/portal/volunteers`,
    icon: Users,
    roles: ['staff_member'],
  },
  {
    title: t('nav.timeApprovals'),
    href: `/${locale}/portal/time-approvals`,
    icon: ClipboardCheck,
    roles: ['staff_member'],
  },
  {
    title: t('nav.tasks'),
    href: `/${locale}/portal/tasks`,
    icon: CheckSquare,
    roles: ['staff_member'],
  },
  {
    title: t('nav.contactSubmissions'),
    href: `/${locale}/portal/contact`,
    icon: Mail,
    roles: ['staff_member'],
  },
  {
    title: t('nav.gamification'),
    href: `/${locale}/portal/gamification`,
    icon: Award,
    roles: ['staff_member'],
  },
]
```

---

### Volunteers Management

**Route:** `/[locale]/portal/volunteers`
**File:** `src/app/[locale]/portal/volunteers/page.tsx`

**API Endpoints:**
- `GET /volunteers/` - List volunteers
- `GET /volunteers/{volunteer_id}` - Get volunteer profile
- `PUT /volunteers/{volunteer_id}` - Update volunteer
- `DELETE /volunteers/{volunteer_id}` - Deactivate volunteer
- `GET /volunteers/{volunteer_id}/skills` - Get skills
- `POST /volunteers/{volunteer_id}/skills` - Assign skill
- `GET /volunteers/stats` - Volunteer statistics

**Features:**
- Volunteer directory with search
- View/edit volunteer profiles
- Manage skills
- View activity history
- Activate/deactivate volunteers

**Layout:**

```tsx
<div>
  <PageHeader
    title="Volunteers"
    description="Manage volunteer profiles and skills"
  />

  {/* Stats Cards */}
  <div className="grid gap-4 md:grid-cols-3 mb-6">
    <StatCard title="Total Volunteers" value={stats.total} icon={Users} />
    <StatCard title="Active" value={stats.active} icon={UserCheck} variant="success" />
    <StatCard title="Inactive" value={stats.inactive} icon={UserX} variant="secondary" />
  </div>

  {/* Search & Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input
          placeholder="Search volunteers..."
          className="max-w-sm"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />

        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>

        <MultiSelect
          options={skillOptions}
          selected={skillFilters}
          onChange={setSkillFilters}
          placeholder="Filter by skills"
        />
      </div>
    </CardContent>
  </Card>

  {/* Volunteers Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Volunteer</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Skills</TableHead>
          <TableHead>Hours</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {volunteers.map(volunteer => (
          <TableRow key={volunteer.id}>
            <TableCell>
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={volunteer.avatar_url} />
                  <AvatarFallback>{volunteer.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">{volunteer.name}</p>
                  <p className="text-sm text-muted-foreground">
                    Joined {formatDate(volunteer.created_at)}
                  </p>
                </div>
              </div>
            </TableCell>
            <TableCell>{volunteer.email}</TableCell>
            <TableCell>
              <div className="flex flex-wrap gap-1">
                {volunteer.skills.slice(0, 3).map(skill => (
                  <Badge key={skill} variant="outline" className="text-xs">
                    {skill}
                  </Badge>
                ))}
                {volunteer.skills.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{volunteer.skills.length - 3}
                  </Badge>
                )}
              </div>
            </TableCell>
            <TableCell>{volunteer.total_hours}h</TableCell>
            <TableCell>
              <Badge variant={statusVariants[volunteer.status]}>
                {volunteer.status}
              </Badge>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => viewProfile(volunteer.id)}>
                    View Profile
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => editVolunteer(volunteer)}>
                    Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => manageSkills(volunteer.id)}>
                    Manage Skills
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {volunteer.status === 'active' ? (
                    <DropdownMenuItem
                      onClick={() => deactivate(volunteer.id)}
                      className="text-destructive"
                    >
                      Deactivate
                    </DropdownMenuItem>
                  ) : (
                    <DropdownMenuItem onClick={() => activate(volunteer.id)}>
                      Activate
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Input, Button, Badge
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarImage, AvatarFallback
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: Users, UserCheck, UserX, MoreHorizontal
- Custom: StatCard, MultiSelect

**API Calls:**
- Load volunteers: `GET /volunteers/?status={filter}&skills={skills}&search={query}`
- Load stats: `GET /volunteers/stats`
- Update volunteer: `PUT /volunteers/{volunteer_id}`
- Deactivate: `DELETE /volunteers/{volunteer_id}`

---

### Time Approvals (Staff)

**Route:** `/[locale]/portal/time-approvals`
**File:** `src/app/[locale]/portal/time-approvals/page.tsx`

**Same layout as PM Time Approvals.** Staff members see all pending logs across the entire organization (not scoped to a project manager's projects).

**API Endpoints:**
- `GET /volunteers/hours?status={filter}` - List all time logs org-wide
- `POST /volunteers/hours/{time_log_id}/approve` - Approve or reject

**API Calls:**
- Load logs: `GET /volunteers/hours?status={filter}&page={page}&limit={limit}`
- Approve: `POST /volunteers/hours/{time_log_id}/approve` with `{ "status": "approved" }`
- Reject: `POST /volunteers/hours/{time_log_id}/approve` with `{ "status": "rejected", "rejection_reason": "..." }`

---

### Tasks Assignment (Staff)

**Route:** `/[locale]/portal/tasks`
**File:** `src/app/[locale]/portal/tasks/page.tsx`

**Same layout as PM Tasks Management.** Staff see all tasks across all projects (no project-manager scoping).

**API Endpoints:**
- `GET /tasks/` - List all tasks (org-wide)
- `POST /tasks/` - Create task
- `PUT /tasks/{task_id}` - Update task
- `POST /tasks/{task_id}/volunteers` - Assign volunteer
- `DELETE /tasks/{task_id}/volunteers/{volunteer_id}` - Remove volunteer
- `GET /volunteers/?status=active` - List volunteers for assignment dropdown

**API Calls:**
- Load tasks: `GET /tasks/?status={filter}&priority={filter}&project_id={filter}`
- Assign volunteer: `POST /tasks/{task_id}/volunteers` with `{ "volunteer_id": "uuid" }`

---

### Contact Submissions

**Route:** `/[locale]/portal/contact`
**File:** `src/app/[locale]/portal/contact/page.tsx`

**API Endpoints:**
- `GET /contact/submissions` - List contact form submissions
- `PATCH /contact/submissions/{submission_id}/read` - Mark as read
- `DELETE /contact/submissions/{submission_id}` - Delete submission

**Features:**
- Inbox of contact form submissions
- Unread count badge
- Mark as read/unread
- Filter by read status
- Delete submissions

**Layout:**

```tsx
<div>
  <PageHeader
    title="Contact Submissions"
    description="Manage incoming contact form messages"
  />

  {/* Stats */}
  <div className="grid gap-4 md:grid-cols-2 mb-6">
    <StatCard title="Unread" value={counts.unread} icon={Mail} variant="warning" />
    <StatCard title="Total" value={counts.total} icon={Inbox} />
  </div>

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <Tabs value={readFilter} onValueChange={setReadFilter}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="unread">
            Unread
            {counts.unread > 0 && (
              <Badge className="ml-2 h-5 px-1.5" variant="destructive">{counts.unread}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="read">Read</TabsTrigger>
        </TabsList>
      </Tabs>
    </CardContent>
  </Card>

  {/* Submissions Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Subject</TableHead>
          <TableHead>Message</TableHead>
          <TableHead>Received</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {submissions.map(submission => (
          <TableRow
            key={submission.id}
            className={!submission.is_read ? 'bg-muted/30' : ''}
          >
            <TableCell>
              <span className={!submission.is_read ? 'font-semibold' : ''}>
                {submission.name}
              </span>
            </TableCell>
            <TableCell>{submission.email}</TableCell>
            <TableCell>{submission.subject}</TableCell>
            <TableCell>
              <p className="text-sm text-muted-foreground line-clamp-2 max-w-xs">
                {submission.message}
              </p>
            </TableCell>
            <TableCell>{formatDateTime(submission.created_at)}</TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => viewFull(submission)}>
                    View Full Message
                  </DropdownMenuItem>
                  {!submission.is_read && (
                    <DropdownMenuItem onClick={() => markAsRead(submission.id)}>
                      Mark as Read
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => deleteSubmission(submission.id)}
                    className="text-destructive"
                  >
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Tabs, TabsList, TabsTrigger
- Button, Badge
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: Mail, Inbox, MoreHorizontal
- Custom: StatCard

**API Calls:**
- Load submissions: `GET /contact/submissions?is_read={filter}&page={page}&limit={limit}`
- Mark read: `PATCH /contact/submissions/{submission_id}/read`
- Delete: `DELETE /contact/submissions/{submission_id}`

---

### Gamification Awards (Staff)

**Route:** `/[locale]/portal/gamification`
**File:** `src/app/[locale]/portal/gamification/page.tsx`

**API Endpoints:**
- `GET /volunteers/?status=active` - List volunteers
- `GET /gamification/badges` - List available badges
- `POST /gamification/volunteers/{volunteer_id}/badges/award` - Award badge
- `POST /gamification/volunteers/{volunteer_id}/points/award` - Award bonus points
- `GET /gamification/stats` - Overall gamification stats

**Features:**
- Award badges manually to volunteers
- Award bonus points with a reason
- View overall gamification stats

**Layout:**

```tsx
<div>
  <PageHeader
    title="Gamification"
    description="Award badges and bonus points to volunteers"
  />

  <div className="grid gap-6 md:grid-cols-2">
    {/* Award Points */}
    <Card>
      <CardHeader>
        <CardTitle>Award Points</CardTitle>
        <CardDescription>Manually award bonus points to a volunteer</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Volunteer</label>
          <Select value={selectedVolunteer} onValueChange={setSelectedVolunteer}>
            <SelectTrigger>
              <SelectValue placeholder="Select volunteer" />
            </SelectTrigger>
            <SelectContent>
              {volunteers.map(v => (
                <SelectItem key={v.id} value={v.id}>{v.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Points</label>
          <Input type="number" min="1" max="1000" value={points} onChange={e => setPoints(e.target.value)} />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Reason</label>
          <Textarea
            placeholder="Why are you awarding these points?"
            value={reason}
            onChange={e => setReason(e.target.value)}
          />
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={awardPoints} className="w-full">Award Points</Button>
      </CardFooter>
    </Card>

    {/* Award Badge */}
    <Card>
      <CardHeader>
        <CardTitle>Award Badge</CardTitle>
        <CardDescription>Manually award a badge to a volunteer</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm font-medium">Volunteer</label>
          <Select value={badgeVolunteer} onValueChange={setBadgeVolunteer}>
            <SelectTrigger>
              <SelectValue placeholder="Select volunteer" />
            </SelectTrigger>
            <SelectContent>
              {volunteers.map(v => (
                <SelectItem key={v.id} value={v.id}>{v.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium">Badge</label>
          <div className="grid grid-cols-2 gap-2 max-h-52 overflow-y-auto border rounded p-2">
            {badges.map(badge => (
              <div
                key={badge.id}
                className={`flex items-center gap-2 p-2 rounded cursor-pointer border ${
                  selectedBadge === badge.id ? 'border-primary bg-primary/5' : 'border-transparent'
                }`}
                onClick={() => setSelectedBadge(badge.id)}
              >
                <img src={badge.icon_url} alt={badge.name} className="w-8 h-8" />
                <span className="text-sm font-medium">{badge.name}</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
      <CardFooter>
        <Button onClick={awardBadge} className="w-full" disabled={!badgeVolunteer || !selectedBadge}>
          Award Badge
        </Button>
      </CardFooter>
    </Card>
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Input, Textarea, Button

**API Calls:**
- Load volunteers: `GET /volunteers/?status=active`
- Load badges: `GET /gamification/badges`
- Award points: `POST /gamification/volunteers/{volunteer_id}/points/award` with `{ "points": 50, "reason": "..." }`
- Award badge: `POST /gamification/volunteers/{volunteer_id}/badges/award` with `{ "badge_id": "uuid" }`

---

## ADMIN

### Sidebar Navigation

```typescript
// components/app-sidebar.tsx - Admin section
const adminNav = [
  {
    title: t('nav.overview'),
    href: `/${locale}/portal`,
    icon: LayoutDashboard,
    roles: ['admin'],
  },
  {
    title: t('nav.users'),
    href: `/${locale}/portal/users`,
    icon: Users,
    roles: ['admin'],
  },
  {
    title: t('nav.projects'),
    href: `/${locale}/portal/projects`,
    icon: Folder,
    roles: ['admin'],
  },
  {
    title: t('nav.volunteers'),
    href: `/${locale}/portal/volunteers`,
    icon: Heart,
    roles: ['admin'],
  },
  {
    title: t('nav.tasks'),
    href: `/${locale}/portal/tasks`,
    icon: CheckSquare,
    roles: ['admin'],
  },
  {
    title: t('nav.resources'),
    href: `/${locale}/portal/resources`,
    icon: Package,
    roles: ['admin'],
  },
  {
    title: t('nav.blog'),
    href: `/${locale}/portal/blog`,
    icon: FileText,
    roles: ['admin'],
  },
  {
    title: t('nav.contact'),
    href: `/${locale}/portal/contact`,
    icon: Mail,
    roles: ['admin'],
  },
  {
    title: t('nav.newsletter'),
    href: `/${locale}/portal/newsletter`,
    icon: Send,
    roles: ['admin'],
  },
  {
    title: t('nav.gamification'),
    icon: Award,
    roles: ['admin'],
    items: [
      {
        title: t('nav.badges'),
        href: `/${locale}/portal/gamification/badges`,
      },
      {
        title: t('nav.achievements'),
        href: `/${locale}/portal/gamification/achievements`,
      },
      {
        title: t('nav.leaderboards'),
        href: `/${locale}/portal/gamification/leaderboards`,
      },
    ],
  },
  {
    title: t('nav.analytics'),
    href: `/${locale}/portal/analytics`,
    icon: BarChart,
    roles: ['admin'],
  },
  {
    title: t('nav.reports'),
    href: `/${locale}/portal/reports`,
    icon: FileSpreadsheet,
    roles: ['admin'],
  },
]
```

---

### Admin Dashboard

**Route:** `/[locale]/portal`
**File:** `src/app/[locale]/portal/page.tsx`

**API Endpoints:**
- `GET /reports/dashboard` - System-wide summary
- `GET /analytics/dashboard` - Analytics overview
- `GET /projects/stats` - Project statistics
- `GET /volunteers/stats` - Volunteer statistics
- `GET /tasks/stats` - Task statistics

**Features:**
- System-wide statistics
- Key metrics overview
- Recent activity feed
- Quick actions

**Layout:**

```tsx
<div>
  <PageHeader
    title="Admin Dashboard"
    description="System overview and key metrics"
  />

  {/* Stats Grid */}
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
    <StatCard title="Total Users" value={stats.total_users} icon={Users} />
    <StatCard title="Active Projects" value={stats.active_projects} icon={Folder} />
    <StatCard title="Total Volunteers" value={stats.total_volunteers} icon={Heart} />
    <StatCard title="Hours Logged" value={stats.total_hours} icon={Clock} />
  </div>

  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
    {/* Recent Users */}
    <Card>
      <CardHeader>
        <CardTitle>Recent Users</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentUsers.map(user => (
            <div key={user.id} className="flex items-center gap-3">
              <Avatar>
                <AvatarImage src={user.avatar_url} />
                <AvatarFallback>{user.name[0]}</AvatarFallback>
              </Avatar>
              <div>
                <p className="font-medium">{user.name}</p>
                <p className="text-xs text-muted-foreground">
                  {user.user_type} • {formatDate(user.created_at)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>

    {/* Activity Feed */}
    <Card className="md:col-span-2">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activityFeed.map(activity => (
            <div key={activity.id} className="flex gap-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <div className="flex-1">
                <p className="text-sm">{activity.description}</p>
                <p className="text-xs text-muted-foreground">
                  {formatRelativeTime(activity.timestamp)}
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardContent
- Avatar, AvatarImage, AvatarFallback
- Icons: Users, Folder, Heart, Clock
- Custom: StatCard

**API Calls:**
- Load dashboard: `GET /reports/dashboard`
- Load analytics: `GET /analytics/dashboard`

---

### Users Management

**Route:** `/[locale]/portal/users`
**File:** `src/app/[locale]/portal/users/page.tsx`

**API Endpoints:**
- `GET /users/` - List users
- `GET /users/{user_id}` - Get user
- `PUT /users/{user_id}` - Update user
- `POST /users/{user_id}/activate` - Activate user
- `POST /users/{user_id}/deactivate` - Deactivate user
- `GET /users/types/all` - Get user types
- `GET /users/departments/all` - Get departments

**Features:**
- User directory with filters
- View/edit user details
- Activate/deactivate users
- Filter by user type and department
- Search users

**Layout:**

```tsx
<div>
  <PageHeader
    title="Users"
    description="Manage all system users"
    actions={
      <Button onClick={() => router.push('/portal/users/invite')}>
        <UserPlus className="mr-2 h-4 w-4" />
        Invite User
      </Button>
    }
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input
          placeholder="Search users..."
          className="max-w-sm"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        <Select value={userTypeFilter} onValueChange={setUserTypeFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Roles" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Roles</SelectItem>
            <SelectItem value="volunteer">Volunteer</SelectItem>
            <SelectItem value="staff_member">Staff Member</SelectItem>
            <SelectItem value="project_manager">Project Manager</SelectItem>
            <SelectItem value="admin">Admin</SelectItem>
            <SelectItem value="collaborator">Collaborator</SelectItem>
          </SelectContent>
        </Select>
        <Select value={departmentFilter} onValueChange={setDepartmentFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Departments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {departments.map(d => (
              <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="inactive">Inactive</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Users Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>User</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Department</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Joined</TableHead>
          <TableHead>Last Login</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map(user => (
          <TableRow key={user.id}>
            <TableCell>
              <div className="flex items-center gap-3">
                <Avatar>
                  <AvatarImage src={user.avatar_url} />
                  <AvatarFallback>{user.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">{user.name}</p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                </div>
              </div>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{user.user_type}</Badge>
            </TableCell>
            <TableCell>{user.department || '-'}</TableCell>
            <TableCell>
              <Badge variant={user.is_active ? 'success' : 'secondary'}>
                {user.is_active ? 'Active' : 'Inactive'}
              </Badge>
            </TableCell>
            <TableCell>{formatDate(user.created_at)}</TableCell>
            <TableCell>{user.last_login ? formatRelativeTime(user.last_login) : 'Never'}</TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => viewUser(user.id)}>View Profile</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => editUser(user)}>Edit</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  {user.is_active ? (
                    <DropdownMenuItem
                      onClick={() => deactivateUser(user.id)}
                      className="text-destructive"
                    >
                      Deactivate
                    </DropdownMenuItem>
                  ) : (
                    <DropdownMenuItem onClick={() => activateUser(user.id)}>
                      Activate
                    </DropdownMenuItem>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Input, Button, Badge
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Avatar, AvatarImage, AvatarFallback
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: UserPlus, MoreHorizontal

**API Calls:**
- Load users: `GET /users/?search={query}&user_type={filter}&department_id={filter}&is_active={filter}&page={page}`
- Load departments: `GET /users/departments/all`
- Load user types: `GET /users/types/all`
- Update user: `PUT /users/{user_id}`
- Activate: `POST /users/{user_id}/activate`
- Deactivate: `POST /users/{user_id}/deactivate`

---

### Blog Management

**Route:** `/[locale]/portal/blog`
**File:** `src/app/[locale]/portal/blog/page.tsx`

**API Endpoints:**
- `GET /blog/posts` - List posts
- `POST /blog/posts` - Create post
- `PUT /blog/posts/{post_id}` - Update post
- `DELETE /blog/posts/{post_id}` - Delete post
- `POST /blog/posts/{post_id}/publish` - Publish post
- `POST /blog/posts/{post_id}/unpublish` - Unpublish post
- `GET /blog/categories` - List categories
- `GET /blog/tags` - List tags

**Features:**
- Posts list with status filters
- Create/edit posts (rich editor)
- Publish/unpublish posts
- Manage categories and tags
- Preview posts

**Layout:**

```tsx
<div>
  <PageHeader
    title="Blog Management"
    description="Manage blog posts, categories, and tags"
    actions={
      <Button onClick={() => router.push('/portal/blog/new')}>
        <Plus className="mr-2 h-4 w-4" />
        New Post
      </Button>
    }
  />

  {/* Tabs */}
  <Tabs defaultValue="posts">
    <TabsList className="mb-6">
      <TabsTrigger value="posts">Posts</TabsTrigger>
      <TabsTrigger value="categories">Categories</TabsTrigger>
      <TabsTrigger value="tags">Tags</TabsTrigger>
    </TabsList>

    {/* Posts Tab */}
    <TabsContent value="posts">
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <Input placeholder="Search posts..." className="max-w-sm" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="published">Published</SelectItem>
                <SelectItem value="draft">Draft</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Title</TableHead>
              <TableHead>Author</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Published</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {posts.map(post => (
              <TableRow key={post.id}>
                <TableCell>
                  <div>
                    <p className="font-medium">{post.title}</p>
                    <p className="text-sm text-muted-foreground line-clamp-1">
                      {post.excerpt}
                    </p>
                  </div>
                </TableCell>
                <TableCell>{post.author_name}</TableCell>
                <TableCell>
                  <Badge variant="outline">{post.category_name}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariants[post.status]}>
                    {post.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {post.published_at ? formatDate(post.published_at) : '-'}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => editPost(post.id)}>
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => previewPost(post.id)}>
                        Preview
                      </DropdownMenuItem>
                      {post.status === 'draft' ? (
                        <DropdownMenuItem onClick={() => publishPost(post.id)}>
                          Publish
                        </DropdownMenuItem>
                      ) : (
                        <DropdownMenuItem onClick={() => unpublishPost(post.id)}>
                          Unpublish
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => deletePost(post.id)}
                        className="text-destructive"
                      >
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </TabsContent>

    {/* Categories & Tags tabs similar structure */}
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge, Input
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- DropdownMenu (similar to previous examples)
- Icons: Plus, MoreHorizontal

**API Calls:**
- Load posts: `GET /blog/posts?status={filter}&search={query}`
- Create post: `POST /blog/posts`
- Publish: `POST /blog/posts/{post_id}/publish`
- Delete: `DELETE /blog/posts/{post_id}`

---

### Newsletter Management

**Route:** `/[locale]/portal/newsletter`
**File:** `src/app/[locale]/portal/newsletter/page.tsx`

**API Endpoints:**
- `GET /newsletter/campaigns` - List campaigns
- `POST /newsletter/campaigns` - Create campaign
- `POST /newsletter/campaigns/{campaign_id}/schedule` - Schedule campaign
- `POST /newsletter/campaigns/{campaign_id}/send-now` - Send immediately
- `GET /newsletter/campaigns/{campaign_id}/stats` - Campaign stats
- `GET /newsletter/subscribers` - List subscribers
- `GET /newsletter/templates` - List templates

**Features:**
- Campaign list and management
- Create/schedule campaigns
- View campaign statistics
- Subscriber management
- Template library

**Layout:**

```tsx
<div>
  <PageHeader
    title="Newsletter"
    description="Manage campaigns and subscribers"
    actions={
      <Button onClick={() => setCreateCampaignOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Campaign
      </Button>
    }
  />

  {/* Stats Cards */}
  <div className="grid gap-4 md:grid-cols-4 mb-6">
    <StatCard
      title="Total Subscribers"
      value={stats.total_subscribers}
      icon={Users}
    />
    <StatCard
      title="Active Campaigns"
      value={stats.active_campaigns}
      icon={Send}
    />
    <StatCard
      title="Avg Open Rate"
      value={`${stats.avg_open_rate}%`}
      icon={Mail}
    />
    <StatCard
      title="Avg Click Rate"
      value={`${stats.avg_click_rate}%`}
      icon={MousePointer}
    />
  </div>

  {/* Tabs */}
  <Tabs defaultValue="campaigns">
    <TabsList className="mb-6">
      <TabsTrigger value="campaigns">Campaigns</TabsTrigger>
      <TabsTrigger value="subscribers">Subscribers</TabsTrigger>
      <TabsTrigger value="templates">Templates</TabsTrigger>
    </TabsList>

    {/* Campaigns Tab */}
    <TabsContent value="campaigns">
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Scheduled</TableHead>
              <TableHead>Recipients</TableHead>
              <TableHead>Open Rate</TableHead>
              <TableHead>Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {campaigns.map(campaign => (
              <TableRow key={campaign.id}>
                <TableCell>
                  <div>
                    <p className="font-medium">{campaign.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {campaign.subject}
                    </p>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariants[campaign.status]}>
                    {campaign.status}
                  </Badge>
                </TableCell>
                <TableCell>
                  {campaign.scheduled_at ? formatDateTime(campaign.scheduled_at) : '-'}
                </TableCell>
                <TableCell>{campaign.recipients_count}</TableCell>
                <TableCell>
                  {campaign.open_rate ? `${campaign.open_rate}%` : '-'}
                </TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => viewStats(campaign.id)}>
                        View Stats
                      </DropdownMenuItem>
                      {campaign.status === 'draft' && (
                        <>
                          <DropdownMenuItem onClick={() => editCampaign(campaign)}>
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => scheduleCampaign(campaign.id)}>
                            Schedule
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => sendNow(campaign.id)}>
                            Send Now
                          </DropdownMenuItem>
                        </>
                      )}
                      {campaign.status === 'scheduled' && (
                        <DropdownMenuItem onClick={() => cancelCampaign(campaign.id)}>
                          Cancel
                        </DropdownMenuItem>
                      )}
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </TabsContent>

    {/* Subscribers & Templates tabs... */}
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table components
- Button, Badge
- DropdownMenu
- Icons: Plus, Users, Send, Mail, MousePointer, MoreHorizontal
- Custom: StatCard

**API Calls:**
- Load campaigns: `GET /newsletter/campaigns`
- Create: `POST /newsletter/campaigns`
- Schedule: `POST /newsletter/campaigns/{campaign_id}/schedule`
- View stats: `GET /newsletter/campaigns/{campaign_id}/stats`

---

### Badges Management

**Route:** `/[locale]/portal/gamification/badges`
**File:** `src/app/[locale]/portal/gamification/badges/page.tsx`

**API Endpoints:**
- `GET /gamification/badges` - List badges
- `POST /gamification/badges` - Create badge
- `PUT /gamification/badges/{badge_id}` - Update badge
- `DELETE /gamification/badges/{badge_id}` - Delete badge
- `GET /gamification/badges/categories` - Get categories
- `POST /gamification/volunteers/{volunteer_id}/badges/award` - Award badge

**Features:**
- Badge library
- Create/edit badges
- Award badges to volunteers
- View badge recipients

**Layout:**

```tsx
<div>
  <PageHeader
    title="Badges"
    description="Manage gamification badges"
    actions={
      <Button onClick={() => setCreateBadgeOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        Create Badge
      </Button>
    }
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input placeholder="Search badges..." className="max-w-sm" />
        <Select value={categoryFilter} onValueChange={setCategoryFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Categories</SelectItem>
            {categories.map(cat => (
              <SelectItem key={cat} value={cat}>{cat}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Badges Grid */}
  <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
    {badges.map(badge => (
      <Card key={badge.id}>
        <CardContent className="pt-6">
          <div className="text-center">
            <div className="mx-auto w-20 h-20 mb-3">
              <img
                src={badge.icon_url}
                alt={badge.name}
                className="w-full h-full object-contain"
              />
            </div>
            <h3 className="font-semibold mb-1">{badge.name}</h3>
            <Badge variant="outline" className="mb-3">
              {badge.category}
            </Badge>
            <p className="text-sm text-muted-foreground mb-3">
              {badge.description}
            </p>
            <div className="text-sm text-muted-foreground">
              <p>{badge.points_value} points</p>
              <p>{badge.earned_count} awarded</p>
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => awardBadge(badge.id)}
          >
            Award
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="flex-1"
            onClick={() => editBadge(badge)}
          >
            Edit
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>

  {/* Create Badge Dialog */}
  <Dialog open={createBadgeOpen} onOpenChange={setCreateBadgeOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Create Badge</DialogTitle>
      </DialogHeader>
      <Form>
        <FormField name="name" label="Badge Name">
          <Input />
        </FormField>
        <FormField name="description" label="Description">
          <Textarea />
        </FormField>
        <FormField name="category" label="Category">
          <Select>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {categories.map(cat => (
                <SelectItem key={cat} value={cat}>{cat}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        <FormField name="points_value" label="Points Value">
          <Input type="number" />
        </FormField>
        <FormField name="icon" label="Icon">
          <Input type="file" accept="image/*" />
        </FormField>
      </Form>
      <DialogFooter>
        <Button variant="outline" onClick={() => setCreateBadgeOpen(false)}>
          Cancel
        </Button>
        <Button onClick={createBadge}>Create Badge</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</div>
```

**Components:**
- Card, CardContent, CardFooter
- Button, Badge, Input, Textarea
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
- Form, FormField
- Icons: Plus

**API Calls:**
- Load badges: `GET /gamification/badges?category={filter}&search={query}`
- Create: `POST /gamification/badges`
- Update: `PUT /gamification/badges/{badge_id}`
- Award: `POST /gamification/volunteers/{volunteer_id}/badges/award` with `{ badge_id: "uuid" }`

---

### Achievements Management

**Route:** `/[locale]/portal/gamification/achievements`
**File:** `src/app/[locale]/portal/gamification/achievements/page.tsx`

**API Endpoints:**
- `GET /gamification/achievements` - List achievements
- `GET /gamification/achievements/types` - Get achievement types
- `POST /gamification/achievements` - Create achievement
- `PUT /gamification/achievements/{achievement_id}` - Update achievement
- `DELETE /gamification/achievements/{achievement_id}` - Delete achievement

**Features:**
- Achievement library with type filter
- Create/edit achievements with target value and criteria
- View how many volunteers have completed each achievement
- Delete achievements

**Layout:**

```tsx
<div>
  <PageHeader
    title="Achievements"
    description="Manage volunteer achievement milestones"
    actions={
      <Button onClick={() => setCreateOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        Create Achievement
      </Button>
    }
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input placeholder="Search achievements..." className="max-w-sm" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {achievementTypes.map(t => (
              <SelectItem key={t} value={t}>{t}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Achievements Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Achievement</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Target</TableHead>
          <TableHead>Completed By</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {achievements.map(achievement => (
          <TableRow key={achievement.id}>
            <TableCell>
              <p className="font-medium">{achievement.name}</p>
              <p className="text-sm text-muted-foreground">{achievement.description}</p>
            </TableCell>
            <TableCell>
              <Badge variant="outline">{achievement.achievement_type}</Badge>
            </TableCell>
            <TableCell>{achievement.target_value}</TableCell>
            <TableCell>{achievement.completed_count} volunteers</TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => editAchievement(achievement)}>Edit</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => deleteAchievement(achievement.id)}
                    className="text-destructive"
                  >
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>

  {/* Create/Edit Dialog */}
  <Dialog open={createOpen} onOpenChange={setCreateOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>{editingAchievement ? 'Edit Achievement' : 'Create Achievement'}</DialogTitle>
      </DialogHeader>
      <Form>
        <FormField name="name" label="Name"><Input /></FormField>
        <FormField name="description" label="Description"><Textarea /></FormField>
        <FormField name="achievement_type" label="Type">
          <Select>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              {achievementTypes.map(t => (
                <SelectItem key={t} value={t}>{t}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </FormField>
        <FormField name="target_value" label="Target Value">
          <Input type="number" min="1" />
        </FormField>
      </Form>
      <DialogFooter>
        <Button variant="outline" onClick={() => setCreateOpen(false)}>Cancel</Button>
        <Button onClick={saveAchievement}>Save</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge, Input, Textarea
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Form, FormField
- Icons: Plus, MoreHorizontal

**API Calls:**
- Load achievements: `GET /gamification/achievements?search={query}&achievement_type={filter}`
- Load types: `GET /gamification/achievements/types`
- Create: `POST /gamification/achievements`
- Update: `PUT /gamification/achievements/{achievement_id}`
- Delete: `DELETE /gamification/achievements/{achievement_id}`

---

### Projects Management (Admin)

**Route:** `/[locale]/portal/projects`
**File:** `src/app/[locale]/portal/projects/page.tsx`

**API Endpoints:**
- `GET /projects/` - List all projects
- `GET /projects/stats` - Project statistics
- `POST /projects/` - Create project
- `PUT /projects/{project_id}` - Update project
- `DELETE /projects/{project_id}` - Delete/cancel project
- `GET /projects/{project_id}/team` - View team
- `GET /projects/{project_id}/activity` - View activity log
- `GET /users/?user_type=project_manager` - List PMs for assignment

**Features:**
- Full project directory (all projects, all PMs)
- Create, edit, cancel projects
- Assign/change project manager
- View project team and activity
- Filter by status, PM, date range

**Layout:**

```tsx
<div>
  <PageHeader
    title="Projects"
    description="Manage all organization projects"
    actions={
      <Button onClick={() => setCreateOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        New Project
      </Button>
    }
  />

  {/* Stats */}
  <div className="grid gap-4 md:grid-cols-4 mb-6">
    <StatCard title="Total" value={stats.total} icon={Folder} />
    <StatCard title="Active" value={stats.active} icon={Folder} variant="success" />
    <StatCard title="Completed" value={stats.completed} icon={CheckCircle} />
    <StatCard title="On Hold" value={stats.on_hold} icon={PauseCircle} variant="warning" />
  </div>

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input placeholder="Search projects..." className="max-w-sm" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="on_hold">On Hold</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
        <Select value={pmFilter} onValueChange={setPmFilter}>
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All Project Managers" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All PMs</SelectItem>
            {projectManagers.map(pm => (
              <SelectItem key={pm.id} value={pm.id}>{pm.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Projects Table */}
  <Card>
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Project</TableHead>
          <TableHead>Manager</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Tasks</TableHead>
          <TableHead>Team</TableHead>
          <TableHead>End Date</TableHead>
          <TableHead>Progress</TableHead>
          <TableHead>Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {projects.map(project => (
          <TableRow key={project.id}>
            <TableCell>
              <p className="font-medium">{project.name}</p>
              <p className="text-sm text-muted-foreground line-clamp-1">{project.description}</p>
            </TableCell>
            <TableCell>{project.project_manager_name}</TableCell>
            <TableCell>
              <Badge variant={statusVariants[project.status]}>{project.status}</Badge>
            </TableCell>
            <TableCell>{project.tasks_completed}/{project.tasks_total}</TableCell>
            <TableCell>{project.team_size}</TableCell>
            <TableCell>{formatDate(project.end_date)}</TableCell>
            <TableCell>
              <div className="flex items-center gap-2">
                <Progress value={project.completion_percentage} className="w-16" />
                <span className="text-xs">{project.completion_percentage}%</span>
              </div>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => viewProject(project.id)}>View Details</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => editProject(project)}>Edit</DropdownMenuItem>
                  <DropdownMenuItem onClick={() => viewActivity(project.id)}>Activity Log</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem
                    onClick={() => cancelProject(project.id)}
                    className="text-destructive"
                  >
                    Cancel Project
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
</div>
```

**Components:**
- Card, CardContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge, Input, Progress
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator
- Icons: Plus, Folder, CheckCircle, PauseCircle, MoreHorizontal
- Custom: StatCard

**API Calls:**
- Load projects: `GET /projects/?status={filter}&project_manager_id={filter}&search={query}&page={page}`
- Load stats: `GET /projects/stats`
- Create: `POST /projects/`
- Update: `PUT /projects/{project_id}`
- Cancel: `DELETE /projects/{project_id}`

---

### Resources Management

**Route:** `/[locale]/portal/resources`
**File:** `src/app/[locale]/portal/resources/page.tsx`

**API Endpoints:**
- `GET /resources/` - List all resources
- `GET /resources/stats` - Resource statistics
- `POST /resources/` - Create resource
- `GET /resources/{resource_id}` - Get resource detail
- `GET /projects/{project_id}/resources` - Resources allocated to a project
- `POST /projects/{project_id}/resources` - Allocate resource to project
- `PUT /projects/{project_id}/resources/{allocation_id}` - Update allocation
- `DELETE /projects/{project_id}/resources/{allocation_id}` - Remove allocation

**Features:**
- Resource inventory list
- Create resources
- View allocations per project
- Allocate/deallocate resources to projects

**Layout:**

```tsx
<div>
  <PageHeader
    title="Resources"
    description="Manage organization resources and project allocations"
    actions={
      <Button onClick={() => setCreateOpen(true)}>
        <Plus className="mr-2 h-4 w-4" />
        Add Resource
      </Button>
    }
  />

  {/* Stats */}
  <div className="grid gap-4 md:grid-cols-3 mb-6">
    <StatCard title="Total Resources" value={stats.total} icon={Package} />
    <StatCard title="Allocated" value={stats.allocated} icon={Package} variant="warning" />
    <StatCard title="Available" value={stats.available} icon={Package} variant="success" />
  </div>

  <Tabs defaultValue="inventory">
    <TabsList className="mb-6">
      <TabsTrigger value="inventory">Inventory</TabsTrigger>
      <TabsTrigger value="allocations">Project Allocations</TabsTrigger>
    </TabsList>

    <TabsContent value="inventory">
      <Card>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Resource</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Quantity</TableHead>
              <TableHead>Unit</TableHead>
              <TableHead>Allocated</TableHead>
              <TableHead>Available</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {resources.map(resource => (
              <TableRow key={resource.id}>
                <TableCell>
                  <p className="font-medium">{resource.name}</p>
                  <p className="text-sm text-muted-foreground">{resource.description}</p>
                </TableCell>
                <TableCell><Badge variant="outline">{resource.type}</Badge></TableCell>
                <TableCell>{resource.total_quantity}</TableCell>
                <TableCell>{resource.unit}</TableCell>
                <TableCell>{resource.allocated_quantity}</TableCell>
                <TableCell>
                  <span className={resource.available_quantity === 0 ? 'text-destructive' : 'text-green-600'}>
                    {resource.available_quantity}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </TabsContent>

    <TabsContent value="allocations">
      {/* Project selector then show allocations table */}
      <Card className="mb-4">
        <CardContent className="pt-6">
          <Select value={selectedProject} onValueChange={setSelectedProject}>
            <SelectTrigger className="w-[280px]">
              <SelectValue placeholder="Select a project" />
            </SelectTrigger>
            <SelectContent>
              {projects.map(p => (
                <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardContent>
      </Card>
      {/* Allocations table for selected project */}
    </TabsContent>
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Icons: Plus, Package
- Custom: StatCard

**API Calls:**
- Load resources: `GET /resources/?page={page}&limit={limit}`
- Load stats: `GET /resources/stats`
- Create resource: `POST /resources/`
- Load allocations: `GET /projects/{project_id}/resources`
- Add allocation: `POST /projects/{project_id}/resources` with `{ "resource_id": "uuid", "quantity": 5, "notes": "..." }`
- Remove allocation: `DELETE /projects/{project_id}/resources/{allocation_id}`

---

### Contact Management (Admin)

**Route:** `/[locale]/portal/contact`
**File:** `src/app/[locale]/portal/contact/page.tsx`

**Same layout as Staff Contact Submissions.** Admin has identical functionality with the same API endpoints.

**API Calls:**
- Load submissions: `GET /contact/submissions?is_read={filter}&page={page}&limit={limit}`
- Mark read: `PATCH /contact/submissions/{submission_id}/read`
- Delete: `DELETE /contact/submissions/{submission_id}`

---

### Analytics

**Route:** `/[locale]/portal/analytics`
**File:** `src/app/[locale]/portal/analytics/page.tsx`

**API Endpoints:**
- `GET /analytics/dashboard` - Analytics overview
- `GET /analytics/metrics/time-series?metric={type}&granularity={day|week|month}&start={date}&end={date}` - Time-series chart data
- `GET /analytics/activity` - Activity log feed

**Features:**
- System-wide KPI cards
- Time-series charts for key metrics (volunteers, hours, tasks, projects)
- Granularity selector (daily/weekly/monthly)
- Date range filter
- Activity feed

**Layout:**

```tsx
<div>
  <PageHeader
    title="Analytics"
    description="System-wide performance metrics and trends"
  />

  {/* Date + Granularity Controls */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange ? formatDateRange(dateRange) : "Select date range"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar mode="range" selected={dateRange} onSelect={setDateRange} />
          </PopoverContent>
        </Popover>
        <Select value={granularity} onValueChange={setGranularity}>
          <SelectTrigger className="w-[140px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="day">Daily</SelectItem>
            <SelectItem value="week">Weekly</SelectItem>
            <SelectItem value="month">Monthly</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* KPI Cards */}
  <div className="grid gap-4 md:grid-cols-4 mb-6">
    <StatCard title="Active Volunteers" value={kpis.active_volunteers} icon={Users} trend={kpis.volunteer_trend} />
    <StatCard title="Hours Logged" value={kpis.total_hours} icon={Clock} trend={kpis.hours_trend} />
    <StatCard title="Tasks Completed" value={kpis.tasks_completed} icon={CheckSquare} trend={kpis.tasks_trend} />
    <StatCard title="Active Projects" value={kpis.active_projects} icon={Folder} />
  </div>

  {/* Charts Grid */}
  <div className="grid gap-6 md:grid-cols-2">
    <Card>
      <CardHeader>
        <CardTitle>Volunteer Hours Over Time</CardTitle>
      </CardHeader>
      <CardContent>
        <BarChart data={hoursTimeSeries} />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Task Completion Rate</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart data={taskTimeSeries} />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>New Volunteers</CardTitle>
      </CardHeader>
      <CardContent>
        <BarChart data={volunteerTimeSeries} />
      </CardContent>
    </Card>

    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-64 overflow-y-auto">
          {activityLog.map(entry => (
            <div key={entry.id} className="flex gap-3 text-sm">
              <span className="text-muted-foreground whitespace-nowrap">
                {formatRelativeTime(entry.timestamp)}
              </span>
              <span>{entry.description}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardContent
- Button, Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Popover, PopoverTrigger, PopoverContent, Calendar
- Icons: CalendarIcon, Users, Clock, CheckSquare, Folder
- Custom: StatCard, BarChart, LineChart

**API Calls:**
- Load dashboard: `GET /analytics/dashboard`
- Hours time series: `GET /analytics/metrics/time-series?metric=hours&granularity={granularity}&start={start}&end={end}`
- Tasks time series: `GET /analytics/metrics/time-series?metric=tasks_completed&granularity={granularity}&start={start}&end={end}`
- Volunteers time series: `GET /analytics/metrics/time-series?metric=new_volunteers&granularity={granularity}&start={start}&end={end}`
- Activity log: `GET /analytics/activity?limit=50`

---

### Reports (Admin)

**Route:** `/[locale]/portal/reports`
**File:** `src/app/[locale]/portal/reports/page.tsx`

**API Endpoints:**
- `GET /reports/dashboard` - High-level summary with key metrics
- `GET /reports/projects` - Full project report
- `GET /reports/volunteers` - Full volunteer report
- `GET /reports/tasks` - Full task report
- `GET /reports/resources` - Resource utilization report
- `GET /reports/export/projects/csv` - Export projects CSV
- `GET /reports/export/volunteers/csv` - Export volunteers CSV
- `GET /reports/export/tasks/csv` - Export tasks CSV
- `GET /reports/export/hours/csv` - Export hours CSV

**Features:**
- Tabbed reports: Summary | Projects | Volunteers | Tasks | Resources
- Date range filter applied to all tabs
- CSV export per report type
- Summary tab shows `GET /reports/dashboard` aggregate KPIs

**Layout:**

```tsx
<div>
  <PageHeader
    title="Reports"
    description="Organization-wide performance reports and exports"
  />

  {/* Date Range */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline">
              <CalendarIcon className="mr-2 h-4 w-4" />
              {dateRange ? formatDateRange(dateRange) : "Select date range"}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0">
            <Calendar mode="range" selected={dateRange} onSelect={setDateRange} />
          </PopoverContent>
        </Popover>
        <Button variant="outline" onClick={applyDateRange}>Apply</Button>
      </div>
    </CardContent>
  </Card>

  <Tabs defaultValue="summary">
    <TabsList className="mb-6">
      <TabsTrigger value="summary">Summary</TabsTrigger>
      <TabsTrigger value="projects">Projects</TabsTrigger>
      <TabsTrigger value="volunteers">Volunteers</TabsTrigger>
      <TabsTrigger value="tasks">Tasks</TabsTrigger>
      <TabsTrigger value="resources">Resources</TabsTrigger>
    </TabsList>

    {/* Summary Tab */}
    <TabsContent value="summary">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <StatCard title="Total Hours Logged" value={summary.total_hours} icon={Clock} />
        <StatCard title="Active Volunteers" value={summary.active_volunteers} icon={Users} />
        <StatCard title="Tasks Completed" value={summary.tasks_completed} icon={CheckSquare} />
        <StatCard title="Projects Active" value={summary.active_projects} icon={Folder} />
      </div>
    </TabsContent>

    {/* Projects Tab - same structure as PM Reports */}
    {/* Volunteers Tab - columns: name, hours, tasks, projects, badges earned */}
    {/* Tasks Tab - columns: title, project, status, assigned volunteers, hours */}
    {/* Resources Tab - columns: name, type, total, allocated, utilization % */}
  </Tabs>
</div>
```

**Components:**
- Card, CardContent
- Tabs, TabsList, TabsTrigger, TabsContent
- Table, TableHeader, TableHead, TableBody, TableRow, TableCell
- Button, Badge, Progress
- Popover, PopoverTrigger, PopoverContent, Calendar
- Icons: CalendarIcon, Clock, Users, CheckSquare, Folder, Download
- Custom: StatCard

**API Calls:**
- Summary: `GET /reports/dashboard`
- Projects: `GET /reports/projects?start_date={start}&end_date={end}`
- Volunteers: `GET /reports/volunteers?start_date={start}&end_date={end}`
- Tasks: `GET /reports/tasks?start_date={start}&end_date={end}`
- Resources: `GET /reports/resources?start_date={start}&end_date={end}`
- Exports: `GET /reports/export/{type}/csv?start_date={start}&end_date={end}`

---

## COLLABORATOR

### Sidebar Navigation

```typescript
// components/app-sidebar.tsx - Collaborator section
const collaboratorNav = [
  {
    title: t('nav.overview'),
    href: `/${locale}/portal`,
    icon: LayoutDashboard,
    roles: ['collaborator'],
  },
  {
    title: t('nav.projects'),
    href: `/${locale}/portal/projects`,
    icon: Folder,
    roles: ['collaborator'],
  },
  {
    title: t('nav.resources'),
    href: `/${locale}/portal/resources`,
    icon: Package,
    roles: ['collaborator'],
  },
]
```

---

### Dashboard (Collaborator)

**Route:** `/[locale]/portal`
**File:** `src/app/[locale]/portal/page.tsx`

**API Endpoints:**
- `GET /projects/?status=active` - Active projects overview
- `GET /projects/stats` - Project statistics

**Features:**
- Read-only overview of active projects
- Project stats summary
- No action buttons (view only)

**Layout:**

```tsx
<div>
  <PageHeader
    title="Welcome"
    description="Organization project overview"
  />

  {/* Stats Cards */}
  <div className="grid gap-4 md:grid-cols-3 mb-6">
    <StatCard title="Active Projects" value={stats.active} icon={Folder} />
    <StatCard title="Total Volunteers" value={stats.total_volunteers} icon={Users} />
    <StatCard title="Hours Logged" value={stats.total_hours} icon={Clock} />
  </div>

  {/* Projects List */}
  <Card>
    <CardHeader>
      <CardTitle>Active Projects</CardTitle>
      <CardDescription>Current organization initiatives</CardDescription>
    </CardHeader>
    <CardContent>
      <div className="space-y-4">
        {projects.map(project => (
          <div key={project.id} className="flex items-center justify-between">
            <div>
              <p className="font-medium">{project.name}</p>
              <p className="text-sm text-muted-foreground line-clamp-1">{project.description}</p>
            </div>
            <div className="flex items-center gap-4">
              <Progress value={project.completion_percentage} className="w-24" />
              <span className="text-sm text-muted-foreground">{project.completion_percentage}%</span>
              <Button variant="outline" size="sm" asChild>
                <Link href={`/portal/projects/${project.id}`}>View</Link>
              </Button>
            </div>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent
- Button, Progress, Link
- Icons: Folder, Users, Clock
- Custom: StatCard

**API Calls:**
- Load stats: `GET /projects/stats`
- Load active projects: `GET /projects/?status=active&page=1&limit=10`

---

### Projects (Collaborator)

**Route:** `/[locale]/portal/projects`
**File:** `src/app/[locale]/portal/projects/page.tsx`

**API Endpoints:**
- `GET /projects/` - List projects (read-only)
- `GET /projects/{project_id}` - Project details
- `GET /projects/{project_id}/team` - Team members
- `GET /projects/{project_id}/milestones` - Milestones
- `GET /projects/{project_id}/activity` - Activity log

**Features:**
- Read-only project list with search and status filter
- View project details: description, team, milestones, progress
- No create/edit/delete actions

**Layout:**

```tsx
<div>
  <PageHeader
    title="Projects"
    description="Browse organization projects"
  />

  {/* Filters */}
  <Card className="mb-6">
    <CardContent className="pt-6">
      <div className="flex gap-4">
        <Input
          placeholder="Search projects..."
          className="max-w-sm"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </CardContent>
  </Card>

  {/* Projects Grid */}
  <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
    {projects.map(project => (
      <Card key={project.id}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <CardTitle className="text-lg">{project.name}</CardTitle>
            <Badge variant={statusVariants[project.status]}>{project.status}</Badge>
          </div>
          <CardDescription className="line-clamp-2">{project.description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span className="text-muted-foreground">{project.completion_percentage}%</span>
              </div>
              <Progress value={project.completion_percentage} />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="h-4 w-4" />
              <span>{project.team_size} volunteers</span>
            </div>
          </div>
        </CardContent>
        <CardFooter>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/portal/projects/${project.id}`}>View Details</Link>
          </Button>
        </CardFooter>
      </Card>
    ))}
  </div>
</div>
```

**Components:**
- Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter
- Button, Badge, Input, Progress
- Select, SelectTrigger, SelectValue, SelectContent, SelectItem
- Icons: Users

**API Calls:**
- Load projects: `GET /projects/?status={filter}&search={query}&page={page}`
- Load project details: `GET /projects/{project_id}`
- Load team: `GET /projects/{project_id}/team`
- Load milestones: `GET /projects/{project_id}/milestones`
- Load activity: `GET /projects/{project_id}/activity`

---

### Resources (Collaborator)

**Route:** `/[locale]/portal/resources`
**File:** `src/app/[locale]/portal/resources/page.tsx`

**API Endpoints:**
- `GET /resources/` - List resources (read-only)
- `GET /resources/{resource_id}` - Resource details

**Features:**
- Read-only resource inventory
- Search and filter by type
- No create/edit/delete

**Layout:** Same structure as Admin Resources Management — Inventory tab only, no allocation management, no create button.

**API Calls:**
- Load resources: `GET /resources/?page={page}&limit={limit}`

---

## API Reference Patterns

### Pagination

Most list endpoints support pagination:

```
GET /endpoint?page=1&limit=20&offset=0
```

Response format:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

### Filtering

Filter with query parameters:

```
GET /volunteers?status=active&skills=communication&search=john
```

### Sorting

```
GET /tasks?sort_by=due_date&sort_order=asc
```

### Error Handling

Standard error response:
```json
{
  "error": "Error message",
  "detail": "Detailed explanation",
  "status_code": 400
}
```

Display errors with shadcn Toast:
```tsx
import { useToast } from "@/components/ui/use-toast"

const { toast } = useToast()

toast({
  title: "Error",
  description: error.message,
  variant: "destructive"
})
```

---

## Implementation Priority

### Phase 1: Volunteer Experience (Weeks 1-2)
1. Dashboard
2. My Tasks
3. My Hours
4. Available Tasks
5. My Achievements
6. Leaderboards

### Phase 2: Project Manager (Weeks 3-4)
1. Dashboard
2. My Projects
3. Tasks Management (`/tasks`)
4. Team Management (`/team`)
5. Time Approvals (`/time-approvals`)
6. Reports (`/reports`)

### Phase 3: Staff Member (Week 5)
1. Dashboard
2. Volunteers Management (`/volunteers`)
3. Time Approvals (`/time-approvals`)
4. Tasks Assignment (`/tasks`)
5. Contact Submissions (`/contact`)
6. Gamification Awards (`/gamification`)

### Phase 4: Admin (Weeks 6-8)
1. Dashboard
2. Users Management (`/users`)
3. Projects Management (`/projects`)
4. Resources Management (`/resources`)
5. Blog Management (`/blog`)
6. Newsletter Management (`/newsletter`)
7. Contact Management (`/contact`)
8. Badges Management (`/gamification/badges`)
9. Achievements Management (`/gamification/achievements`)
10. Analytics (`/analytics`)
11. Reports (`/reports`)

### Phase 5: Collaborator (Week 9)
1. Dashboard
2. Projects (read-only)
3. Resources (read-only)

---

## Component Reuse Summary

### Shared Components Across All Roles

- **StatCard** - Used in all dashboards
- **PageHeader** - Used on all pages
- **DataTable** - Used for all tabular data
- **EmptyState** - Used when no data available
- **LoadingState** - Used during data fetches
- **FormField** - Used in all forms
- **StatusBadge** - Used for all status displays
- **ActionDropdown** - Used for row actions in tables

### Role-Specific Components

**Volunteer:**
- TaskCard
- BadgeIcon
- AchievementProgress
- LeaderboardPodium

**Project Manager:**
- ProjectCard
- MilestoneTimeline
- TeamMemberCard

**Admin:**
- CampaignStatsCard
- UserPermissions
- BadgeEditor
- AchievementEditor
- ResourceAllocationRow
- TimeSeriesChart

**Collaborator:**
- ProjectCard (read-only variant)
- ResourceRow (read-only)

---

## Detailed Manual Test Plan (Minimal Batch)

This plan validates all UI features in this specification with the smallest practical set of users and interactions.

### 1) Test Objective
- Validate end-to-end behavior for Volunteer, Project Manager, Staff Member, and Admin.
- Validate role permissions (allowed actions and blocked actions).
- Validate cross-role workflows (project creation, task assignment, hour logging, time approval, achievements).
- Validate admin-only modules (users, blog, newsletter, badges).

### 2) Minimal Test Accounts

| Key | Role | Purpose |
|-----|------|---------|
| `A1` | Admin | Bootstrap data, manage users, run admin modules |
| `PM1` | Project Manager | Own and manage one project |
| `S1` | Staff Member | Volunteer operations + time approval + points/badges |
| `V1` | Volunteer | Primary volunteer journey |
| `V2` | Volunteer | Secondary volunteer for leaderboard and assignment coverage |

### 3) Minimal Shared Dataset
- `Project P1` (owned by `PM1`): active, has team `V1`, `V2`, `S1`.
- `Project P2` (owned by `A1`): active, no volunteer assigned initially (used for permission and visibility checks).
- Tasks in `P1`:
1. `T1` open task (available for signup)
2. `T2` assigned task (`V1`)
3. `T3` completed task (`V2`)
- One pending time log from `V1` on `T2` (for approval flow).
- One approved time log from `V2` (for analytics/leaderboard comparison).
- 1 blog category, 1 tag, 1 draft post, 1 published post.
- Newsletter: 1 confirmed subscriber, 1 draft campaign.
- Gamification: 1 active badge; `V1` and `V2` have different point totals.

### 4) Execution Order (End-to-End)

#### Phase A - Admin Bootstrap (`A1`)
1. Create users `PM1`, `S1`, `V1`, `V2` in Users Management.
2. Create `P1` and `P2`; assign `PM1` as manager of `P1`.
3. Add team members to `P1`: `S1`, `V1`, `V2`.
4. Create `T1`, `T2`, `T3` in `P1` with statuses open/in-progress/completed.
5. Seed initial time logs (or create through volunteer flow, then return to admin checks).
6. Create blog category/tag + draft + published post.
7. Create newsletter template/campaign draft + ensure one confirmed subscriber.
8. Create one badge for gamification checks.

Expected:
- Entities appear in corresponding lists with correct counts.
- All created entities visible in admin dashboard KPIs.

#### Phase B - Volunteer Journey (`V1`)
1. Verify volunteer sidebar shows only volunteer pages.
2. Dashboard: check stats, current tasks, recent achievements, hours chart render.
3. My Tasks: filter by status/priority/project; open task details; update own assigned task status.
4. Available Tasks: view `T1`, sign up, verify it moves to My Tasks and no longer shows as available.
5. My Hours: log new hours against `P1`/`T2` with valid form data; verify new row as `pending`.
6. Edit pending log (if UI allows) and confirm updated value.
7. My Achievements: verify points summary, earned badges list, timeline entries.
8. Leaderboards: validate points/hours/projects tabs and ranking placement relative to `V2`.

Expected:
- Volunteer can only operate on own assignments/logs.
- New time log enters approval queue.
- UI state transitions are immediate and consistent after actions.

#### Phase C - Project Manager Journey (`PM1`)
1. Verify PM sidebar and dashboard cards (active projects, tasks, approvals).
2. My Projects: open `P1`, validate details, team list, progress indicators.
3. Edit `P1` metadata and confirm persistence.
4. Create or update one task in `P1`; assign/reassign `V1` or `V2`.
5. Open Time Approvals and approve pending log from `V1`.
6. Confirm approved entry disappears from pending queue and appears in approved/history views.

Expected:
- PM actions are limited to owned project (`P1`), not `P2`.
- Approval updates volunteer and dashboard metrics.

#### Phase D - Staff Journey (`S1`)
1. Volunteers Management: search/filter volunteers; open `V1` profile; update one editable field.
2. Time Approvals: create one new pending log as `V1` (if needed), approve or reject as staff.
3. Award points or badge to `V1`; verify reflected in achievements/leaderboard.
4. Validate staff can view operational lists but cannot access admin-only modules.

Expected:
- Staff can manage volunteer operational workflows.
- Staff cannot create projects or access users/blog/newsletter admin screens.

#### Phase E - Admin Module Validation (`A1`)
1. Admin Dashboard: verify global KPIs changed after prior actions.
2. Users Management: update role/status (activate/deactivate) for one non-critical test user.
3. Blog Management:
   - create/edit/delete draft post
   - publish post
   - verify published list and public visibility behavior
4. Newsletter Management:
   - review subscribers list
   - create/edit campaign
   - send test campaign (or trigger send-now in staging)
   - verify campaign status progression
5. Badges Management:
   - create/update/archive badge
   - award badge manually
   - verify it appears in volunteer achievements

Expected:
- Admin-only features are accessible and fully functional.
- Content states transition correctly (draft -> published, campaign draft -> sent).

### 5) Interaction Coverage Matrix

| Feature Group | Minimum Interactions Required |
|---------------|-------------------------------|
| Authentication/Session | Login/logout once per role; refresh token once |
| Role Navigation | Verify sidebar visibility once per role |
| Dashboard | Open each role dashboard and validate KPI consistency |
| Projects | Create, edit, assign team, view details, PM scope check |
| Tasks | Create, assign, volunteer signup, status update, filter/search |
| Hours/Approvals | Log hour (`V1`), approve (`PM1`), approve/reject (`S1`) |
| Volunteers | Staff edits volunteer profile and checks directory filters |
| Gamification | Award points/badge and verify achievements + leaderboard |
| Users (Admin) | Create role users, deactivate/reactivate one user |
| Blog (Admin) | Category/tag setup, draft create/edit, publish, delete |
| Newsletter (Admin/Public) | Subscribe/confirm, create campaign, send-now |
| Common UI Quality | Empty/loading/error/form validation/mobile for each key page |

### 6) Permission and Security Checks (Mandatory)

Run these negative tests during the same session:
1. `V1` attempts to access admin URL directly -> blocked/redirected.
2. `S1` attempts to create project -> blocked.
3. `PM1` attempts to edit `P2` (not owned) -> blocked.
4. `V2` attempts to edit `V1` time log -> blocked.
5. Hidden nav items must remain hidden even after hard refresh.

### 7) Page-Level Quality Checklist (Apply to Each Tested Screen)
- [ ] Data loads from expected APIs.
- [ ] Loading, empty, and error states are visible and correct.
- [ ] Filters/sorting/pagination update results correctly.
- [ ] Form validation messages and success/error toasts appear correctly.
- [ ] Mobile layout and keyboard accessibility are acceptable.
- [ ] State is consistent after refresh (no stale or duplicated records).

### 8) Exit Criteria
- All steps in Phases A-E pass.
- All permission negative tests pass.
- No severity-1 or severity-2 defects remain open.
- Any lower-severity defects are logged with reproducible steps and owner.

---

## Conclusion

This specification provides a complete mapping of all API endpoints to user interface screens organized by role. Each screen includes:

- Exact API endpoints to call
- shadcn component structure
- Layout code snippets
- Feature descriptions
- Component lists

Use this document as a reference during frontend development to ensure consistent, role-appropriate interfaces across the platform.
