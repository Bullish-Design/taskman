---
description: Sync GitHub issues and external task sources with TaskWarrior using BugWarrior. Use when the user wants to import issues, synchronize with external systems, or manage integration with GitHub.
tags: [task-management, bugwarrior, github, integration, sync]
---

# BugWarrior Sync Skill

You are helping the user synchronize external task sources (primarily GitHub issues) with TaskWarrior using BugWarrior. This creates a unified task management system.

## Overview

BugWarrior pulls issues from external services (GitHub, GitLab, Jira, etc.) and creates TaskWarrior tasks. This allows you to:
- Manage GitHub issues alongside local tasks
- Track all work in one place
- Break down GitHub issues into local subtasks
- Keep work visible even when offline

## Initial Setup

### Step 1: Configure BugWarrior

Create or edit `.bugwarriorrc`:

```ini
[general]
targets = github
shorten = True
inline_links = False
annotation_links = True
log.level = INFO

# Where to store pulled data
annotation_comments = True
description_template = {{githubtitle}}

[github]
service = github

# Authentication - choose one method:

# Option 1: Personal Access Token (recommended)
github.token = YOUR_GITHUB_PERSONAL_ACCESS_TOKEN

# Option 2: GitHub CLI authentication
# github.login = YOUR_USERNAME
# github.username = YOUR_USERNAME

# What to import
github.include_user_repos = True
github.include_user_issues = True
github.involved_issues = True

# Only import certain repos (optional)
# github.include_repos = owner/repo1, owner/repo2

# Only import certain labels (optional)
# github.query = label:bug OR label:enhancement

# Project naming
github.project_template = gh.{{githubrepo}}

# Tags
github.add_tags = github
```

### Step 2: Set Up TaskWarrior UDAs

Add to `.taskrc` (User Defined Attributes for GitHub metadata):

```
# GitHub integration
uda.githubtitle.type=string
uda.githubtitle.label=Github Title
uda.githuburl.type=string
uda.githuburl.label=Github URL
uda.githubnumber.type=numeric
uda.githubnumber.label=Github Issue
uda.githubrepo.type=string
uda.githubrepo.label=Github Repo
uda.githubtype.type=string
uda.githubtype.label=Github Type
uda.githubstate.type=string
uda.githubstate.label=Github State
uda.githubuser.type=string
uda.githubuser.label=Github User
```

### Step 3: Create Personal Access Token

```bash
# Using GitHub CLI
gh auth login

# Or create token manually at:
# https://github.com/settings/tokens
# Scopes needed: repo, read:org, read:user
```

## Synchronization Workflow

### Basic Sync

```bash
# Pull latest issues from GitHub
bugwarrior-pull

# Or using the wrapper
tw sync
```

### What Happens During Sync

1. **BugWarrior queries GitHub** for issues matching your config
2. **Creates TaskWarrior tasks** for new issues
3. **Updates existing tasks** if issues changed
4. **Does NOT delete** tasks if issues are closed (you must do this manually)

### After First Sync

```bash
# View all GitHub issues
task +github list

# View by project (repository)
task project:gh.owner.repo list

# View open issues
task +github status:pending list

# View issues from specific repo
task githubrepo:owner/repo list
```

## Managing Imported Issues

### Pattern 1: Organizing GitHub Issues

After sync, organize imported issues:

```bash
# View all GitHub tasks
task +github list

# Add project context if needed
task +github modify project:myapp.github

# Set priorities based on labels
task +github githublabel:critical modify priority:H
task +github githublabel:bug modify priority:H

# Add local tags
task +github githubtype:bug modify +bug
task +github githubtype:enhancement modify +feature
```

### Pattern 2: Breaking Down GitHub Issues

GitHub issues often represent large work items. Break them down:

```bash
# Find the GitHub issue task (e.g., ID 150)
task +github /user authentication/ list

# Mark as parent
task 150 modify +parent

# Create local subtasks
task add project:myapp "Auth - Research OAuth providers" depends:150 +research
task add project:myapp "Auth - Implement OAuth flow" depends:150,151 +backend
task add project:myapp "Auth - Add login UI" depends:150,152 +frontend
task add project:myapp "Auth - Write tests" depends:150,153 +test

# Now you can track subtasks locally while issue stays synced with GitHub
```

### Pattern 3: Linking Local Work to GitHub Issues

```bash
# Create local tasks that reference GitHub issues
task add project:myapp "Fix bug from GitHub issue #123" githubnumber:123 +bug priority:H

# Link existing task to GitHub issue
task 42 modify githubnumber:456 githuburl:https://github.com/owner/repo/issues/456
```

### Pattern 4: Filtering GitHub vs Local Tasks

```bash
# Only local tasks (not from GitHub)
task -github status:pending list

# Only GitHub tasks
task +github list

# GitHub bugs
task +github +bug list

# Local features not in GitHub
task -github +feature list

# Mix: Local tasks for GitHub issue
task depends:GITHUB_TASK_ID list
```

## Sync Strategies

### Strategy 1: Selective Import

Only import specific repositories:

```ini
# In .bugwarriorrc
[github]
github.include_repos = myorg/important-repo, myorg/critical-repo
```

### Strategy 2: Label-Based Import

Only import issues with specific labels:

```ini
[github]
github.query = label:"needs-work" OR label:"in-progress"
```

### Strategy 3: Namespace by Repository

Keep GitHub issues separate from local work:

```ini
[github]
github.project_template = github.{{githubrepo}}
```

Then:
```bash
# GitHub issues for repo
task project:github.owner.repo list

# Local work for same repo
task project:myapp list
```

### Strategy 4: Regular Sync Schedule

```bash
# Add to crontab for automatic sync
0 */2 * * * cd /path/to/taskman && bugwarrior-pull

# Or using systemd timer (included in flake)
# Enable with: systemctl --user enable bugwarrior-sync.timer
```

## Handling Sync Issues

### Problem: Too Many Issues Imported

```bash
# Filter by date - only recent issues
task +github entry.after:today-7days list

# Delete old GitHub issues
task +github entry.before:today-30days delete

# Or modify config to limit imports
[github]
github.query = created:>2026-01-01
```

### Problem: Duplicate Tasks

```bash
# Find duplicates
task +github githubnumber:123 list

# BugWarrior uses UUIDs to prevent duplicates, but if you see them:
# Keep one, delete the other
task DUPLICATE_ID delete
```

### Problem: Closed Issues Still Showing

```bash
# BugWarrior doesn't auto-delete when issues close
# Find closed issues
task +github githubstate:closed list

# Complete them
task +github githubstate:closed done

# Or delete them
task +github githubstate:closed delete
```

### Problem: Sync Fails

```bash
# Check BugWarrior configuration
bugwarrior-pull --dry-run

# Verbose logging
bugwarrior-pull --log-level DEBUG

# Common issues:
# 1. Invalid GitHub token
# 2. Network connectivity
# 3. Malformed .bugwarriorrc
```

## Advanced Patterns

### Pattern 5: Multiple Service Integration

```ini
# .bugwarriorrc with multiple services
[general]
targets = github, gitlab, jira

[github]
service = github
github.token = YOUR_TOKEN
# ... github config

[gitlab]
service = gitlab
gitlab.token = YOUR_TOKEN
gitlab.host = gitlab.com
# ... gitlab config

[jira]
service = jira
jira.base_uri = https://your-company.atlassian.net
jira.username = you@company.com
jira.password = YOUR_PASSWORD
# ... jira config
```

Then:
```bash
# Sync all services
bugwarrior-pull

# View by service
task +github list
task +gitlab list
task +jira list
```

### Pattern 6: Custom Annotations

Add custom annotations during import:

```ini
[github]
github.add_tags = github, external
github.default_priority = M
annotation_comments = True
```

### Pattern 7: Pull Request Integration

```ini
[github]
github.include_user_issues = True
github.include_user_repos = True
github.include_pull_requests = True  # Also import PRs!

# PRs get tagged differently
# uda.githubtype will be "pull_request"
```

Then:
```bash
# View pull requests
task +github githubtype:pull_request list

# Your PRs to review
task +github githubtype:pull_request list
```

### Pattern 8: Team Workflows

For team-based work:

```ini
[github]
# Import issues from team repos
github.include_repos = team/frontend, team/backend, team/shared

# Only issues assigned to you or created by you
github.involved_issues = True

# Tag by team
github.add_tags = team, github
```

## Workflow Examples

### Example 1: Morning Sync Routine

```bash
# 1. Sync with GitHub
bugwarrior-pull

# 2. Review new issues
task +github entry.after:today list

# 3. Prioritize new issues
task +github entry.after:today githublabel:urgent modify priority:H

# 4. Break down complex issues
task +github entry.after:today +parent list
# For each parent, create subtasks

# 5. Plan your day
task next
```

### Example 2: Working on GitHub Issue

```bash
# 1. Find the issue
task +github /authentication bug/ list
# ID 200

# 2. Start working
task 200 start

# 3. Create local subtasks as you work
task add project:myapp "Fix auth validation logic" depends:200 +backend
task add project:myapp "Add test for auth fix" depends:200,201 +test

# 4. Complete subtasks
task 201 done
task 202 done

# 5. Complete the GitHub issue task
task 200 done

# Note: This doesn't close the GitHub issue!
# Close the issue on GitHub separately
```

### Example 3: End of Day Review

```bash
# What GitHub issues did I work on?
task +github completed today

# What local work did I complete?
task -github completed today

# What's still in progress?
task +github +ACTIVE list

# What's blocked?
task +github +BLOCKED list
```

## Best Practices

### 1. Use Namespaces

Keep GitHub issues separate from local work:
- GitHub issues: `project:github.repo`
- Local work: `project:myapp`
- Mixed: `project:myapp.github`

### 2. Break Down Imported Issues

Large GitHub issues should become parent tasks with local subtasks.

### 3. Don't Duplicate Work

If it's in GitHub, import it. Don't manually recreate it.

### 4. Sync Regularly

Run `bugwarrior-pull` at least daily, or automate it.

### 5. Clean Up Completed Issues

Periodically clean up closed GitHub issues:
```bash
task +github githubstate:closed done
```

### 6. Use Tags Effectively

- `+github` - Identifies GitHub-imported tasks
- `+external` - Any externally-sourced task
- Combine with local tags: `+github +bug +backend`

### 7. Link Don't Duplicate

When working on a GitHub issue, link your local tasks to it with dependencies rather than duplicating information.

### 8. Review Before Closing

Before closing a GitHub issue, ensure all local subtasks are done:
```bash
task depends:GITHUB_ISSUE_ID status:pending list
```

## Automation

### Automatic Sync (systemd)

The flake includes systemd timer configuration. Enable it:

```bash
# User-level timer
systemctl --user enable bugwarrior-sync.timer
systemctl --user start bugwarrior-sync.timer

# Check status
systemctl --user status bugwarrior-sync.timer
```

### Sync on Shell Startup

Add to your shell rc file:

```bash
# .bashrc or .zshrc
if [ -f .bugwarriorrc ]; then
    # Sync if last sync was >1 hour ago
    if [ ! -f .last-bugwarrior-sync ] || [ $(($(date +%s) - $(stat -f %m .last-bugwarrior-sync))) -gt 3600 ]; then
        bugwarrior-pull > /dev/null 2>&1 &
        touch .last-bugwarrior-sync
    fi
fi
```

## Troubleshooting

### Issue: "No service targets found"

Check `.bugwarriorrc` has `targets` defined:
```ini
[general]
targets = github
```

### Issue: "Authentication failed"

Verify GitHub token:
```bash
# Test token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

### Issue: "No issues imported"

Check your filters:
```ini
[github]
# Remove restrictive filters temporarily
# github.query =
github.include_user_issues = True
```

## Remember

- **BugWarrior imports external work into TaskWarrior**
- **Sync regularly** to keep data fresh
- **Break down imported issues** into actionable subtasks
- **Use namespaces** to separate external and local work
- **Tag consistently** for easy filtering
- **Don't rely on BugWarrior to close issues** - manage issue state in GitHub
- **Clean up periodically** to avoid task bloat

BugWarrior brings external work into your local task management system, giving you complete visibility and control over all your work!
