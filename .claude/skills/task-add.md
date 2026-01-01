---
description: Add tasks to TaskWarrior with intelligent breakdown into subtasks. Use when the user wants to create new tasks, especially complex ones that need decomposition.
tags: [task-management, taskwarrior, productivity]
---

# Task Addition Skill

You are helping the user add tasks to TaskWarrior. Follow these critical patterns:

## Core Principles

1. **Break down complex tasks automatically** - If a task will take more than 2 hours, break it into subtasks
2. **Use projects consistently** - Always assign tasks to projects
3. **Set priorities appropriately** - H (urgent/important), M (normal), L (low priority)
4. **Tag meaningfully** - Use tags like +bug, +feature, +refactor, +test, +docs
5. **Establish dependencies** - Order work logically with depends:

## Workflow

### Step 1: Understand the Task

Ask clarifying questions if needed:
- What project does this belong to?
- Is this a bug fix, feature, refactor, or something else?
- Are there dependencies on other work?
- What's the priority/urgency?

### Step 2: Determine Complexity

Evaluate if the task needs breakdown:
- **Simple task** (< 2 hours): Create single task
- **Medium task** (2-8 hours): Create parent + 3-5 subtasks
- **Complex task** (> 8 hours): Create parent + 5-10 subtasks, possibly nested

### Step 3: Check Existing Tasks

Before creating tasks, always check what exists:

```bash
# List tasks in the project
task project:PROJECTNAME list

# Search for related tasks
task /KEYWORD/ list
```

### Step 4: Create Tasks

#### For Simple Tasks:

```bash
task add project:PROJECTNAME "Task description" +tag priority:M
```

#### For Complex Tasks (PREFERRED APPROACH):

```bash
# 1. Create parent task
task add project:PROJECTNAME "High-level goal (PARENT)" +parent +feature priority:H

# Get the ID of the created task (let's say it's 42)

# 2. Create subtasks with clear, actionable descriptions
task add project:PROJECTNAME "Subtask 1: Specific action" depends:42 +tag
task add project:PROJECTNAME "Subtask 2: Specific action" depends:42 +tag
task add project:PROJECTNAME "Subtask 3: Specific action" depends:42,43 +tag
# Note: Subtask 3 depends on both parent (42) and previous subtask (43)

# 3. Add estimates if possible (requires UDA setup)
task 43 modify estimate:1h
task 44 modify estimate:2h
```

### Step 5: Verify Creation

```bash
# Show the created tasks
task project:PROJECTNAME newest

# Show parent task with dependencies
task ID info
```

## Examples

### Example 1: Simple Bug Fix

```bash
task add project:myapp "Fix login button alignment on mobile" +bug +quick +frontend priority:H
```

### Example 2: Medium Feature (with breakdown)

User request: "Add user profile page"

```bash
# Create parent
task add project:myapp "User profile page" +feature +parent priority:M
# Returns ID 100

# Create subtasks
task add project:myapp "Profile - Design data model and API" depends:100 +backend
task add project:myapp "Profile - Create API endpoints" depends:100,101 +backend
task add project:myapp "Profile - Build profile component" depends:101 +frontend
task add project:myapp "Profile - Add avatar upload" depends:103 +frontend
task add project:myapp "Profile - Write tests" depends:102,103,104 +test
```

### Example 3: Complex Feature (nested breakdown)

User request: "Implement payment processing"

```bash
# Create top-level parent
task add project:myapp "Payment processing system" +feature +parent priority:H
# ID 200

# Create major subtasks (which are also parents)
task add project:myapp "Payment - Backend integration (PARENT)" depends:200 +parent +backend
# ID 201
task add project:myapp "Payment - Frontend UI (PARENT)" depends:200 +parent +frontend
# ID 202
task add project:myapp "Payment - Testing & Security (PARENT)" depends:200 +parent +test
# ID 203

# Break down backend integration
task add project:myapp "Payment - Research Stripe vs PayPal APIs" depends:201 +research
task add project:myapp "Payment - Set up Stripe account and keys" depends:201,204 +backend
task add project:myapp "Payment - Implement payment intent creation" depends:201,205 +backend
task add project:myapp "Payment - Add webhook handlers" depends:201,206 +backend
task add project:myapp "Payment - Create payment records in DB" depends:201,206 +backend

# Break down frontend UI
task add project:myapp "Payment - Design payment form UI" depends:202 +frontend
task add project:myapp "Payment - Implement Stripe Elements" depends:202,209 +frontend
task add project:myapp "Payment - Add payment confirmation page" depends:202,210 +frontend
task add project:myapp "Payment - Handle error states" depends:202,210 +frontend

# Break down testing
task add project:myapp "Payment - Write unit tests for backend" depends:203,208 +test
task add project:myapp "Payment - Write E2E tests" depends:203,211 +test
task add project:myapp "Payment - Security audit of payment flow" depends:203,213,214 +security
task add project:myapp "Payment - Load testing" depends:203,215 +test
```

## Smart Breakdown Heuristics

When deciding how to break down a task, consider:

### By Implementation Phases
- Research/Design
- Backend/API
- Frontend/UI
- Testing
- Documentation
- Deployment

### By Components
- Database schema
- API endpoints
- Business logic
- UI components
- Integration points

### By User Stories
- "As a user, I want to..."
- Each user story becomes a subtask

### By Technical Steps
- Set up dependencies
- Implement core functionality
- Add error handling
- Write tests
- Optimize performance

## Tags to Use

```
# Type tags
+feature      - New functionality
+bug          - Bug fix
+refactor     - Code improvement
+docs         - Documentation
+test         - Testing
+security     - Security-related
+performance  - Performance optimization

# Status tags
+parent       - Parent task with subtasks
+blocked      - Waiting on something
+review       - Ready for code review
+quick        - < 30 minutes
+research     - Research/investigation

# Domain tags
+frontend     - UI/client work
+backend      - Server/API work
+database     - Database work
+devops       - Infrastructure
+design       - Design work
```

## Common Patterns

### Pattern: User Story → Tasks

User story: "As a user, I want to reset my password"

```bash
task add project:myapp "Password reset feature" +feature +parent priority:H
# ID 50

task add project:myapp "Reset - Add 'forgot password' link to login" depends:50 +frontend
task add project:myapp "Reset - Create password reset request endpoint" depends:50 +backend
task add project:myapp "Reset - Generate and email reset tokens" depends:50,52 +backend
task add project:myapp "Reset - Create reset password form" depends:50 +frontend
task add project:myapp "Reset - Implement password update endpoint" depends:50 +backend
task add project:myapp "Reset - Add token expiration logic" depends:53,55 +backend
task add project:myapp "Reset - Write E2E test" depends:51,54,56 +test
```

### Pattern: Bug Report → Tasks

Bug: "Shopping cart loses items on refresh"

```bash
# For bugs, often don't need parent task unless investigation reveals complexity
task add project:ecommerce "Fix cart persistence on refresh" +bug +backend priority:H
# ID 60

# If investigation reveals it's complex:
task 60 modify +parent
task add project:ecommerce "Cart - Investigate root cause" depends:60 +research
task add project:ecommerce "Cart - Implement localStorage persistence" depends:60,61 +frontend
task add project:ecommerce "Cart - Add backend session sync" depends:60,61 +backend
task add project:ecommerce "Cart - Test across browsers" depends:62,63 +test
```

### Pattern: Refactoring → Tasks

Request: "Refactor authentication system"

```bash
task add project:myapp "Refactor authentication system" +refactor +parent priority:M
# ID 70

task add project:myapp "Auth - Audit current implementation" depends:70 +research
task add project:myapp "Auth - Extract auth logic to service layer" depends:70,71 +backend
task add project:myapp "Auth - Implement JWT refresh tokens" depends:70,72 +backend
task add project:myapp "Auth - Add proper error handling" depends:70,72 +backend
task add project:myapp "Auth - Update tests" depends:72,73,74 +test
task add project:myapp "Auth - Update documentation" depends:75 +docs
```

## Error Handling

If task creation fails:
1. Check if TaskWarrior is initialized: `task version`
2. Verify project exists: `task projects`
3. Check for malformed dependencies: `task ID info`
4. Ensure TASKRC and TASKDATA are set correctly

## After Creating Tasks

Always show the user:
1. **What was created**: `task newest limit:5`
2. **The structure**: `task project:PROJECTNAME list`
3. **Next steps**: What task should be started first?

## Remember

- **Always prefer creating subtasks over single large tasks**
- **Parent tasks should have +parent tag**
- **All subtasks should depend on their parent**
- **Use consistent project namespaces**
- **Set priorities to guide work order**
- **Tags make tasks discoverable later**

When in doubt, break it down more!
