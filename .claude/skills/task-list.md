---
description: Query and list tasks from TaskWarrior with context-aware filtering. Use when the user wants to see tasks, understand project status, or find specific work items.
tags: [task-management, taskwarrior, productivity, query]
---

# Task Listing and Query Skill

You are helping the user query and understand their TaskWarrior tasks. Use the right query patterns to show exactly what they need.

## Core Query Patterns

### 1. Next Actions (Most Common)

**What to work on next:**
```bash
task next
```

**Next tasks in a specific project:**
```bash
task project:PROJECTNAME next
```

**Next tasks without blocked items:**
```bash
task status:pending -BLOCKED next
```

### 2. Project Views

**All projects:**
```bash
task projects
```

**All tasks in a project:**
```bash
task project:PROJECTNAME list
```

**Active tasks in a project:**
```bash
task project:PROJECTNAME +ACTIVE list
```

**Completed tasks in a project:**
```bash
task project:PROJECTNAME status:completed list
```

### 3. Status-Based Queries

**What am I currently working on:**
```bash
task +ACTIVE list
```

**All pending tasks:**
```bash
task status:pending list
```

**Blocked tasks (need attention):**
```bash
task +BLOCKED list
```

**Tasks blocking others:**
```bash
task +BLOCKING list
```

**Recently completed:**
```bash
task status:completed end.after:today-7days list
```

### 4. Tag-Based Queries

**All bugs:**
```bash
task +bug list
```

**Quick wins:**
```bash
task +quick -BLOCKED status:pending list
```

**Frontend work:**
```bash
task +frontend status:pending list
```

**Combine tags:**
```bash
task +bug +backend priority:H list
```

### 5. Priority Queries

**High priority tasks:**
```bash
task priority:H status:pending list
```

**High priority, unblocked, next actions:**
```bash
task priority:H -BLOCKED next
```

### 6. Dependency Views

**See task dependencies:**
```bash
task ID info
```

**All parent tasks:**
```bash
task +parent status:pending list
```

**Child tasks of a parent:**
```bash
task depends:PARENT_ID list
```

### 7. Search Queries

**Search descriptions:**
```bash
task /authentication/ list
```

**Search in specific project:**
```bash
task project:myapp /login/ list
```

### 8. Time-Based Queries

**Tasks modified today:**
```bash
task modified:today list
```

**Tasks added this week:**
```bash
task entry.after:today-7days list
```

**Tasks due soon:**
```bash
task due.before:today+7days list
```

**Overdue tasks:**
```bash
task due.before:today status:pending list
```

### 9. Reporting and Statistics

**Summary report:**
```bash
task summary
```

**Burndown (completed over time):**
```bash
task burndown.daily
task burndown.weekly
```

**Project statistics:**
```bash
task project:PROJECTNAME stats
```

## Advanced Filtering

### Combine Multiple Filters

```bash
# High priority backend bugs
task +bug +backend priority:H status:pending list

# Frontend features not blocked
task +feature +frontend -BLOCKED status:pending next

# Quick wins in current project
task project:myapp +quick status:pending list

# Parent tasks with high priority
task +parent priority:H status:pending list
```

### Exclude Filters

```bash
# All tasks except bugs
task -bug status:pending list

# Tasks without any tags
task tags.none: status:pending list

# Non-blocked, non-active tasks
task -BLOCKED -ACTIVE status:pending list
```

## Context-Aware Responses

### When User Asks: "What should I work on?"

```bash
# 1. Show next actions
task next

# 2. Highlight quick wins if available
task +quick -BLOCKED next

# 3. Show high priority items
task priority:H -BLOCKED next
```

Response template:
```
Here's what you should work on:

High Priority Next Tasks:
[output from task priority:H next]

Quick Wins (if any):
[output from task +quick next]

Currently Active:
[output from task +ACTIVE list]
```

### When User Asks: "How's project X going?"

```bash
# 1. Project overview
task project:X summary

# 2. Pending tasks
task project:X status:pending list

# 3. Blocked items (need attention)
task project:X +BLOCKED list

# 4. Recently completed
task project:X completed.after:today-7days list
```

Response template:
```
Project X Status:

Pending: [count] tasks
Blocked: [count] tasks (need attention!)
Completed this week: [count] tasks

Next Actions:
[output from task project:X next limit:5]

Blocked Items:
[output from task project:X +BLOCKED list]
```

### When User Asks: "What did I accomplish?"

```bash
# Today
task completed today

# This week
task completed.after:today-7days list

# By project
task project:X completed.after:today-7days list
```

### When User Asks: "Why is task X blocked?"

```bash
# Get full task info
task X info

# Find what it depends on
task X info | grep -A5 "Dependencies"

# Check if dependencies are done
task depends:X list
```

Response template:
```
Task X is blocked because it depends on:

[List blocking tasks]

Status of blocking tasks:
[output from checking each dependency]
```

## Custom Reports

### Define in .taskrc

These custom reports provide useful views:

```
# Parent tasks with subtask counts
report.parents.description=Parent tasks
report.parents.columns=id,project,description.count,tags
report.parents.labels=ID,Project,Description,Tags
report.parents.filter=status:pending +parent
report.parents.sort=urgency-

# Quick wins
report.quick.description=Quick tasks
report.quick.columns=id,priority,project,tags,description.count
report.quick.labels=ID,Pri,Project,Tags,Description
report.quick.filter=status:pending +quick -BLOCKED
report.quick.sort=urgency-

# Blocked tasks with reasons
report.blocked.description=Blocked tasks
report.blocked.columns=id,project,description,depends
report.blocked.labels=ID,Project,Description,Depends On
report.blocked.filter=status:pending +BLOCKED
```

Usage:
```bash
task parents
task quick
task blocked
```

## Common User Questions and Queries

### "Show me the big picture"

```bash
# All projects with task counts
task projects

# Summary across all projects
task summary

# Parent tasks (major initiatives)
task +parent list
```

### "I want to context switch to project X"

```bash
# What's next in project X
task project:X next

# What's blocked (might need unblocking first)
task project:X +BLOCKED list

# What's in progress (might want to finish first)
task project:X +ACTIVE list
```

### "I have 30 minutes, what can I do?"

```bash
# Quick tasks
task +quick -BLOCKED next

# Or tasks estimated under 30 min (if using estimates)
task estimate.below:30min next
```

### "What's urgent?"

```bash
# High priority tasks
task priority:H status:pending next

# Overdue tasks
task due.before:today status:pending list

# Highest urgency
task status:pending list urgency\>10
```

### "What's blocking progress?"

```bash
# All blocked tasks
task +BLOCKED list

# Tasks that are blocking others
task +BLOCKING list

# Combination view
task +BLOCKED or +BLOCKING list
```

## Formatting Output

### For Users (Human-Readable)

Use default TaskWarrior output:
```bash
task next
task list
```

### For Processing (Machine-Readable)

Use JSON export:
```bash
task project:X export
task +bug status:pending export | jq '.[] | {id, description, priority}'
```

### For Reports

Use custom columns:
```bash
task rc.report.list.columns=id,project,description.count,tags list
```

## Interpreting Results

### Urgency Score

TaskWarrior calculates urgency based on:
- Priority (H=high, M=medium, L=low)
- Due date (closer = higher)
- Active status (+10 if started)
- Blocking status (+5 if blocking others)
- Tags (can add custom coefficients)

**High urgency (>10)**: Work on these first
**Medium urgency (5-10)**: Normal work
**Low urgency (<5)**: Background tasks

### Task Counts

When showing task counts, categorize:
- **Pending**: Not started
- **Active**: Currently working on (started)
- **Blocked**: Can't proceed
- **Completed**: Done

## Best Practices

### 1. Always Show Context

Don't just run `task list` - be specific:
```bash
# Bad
task list

# Good
task project:myapp status:pending next
```

### 2. Filter Out Noise

Exclude irrelevant tasks:
```bash
# Focus on actionable items
task -BLOCKED -WAITING status:pending next
```

### 3. Show Dependencies

When showing a parent task, show its children:
```bash
task PARENT_ID info
task depends:PARENT_ID list
```

### 4. Highlight Blockers

Always check for blocked tasks:
```bash
task project:X +BLOCKED list
```

### 5. Provide Multiple Views

Give users options:
```bash
# What's next overall
task next

# What's next in current project
task project:X next

# Quick wins
task +quick next
```

## Error Handling

### Empty Results

If a query returns nothing:
```
No tasks found matching: [criteria]

Try:
- task list (see all tasks)
- task projects (see all projects)
- task +PARENT list (see parent tasks)
```

### Invalid Filters

If filter syntax is wrong:
```
TaskWarrior error: [error message]

Did you mean:
- task project:X (not project=X)
- task priority:H (not priority=high)
- task +tag (not tag:value)
```

## Quick Reference

```bash
# Essential queries
task next                           # What to work on next
task +ACTIVE list                   # What I'm working on
task project:X next                 # Next in project X
task +BLOCKED list                  # What's blocked
task completed today                # What I finished today
task ID info                        # Full task details

# Filtering
task +tag                           # Has tag
task -tag                           # Doesn't have tag
task project:X                      # In project
task priority:H                     # High priority
task due.before:today              # Overdue
task status:pending                 # Not completed
task /keyword/                      # Search description

# Combining
task +bug priority:H -BLOCKED list # High-pri unblocked bugs
task project:X +feature next       # Next features in project X
```

## Remember

- **Start broad, then narrow**: `projects` → `project:X list` → `project:X +tag list`
- **Check for blockers**: Always show blocked tasks when reviewing projects
- **Show next actions**: Users want to know what to do, not just what exists
- **Provide context**: Include project, priority, and tags in output
- **Highlight urgency**: Surface high-priority and overdue tasks

Help users understand not just what tasks exist, but what they should work on next!
