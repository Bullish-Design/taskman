---
description: Manage TaskWarrior projects and organize tasks into hierarchical subtasks. Use when the user wants to create projects, break down work, or reorganize task structures.
tags: [task-management, taskwarrior, projects, subtasks, organization]
---

# Project and Subtask Management Skill

You are helping the user organize work into projects and break down complex tasks into manageable subtasks. This is the MOST IMPORTANT skill for effective task management.

## Core Philosophy

**Every complex piece of work should be organized as:**
1. **Project** - A namespace/container (e.g., `project:myapp`)
2. **Parent Task** - The high-level goal (tagged with `+parent`)
3. **Subtasks** - Concrete, actionable steps (depend on parent)

This hierarchy makes work visible, trackable, and manageable.

## Project Creation

### Pattern 1: Starting a New Project

```bash
# 1. Create the project container task
task add project:myapp "Build MyApp - complete web application" +project priority:H

# This creates a task that represents the entire project
# Tag it with +project to distinguish it from regular parent tasks

# 2. Verify project exists
task projects

# 3. Create initial parent tasks for major areas
task add project:myapp "Authentication system" +parent +feature priority:H
task add project:myapp "Database design and setup" +parent priority:H
task add project:myapp "Frontend application" +parent +feature priority:M
task add project:myapp "API development" +parent +feature priority:H
task add project:myapp "Testing infrastructure" +parent +test priority:M
task add project:myapp "Deployment pipeline" +parent +devops priority:L
```

### Pattern 2: Using Project Namespaces

Organize related projects with namespaces:

```bash
# Company-wide organization
project:company                    # Top-level
project:company.frontend          # Frontend team
project:company.backend           # Backend team
project:company.infrastructure    # DevOps team

# Product organization
project:acme                      # Product name
project:acme.api                  # API service
project:acme.web                  # Web app
project:acme.mobile              # Mobile app

# Feature branches
project:myapp.v2                  # Version 2 features
project:myapp.experimental        # Experimental features
project:myapp.maintenance         # Ongoing maintenance
```

Example:
```bash
# Create namespaced projects
task add project:acme.api "REST API service" +project priority:H
task add project:acme.web "Web application" +project priority:H
task add project:acme.mobile "Mobile app" +project priority:M

# Add tasks to specific namespaces
task add project:acme.api "Implement user authentication endpoints" +backend
task add project:acme.web "Create login page" +frontend
```

## Subtask Creation and Management

### Pattern 3: Breaking Down a Task

When you have a task that's too large:

```bash
# Original task (ID 42) is too complex
task 42 modify +parent
task 42 modify "User authentication system (PARENT)"

# Create subtasks
task add project:myapp "Auth - Research authentication strategies" depends:42 +research
task add project:myapp "Auth - Set up passport.js" depends:42,43 +backend
task add project:myapp "Auth - Implement login endpoint" depends:42,44 +backend
task add project:myapp "Auth - Implement registration endpoint" depends:42,44 +backend
task add project:myapp "Auth - Add password hashing" depends:42,44 +backend
task add project:myapp "Auth - Create JWT token system" depends:42,45,46,47 +backend
task add project:myapp "Auth - Build login form" depends:42,48 +frontend
task add project:myapp "Auth - Add auth middleware" depends:42,48 +backend
task add project:myapp "Auth - Write integration tests" depends:42,49,50 +test
task add project:myapp "Auth - Update documentation" depends:42,51 +docs
```

### Pattern 4: Nested Subtasks (for very complex work)

```bash
# Level 1: Project
task add project:ecommerce "E-commerce platform" +project priority:H
# ID 100

# Level 2: Major components (parents)
task add project:ecommerce "Product catalog (PARENT)" depends:100 +parent +feature
# ID 101
task add project:ecommerce "Shopping cart (PARENT)" depends:100 +parent +feature
# ID 102
task add project:ecommerce "Payment processing (PARENT)" depends:100 +parent +feature
# ID 103

# Level 3: Subtasks for product catalog
task add project:ecommerce "Catalog - Database schema" depends:101 +backend
task add project:ecommerce "Catalog - API endpoints" depends:101,104 +backend
task add project:ecommerce "Catalog - Product listing UI" depends:101,105 +frontend
task add project:ecommerce "Catalog - Search functionality" depends:101,105 +backend

# Level 3: Subtasks for shopping cart
task add project:ecommerce "Cart - State management design" depends:102 +frontend
task add project:ecommerce "Cart - Add to cart functionality" depends:102,108 +frontend
task add project:ecommerce "Cart - Cart persistence" depends:102,108 +backend
task add project:ecommerce "Cart - Cart UI component" depends:102,109 +frontend

# Level 4: Breaking down complex subtasks (if needed)
task 107 modify +parent "Catalog - Search functionality (PARENT)"
task add project:ecommerce "Search - Set up Elasticsearch" depends:107 +backend
task add project:ecommerce "Search - Index products" depends:107,112 +backend
task add project:ecommerce "Search - Build search API" depends:107,113 +backend
task add project:ecommerce "Search - Create search UI" depends:107,114 +frontend
```

### Pattern 5: Managing Dependencies

```bash
# Linear dependency chain (must be done in order)
task add project:myapp "Step 1: Design" priority:H
# ID 50
task add project:myapp "Step 2: Implement" depends:50 priority:H
# ID 51
task add project:myapp "Step 3: Test" depends:51 priority:H
# ID 52
task add project:myapp "Step 4: Deploy" depends:52 priority:M

# Parallel work that converges
task add project:myapp "Backend API" priority:H
# ID 60
task add project:myapp "Frontend UI" priority:H
# ID 61
task add project:myapp "Integration testing" depends:60,61 priority:H
# Both 60 and 61 must be done before 62

# Unblocking tasks
task 75 modify depends:-70  # Remove dependency on task 70
task 75 modify depends:71   # Change to depend on 71 instead
```

## Project Management Commands

### View Project Structure

```bash
# List all projects
task projects

# See all tasks in a project
task project:myapp list

# See project hierarchy
task project:myapp +parent list

# View a specific parent and its children
task PARENT_ID info
task depends:PARENT_ID list

# See project statistics
task project:myapp stats
```

### Reorganize Projects

```bash
# Move task to different project
task 42 modify project:newproject

# Move multiple tasks
task project:oldproject +feature modify project:newproject

# Rename project (affects all tasks)
task project:oldname modify project:newname

# Delete all tasks in a project (use carefully!)
task project:abandoned delete
```

### Mark Project Milestones

```bash
# Add milestone tasks
task add project:myapp "Milestone: MVP Complete" +milestone due:2026-03-01 priority:H

# Link tasks to milestone
task project:myapp +feature modify depends:MILESTONE_ID
```

## Workflow Patterns

### Pattern 6: Starting a New Feature

```bash
# 1. Create parent task
task add project:myapp "Dark mode support" +feature +parent priority:M
# Returns ID 80

# 2. Brainstorm subtasks (break down completely)
task add project:myapp "Dark mode - Research CSS variable approach" depends:80 +research
task add project:myapp "Dark mode - Add theme context provider" depends:80,81 +frontend
task add project:myapp "Dark mode - Create dark theme variables" depends:80,81 +frontend
task add project:myapp "Dark mode - Update all components" depends:80,82,83 +frontend
task add project:myapp "Dark mode - Add toggle component" depends:80,82 +frontend
task add project:myapp "Dark mode - Persist preference" depends:80,85 +frontend
task add project:myapp "Dark mode - Test in all browsers" depends:80,84,86 +test

# 3. Start with first task
task 81 start

# 4. Track progress
task 80 info  # Shows completion percentage
task project:myapp +feature list
```

### Pattern 7: Responding to a Bug Report

```bash
# For simple bugs, no parent needed
task add project:myapp "Fix button alignment on mobile" +bug +quick +frontend priority:H

# For complex bugs, use parent task
task add project:myapp "Fix data corruption issue (PARENT)" +bug +parent priority:H
# ID 90
task add project:myapp "Bug - Reproduce issue locally" depends:90 +research
task add project:myapp "Bug - Identify root cause" depends:90,91 +backend
task add project:myapp "Bug - Implement fix" depends:90,92 +backend
task add project:myapp "Bug - Add regression test" depends:90,93 +test
task add project:myapp "Bug - Verify fix in staging" depends:90,94 +test
task add project:myapp "Bug - Document issue and solution" depends:90,95 +docs
```

### Pattern 8: Planning a Sprint

```bash
# Create sprint project
task add project:sprint.2026-01 "Sprint January 2026" +sprint due:2026-01-31

# Pull high-priority items into sprint
task project:myapp priority:H next limit:10

# For each item, add to sprint project
task 42 modify project:sprint.2026-01.myapp

# Or use tags
task project:myapp priority:H modify +sprint202601
```

### Pattern 9: Refactoring Workflow

```bash
# 1. Create refactoring parent
task add project:myapp "Refactor authentication module" +refactor +parent priority:M
# ID 100

# 2. Break down by strategy
task add project:myapp "Refactor - Audit current code" depends:100 +research
task add project:myapp "Refactor - Write tests for current behavior" depends:100,101 +test
task add project:myapp "Refactor - Extract service layer" depends:100,102 +backend
task add project:myapp "Refactor - Update tests" depends:100,103 +test
task add project:myapp "Refactor - Update documentation" depends:100,104 +docs

# 3. Ensure no functionality is lost
task 102 annotate "Must maintain backward compatibility"
```

## Advanced Techniques

### Pattern 10: Critical Path Analysis

```bash
# Find tasks blocking others
task +BLOCKING list

# Find the longest dependency chain
task PARENT_ID info
# Look at dependency depth

# Prioritize blocking tasks
task +BLOCKING modify priority:H
```

### Pattern 11: Parallel Work Streams

```bash
# Create independent work streams
task add project:myapp "Backend API development (PARENT)" +parent +backend
# ID 200
task add project:myapp "Frontend UI development (PARENT)" +parent +frontend
# ID 201

# These can proceed in parallel
task add project:myapp "API - User endpoints" depends:200 +backend
task add project:myapp "API - Product endpoints" depends:200 +backend
task add project:myapp "UI - User components" depends:201 +frontend
task add project:myapp "UI - Product components" depends:201 +frontend

# Create integration task that needs both
task add project:myapp "Integration testing" depends:200,201 +test
```

### Pattern 12: Tracking Blocked Work

```bash
# Mark task as blocked
task 42 modify +blocked
task 42 annotate "Blocked: Waiting for API design approval"

# Create unblocking task
task add project:myapp "Get API design approval" priority:H +urgent
# ID 150

# Link them
task 42 modify depends:150

# When 150 is done, 42 automatically becomes unblocked
```

## Subtask Best Practices

### Guidelines for Good Subtasks

A subtask should be:
1. **Concrete**: "Implement login endpoint" not "Work on auth"
2. **Testable**: Clear definition of "done"
3. **Time-bound**: Completable in <2 hours
4. **Independent**: Minimal dependencies on other subtasks
5. **Tagged**: Proper tags for filtering and organization

### Bad vs Good Subtask Breakdown

❌ **Bad** (too vague):
```bash
task add project:myapp "Do frontend stuff" depends:42
task add project:myapp "Backend work" depends:42
task add project:myapp "Testing" depends:42
```

✅ **Good** (specific and actionable):
```bash
task add project:myapp "Create React component for user profile" depends:42 +frontend
task add project:myapp "Implement GET /api/users/:id endpoint" depends:42 +backend
task add project:myapp "Write unit tests for user profile component" depends:42 +test +frontend
task add project:myapp "Write integration test for user API" depends:42 +test +backend
```

### How Many Subtasks?

- **Simple task**: 0 subtasks (just do it)
- **Medium task**: 3-5 subtasks
- **Complex task**: 5-10 subtasks
- **Very complex**: 10+ subtasks, possibly nested

**If you have >10 subtasks at one level, consider grouping them into intermediate parent tasks.**

## Completion Workflow

### Completing Subtasks

```bash
# Start working on a subtask
task 43 start

# Complete it
task 43 done

# TaskWarrior automatically updates parent task progress
task PARENT_ID info  # Shows how many children are complete

# When all subtasks done, complete parent
task PARENT_ID done
```

### Handling Incomplete Work

```bash
# If a subtask won't be done
task 43 delete
task 43 modify "Won't implement - decided against this approach"
task 43 done

# Add new subtasks if scope changes
task add project:myapp "New subtask discovered during work" depends:PARENT_ID
```

## Common Scenarios

### Scenario: Breaking Down a GitHub Issue

```bash
# Issue: "Add user profile page"
# This is feature work, so create parent + subtasks

task add project:myapp "User profile page (GitHub #123)" +feature +parent priority:H
# ID 200

task add project:myapp "Profile - Design UI mockup" depends:200 +design
task add project:myapp "Profile - Create database fields" depends:200,201 +backend
task add project:myapp "Profile - Build API endpoints" depends:200,202 +backend
task add project:myapp "Profile - Create React component" depends:200,201 +frontend
task add project:myapp "Profile - Add avatar upload" depends:200,204 +frontend
task add project:myapp "Profile - Implement edit mode" depends:200,204 +frontend
task add project:myapp "Profile - Write tests" depends:200,203,206 +test
```

### Scenario: Multi-Phase Project

```bash
# Phase 1: Research and Planning
task add project:newapp "Phase 1: Research & Planning (PARENT)" +parent +phase1 priority:H
# ID 300
task add project:newapp "Research tech stack" depends:300 +research
task add project:newapp "Design architecture" depends:300,301 +design
task add project:newapp "Create project plan" depends:300,302 +planning

# Phase 2: Development (depends on phase 1 completion)
task add project:newapp "Phase 2: Development (PARENT)" +parent +phase2 depends:300 priority:H
# ID 304
# ... add development subtasks

# Phase 3: Testing and Launch (depends on phase 2)
task add project:newapp "Phase 3: Testing & Launch (PARENT)" +parent +phase3 depends:304 priority:H
```

## Remember

1. **Always create a parent task for features/bugs that need >1 step**
2. **Break down tasks immediately** - don't create large tasks and "break them down later"
3. **Use consistent project namespaces** - helps with filtering and organization
4. **Tag parent tasks with +parent** - makes them easy to find
5. **All subtasks should depend on their parent** - creates the hierarchy
6. **Use specific, actionable descriptions** - no vague subtasks
7. **Establish dependencies** - order work logically
8. **Review project structure regularly** - `task project:X +parent list`

The goal: **Every complex piece of work should have a clear, hierarchical breakdown that makes progress visible and success achievable.**
