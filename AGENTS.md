# TaskMan Agent Patterns

## Overview

This document defines patterns and best practices for AI agents (particularly Claude Code) when working with TaskWarrior and BugWarrior for project and task management. The core philosophy is **hierarchical decomposition**: breaking complex work into manageable, trackable units.

## Core Principles

### 1. Hierarchical Task Decomposition

**Every complex task should be broken down into subtasks.** This isn't just good practice—it's essential for:
- **Progress tracking**: See exactly where you are in a large project
- **Context switching**: Pause and resume work without losing place
- **Delegation**: Assign specific subtasks to team members or AI agents
- **Estimation accuracy**: Smaller tasks are easier to estimate
- **Motivation**: Completing subtasks provides regular wins

### 2. Project Structure

```
Epic/Initiative (GitHub Milestone)
  └── Project (TaskWarrior project: namespace)
      └── Parent Task (high-level goal)
          └── Subtask 1 (concrete, actionable)
          └── Subtask 2 (concrete, actionable)
              └── Sub-subtask 2.1 (if needed)
              └── Sub-subtask 2.2 (if needed)
          └── Subtask 3 (concrete, actionable)
```

### 3. Task Granularity Guidelines

**A good task:**
- Can be completed in 2 hours or less
- Has a clear definition of "done"
- Requires minimal context switching
- Is self-contained (or has clear dependencies)

**If a task doesn't meet these criteria, break it down further.**

## TaskWarrior Patterns

### Pattern 1: Creating a New Project

When starting a new project, always create a project task first:

```bash
# Create the project container task
task add project:myapp "Setup and implement MyApp" +project priority:H

# Add initial subtasks with dependencies
task add project:myapp "Research requirements and architecture" depends:PROJECT_TASK_ID
task add project:myapp "Design database schema" depends:RESEARCH_TASK_ID
task add project:myapp "Implement core API endpoints" depends:SCHEMA_TASK_ID
task add project:myapp "Write integration tests" depends:API_TASK_ID
```

**Key points:**
- Use `project:namespace` consistently
- Tag the parent task with `+project`
- Set priorities (H=High, M=Medium, L=Low)
- Use `depends:` to create dependency chains

### Pattern 2: Breaking Down Tasks

When you encounter a task that's too large:

```bash
# Original task (too large)
task 42 modify +needs-breakdown

# Create subtasks
task add project:myapp "Implement user authentication - setup passport.js" depends:42
task add project:myapp "Implement user authentication - create login endpoint" depends:42
task add project:myapp "Implement user authentication - create registration endpoint" depends:42
task add project:myapp "Implement user authentication - add JWT token generation" depends:42
task add project:myapp "Implement user authentication - write auth middleware" depends:42

# Mark original as a parent task
task 42 modify +parent "User authentication system (PARENT)"
```

**Key points:**
- Don't delete the original task—mark it as +parent
- All subtasks depend on the parent
- Subtasks inherit the project
- Use descriptive prefixes for related subtasks

### Pattern 3: Daily Workflow

```bash
# Morning: Review what's next
task next

# Start working on a task
task 15 start

# Add notes/annotations as you work
task 15 annotate "Found issue with database connection pooling"

# Complete the task
task 15 done

# End of day: Review what you accomplished
task completed today

# Look ahead to tomorrow
task project:myapp next
```

### Pattern 4: Managing Dependencies

```bash
# Create a task that depends on another
task add "Deploy to production" depends:42,43,44

# See what's blocking a task
task 50 info

# See all blocked tasks
task status:pending +BLOCKED list

# See all blocking tasks (tasks others depend on)
task status:pending +BLOCKING list
```

### Pattern 5: Using Tags Effectively

```bash
# Functional tags
+bug          # Bug fixes
+feature      # New features
+refactor     # Code improvements
+docs         # Documentation
+test         # Testing tasks

# Status tags
+blocked      # Waiting on something
+review       # Ready for review
+parent       # Parent task with subtasks
+quick        # Can be done in <30 minutes

# Context tags
+frontend     # Frontend work
+backend      # Backend work
+database     # Database work
+devops       # Infrastructure/deployment

# Example: Add a quick bug fix
task add project:myapp "+bug +quick +backend Fix null pointer in user service" priority:H
```

## BugWarrior Integration

### Pattern 6: Syncing GitHub Issues

```bash
# Initial sync
bugwarrior-pull

# View synced issues
task +github list

# Work on a GitHub issue
task +github 123 start

# The issue will sync back to GitHub
# Completing the task locally does NOT close the GitHub issue
# Close issues on GitHub when truly done
```

### Pattern 7: Organizing External Issues

```bash
# After bugwarrior-pull, organize imported issues:

# Add project context to GitHub issues
task +github project:myapp modify project:myapp.github

# Break down complex GitHub issues
task 100 modify +parent
task add project:myapp.github "Implement first part of issue #123" depends:100

# Link related issues
task 101 modify depends:100
```

## Agent Interaction Patterns

### Pattern 8: Agent Task Creation

When Claude Code creates tasks, it should:

1. **Always check for existing related tasks first**
   ```bash
   task project:myapp list
   ```

2. **Create parent task if starting new feature**
   ```bash
   task add project:myapp "Implement dark mode support" +feature +parent priority:M
   ```

3. **Break down into concrete subtasks immediately**
   ```bash
   # Get the parent task ID (e.g., 50)
   task add project:myapp "Dark mode - Add theme context provider" depends:50 +frontend
   task add project:myapp "Dark mode - Create CSS variables for themes" depends:50 +frontend
   task add project:myapp "Dark mode - Add theme toggle component" depends:50 +frontend
   task add project:myapp "Dark mode - Persist theme preference" depends:50 +frontend
   task add project:myapp "Dark mode - Update all components" depends:50 +frontend
   task add project:myapp "Dark mode - Test in all browsers" depends:50 +test
   ```

4. **Set appropriate priorities and tags**

5. **Establish dependencies for ordered work**

### Pattern 9: Agent Task Updates

As Claude Code works on tasks:

```bash
# Start a task when beginning work
task 51 start

# Annotate with progress notes
task 51 annotate "Created ThemeContext with light/dark modes"
task 51 annotate "Added useTheme hook for components"

# If blocked, mark it
task 51 modify +blocked
task 51 annotate "Blocked: Need design team to provide dark mode colors"

# Complete when done
task 51 done
```

### Pattern 10: Agent Task Queries

Claude Code should regularly query tasks to understand context:

```bash
# What am I working on?
task +ACTIVE list

# What's next in this project?
task project:myapp status:pending -BLOCKED next

# What's blocking progress?
task +BLOCKED list

# What did I complete today?
task project:myapp completed today

# Show me the breakdown of a project
task project:myapp list
task project:myapp info
```

## Advanced Patterns

### Pattern 11: Multi-Project Coordination

```bash
# Create related projects with namespace hierarchy
task add project:company.frontend "Frontend application" +project
task add project:company.backend "Backend API" +project
task add project:company.infrastructure "DevOps and infrastructure" +project

# Create tasks that span projects
task add project:company.backend "API endpoint for user profiles"
task add project:company.frontend "User profile UI component" depends:BACKEND_TASK_ID
```

### Pattern 12: Recurring Tasks

```bash
# Weekly code review
task add "Review pull requests" recur:weekly due:friday priority:M +review

# Daily standups
task add "Daily standup notes" recur:daily due:10am +meeting

# Monthly dependency updates
task add "Update npm dependencies" recur:monthly due:1st priority:L +maintenance
```

### Pattern 13: Custom Reports

Add to `.taskrc`:

```
# Report: All parent tasks with their subtasks
report.parents.description=Parent tasks with pending subtasks
report.parents.columns=id,project,description,tags
report.parents.labels=ID,Project,Description,Tags
report.parents.filter=status:pending +parent

# Report: Quick wins
report.quick.description=Quick tasks (<30min)
report.quick.columns=id,priority,project,description
report.quick.labels=ID,Pri,Project,Description
report.quick.filter=status:pending +quick -BLOCKED
report.quick.sort=urgency-

# Report: Project overview
report.overview.description=Projects with task counts
report.overview.columns=project,count
report.overview.labels=Project,Tasks
report.overview.filter=status:pending
```

### Pattern 14: Time Estimation

```bash
# Add UDA for time estimates (add to .taskrc first)
# uda.estimate.type=duration
# uda.estimate.label=Estimate

# Estimate tasks
task 42 modify estimate:2h
task 43 modify estimate:30min
task 44 modify estimate:4h

# Query by estimate
task estimate.below:1h list
```

## Best Practices for Claude Code

### When Starting New Work

1. **Survey existing tasks**: `task project:NAME list`
2. **Check for parent task**: Create one if starting a new feature
3. **Break down immediately**: Don't create single large tasks
4. **Set dependencies**: Order work logically
5. **Tag appropriately**: Make tasks discoverable
6. **Set priorities**: What's urgent vs. important?

### While Working

1. **Start tasks**: `task ID start` - shows what's active
2. **Annotate progress**: Document decisions and findings
3. **Update if blocked**: Mark blockers immediately
4. **Complete atomically**: Finish fully before marking done
5. **Create follow-ups**: If new work discovered, create tasks

### When Blocked

1. **Mark as blocked**: `task ID modify +blocked`
2. **Annotate why**: What's needed to unblock?
3. **Create unblocking task**: If actionable
4. **Switch to next task**: Don't stay idle
5. **Review daily**: Check if blockers are resolved

### End of Session

1. **Complete finished tasks**: Don't leave done tasks unmarked
2. **Update in-progress**: Annotate current state
3. **Review next session**: What's queued up?
4. **Sync external**: Run `bugwarrior-pull` if using GitHub integration

## Example Workflow: Building a Feature

```bash
# 1. Create parent task
task add project:myapp "Add real-time notifications" +feature +parent priority:H
# Returns ID 100

# 2. Break down into subtasks
task add project:myapp "Notifications - Research WebSocket vs SSE" depends:100 +research
task add project:myapp "Notifications - Design notification schema" depends:100 +backend
task add project:myapp "Notifications - Implement WebSocket server" depends:101,102 +backend
task add project:myapp "Notifications - Create notification component" depends:102 +frontend
task add project:myapp "Notifications - Add notification center UI" depends:104 +frontend
task add project:myapp "Notifications - Implement permission system" depends:102 +backend
task add project:myapp "Notifications - Write integration tests" depends:103,105,106 +test
task add project:myapp "Notifications - Update documentation" depends:107 +docs

# 3. Start with research
task 101 start

# 4. Document findings
task 101 annotate "WebSocket chosen - better for bidirectional, lower latency"
task 101 annotate "Using socket.io library for browser compatibility"
task 101 done

# 5. Continue through subtasks
task 102 start
# ... work on schema ...
task 102 done

# 6. Track overall progress
task project:myapp status:pending list
task 100 info  # Shows completion percentage based on dependencies

# 7. When all subtasks done, complete parent
task 100 done
```

## Measuring Success

Good task management has these indicators:

- **No task stays "in progress" for more than a day**
- **>80% of tasks have estimates or time annotations**
- **Blocked tasks have clear unblocking conditions**
- **Projects have clear parent tasks with subtasks**
- **Completed tasks have useful annotations for retrospectives**
- **Daily task completion rate is consistent**

## Integration with Claude Code Skills

The Claude Code skills in `.claude/skills/` implement these patterns:

- `task-add.md`: Intelligent task creation with auto-breakdown
- `task-list.md`: Context-aware task querying
- `task-project.md`: Project and subtask management
- `task-sync.md`: BugWarrior synchronization

These skills encode these patterns so Claude Code automatically follows best practices when managing tasks.

## Conclusion

TaskWarrior is powerful but requires discipline. By following these patterns—especially hierarchical decomposition—you ensure that:

1. No work gets lost or forgotten
2. Progress is visible and measurable
3. Complexity is managed through breakdown
4. Dependencies are explicit and tracked
5. Context is preserved through annotations

**Remember: If a task feels too big, it is. Break it down.**
