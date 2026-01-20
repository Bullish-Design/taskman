# TaskMan: TaskWarrior + BugWarrior + Claude Code Integration

A complete NixOS flake for integrated task management using TaskWarrior, BugWarrior, and Claude Code skills. Focus on hierarchical task decomposition and project organization.

## Overview

TaskMan provides:
- **TaskWarrior**: Powerful command-line task management
- **BugWarrior**: Synchronization with GitHub issues, PRs, and other external services
- **Claude Code Skills**: AI-assisted task breakdown and management
- **NixOS Flake**: Reproducible development environment
- **Agent Patterns**: Best practices for hierarchical task decomposition

## Philosophy

The core principle is **hierarchical decomposition**: every complex task should be broken down into manageable subtasks. This makes work:
- **Visible**: See exactly what needs to be done
- **Trackable**: Monitor progress at every level
- **Manageable**: Work on concrete, achievable steps
- **Completable**: Regular wins from finishing subtasks

## Quick Start

### Using Nix Flakes

```bash
# Clone the repository
git clone <your-repo-url> taskman
cd taskman

# Enter the development shell
nix develop

# TaskWarrior is now configured and ready!
task add "My first task" priority:H
task list
```

### Manual Installation

If not using Nix:

```bash
# Install TaskWarrior and BugWarrior
# On macOS:
brew install task bugwarrior

# On Ubuntu/Debian:
apt-get install taskwarrior python3-bugwarrior

# On Arch:
pacman -S task bugwarrior
```

## Features

### 1. TaskWarrior Configuration

Pre-configured `.taskrc` with:
- User Defined Attributes (UDAs) for GitHub integration
- Custom reports (next, parents, quick wins)
- Dark theme for better readability
- Sensible defaults for productivity

### 2. BugWarrior Integration

Automatically sync with:
- GitHub issues and pull requests
- GitLab issues
- Jira tickets
- Bugzilla bugs
- And many more services

### 3. Claude Code Skills

Located in `.claude/skills/`:
- `task-add.md`: Intelligent task creation with automatic breakdown
- `task-list.md`: Context-aware task querying and filtering
- `task-project.md`: Project and subtask hierarchy management
- `task-sync.md`: BugWarrior synchronization workflows

### 4. Helper Scripts

- `tw`: TaskWarrior wrapper with shortcuts
- `task-project`: Project management helper

## Setup Guide

### Step 1: Initialize TaskWarrior

```bash
# If using nix develop, this is automatic
# Otherwise, initialize manually:
task version
```

### Step 2: Configure BugWarrior (Optional)

Edit `.bugwarriorrc`:

```ini
[general]
targets = github

[github]
service = github
github.token = YOUR_GITHUB_PERSONAL_ACCESS_TOKEN
github.include_user_issues = True
github.add_tags = github
```

Get a GitHub token:
```bash
# Using GitHub CLI
gh auth token

# Or create one at: https://github.com/settings/tokens
# Scopes needed: repo, read:org
```

### Step 3: Configure Claude Code

Claude Code automatically detects skills in `.claude/skills/`. The skills are:

1. **task-add**: For creating and breaking down tasks
2. **task-list**: For querying and viewing tasks
3. **task-project**: For managing project hierarchies
4. **task-sync**: For GitHub integration via BugWarrior

Just tell Claude to help with tasks, and it will use these skills!

## Usage Examples

### Creating Tasks

```bash
# Simple task
task add "Fix login bug" +bug +backend priority:H

# Task with project
task add project:myapp "Implement user authentication" +feature priority:H

# Task with dependencies
task add "Write tests" depends:42 +test priority:M
```

### Breaking Down Complex Work

```bash
# Create parent task
task add project:myapp "Dark mode support" +feature +parent priority:M
# Returns ID 100

# Create subtasks
task add project:myapp "Dark mode - Research approach" depends:100 +research
task add project:myapp "Dark mode - Add theme context" depends:100,101 +frontend
task add project:myapp "Dark mode - Create CSS variables" depends:100,101 +frontend
task add project:myapp "Dark mode - Update components" depends:100,102,103 +frontend
task add project:myapp "Dark mode - Add toggle UI" depends:100,102 +frontend
task add project:myapp "Dark mode - Test browsers" depends:100,104,105 +test
```

### Viewing Tasks

```bash
# Next actions
task next

# All tasks in a project
task project:myapp list

# High priority tasks
task priority:H next

# What am I working on?
task +ACTIVE list

# What's blocked?
task +BLOCKED list

# Recent completions
task completed today
```

### Working with GitHub Issues

```bash
# Sync with GitHub
bugwarrior-pull

# View GitHub issues
task +github list

# View issues from specific repo
task project:gh.owner.repo list

# Break down a GitHub issue
task 150 modify +parent  # GitHub issue becomes parent
task add "Implement first part of issue" depends:150 +backend
task add "Write tests for issue" depends:150,151 +test
```

### Using Claude Code

In Claude Code, just ask:

```
"Help me create tasks for implementing user authentication"
"Show me what I should work on next in the myapp project"
"Break down this GitHub issue into subtasks"
"What's blocking progress on the frontend project?"
```

Claude will use the skills to intelligently manage your tasks!

## Task Organization Best Practices

### Project Structure

```
project:myapp                      # Main project
  └── +project task                # Project container
      └── +parent +feature         # Feature parent
          └── subtask 1            # Concrete work
          └── subtask 2            # Concrete work
              └── sub-subtask 2.1  # If needed
```

### Task Granularity

A good task:
- Can be completed in **< 2 hours**
- Has a **clear definition of done**
- Is **self-contained** or has clear dependencies
- Has **specific, actionable description**

**If a task doesn't meet these criteria, break it down!**

### Using Tags

```bash
# Type tags
+feature      # New functionality
+bug          # Bug fix
+refactor     # Code improvement
+test         # Testing
+docs         # Documentation

# Status tags
+parent       # Parent task with subtasks
+blocked      # Waiting on something
+quick        # Can be done in <30 min

# Domain tags
+frontend     # UI/client work
+backend      # Server/API work
+database     # Database work
+devops       # Infrastructure
```

### Dependencies

```bash
# Linear chain: A → B → C
task add "Design" priority:H
# ID 10
task add "Implement" depends:10
# ID 11
task add "Test" depends:11

# Parallel work converging: A + B → C
task add "Backend API"  # ID 20
task add "Frontend UI"  # ID 21
task add "Integration test" depends:20,21  # Needs both
```

## Advanced Features

### Custom Reports

Already configured in `.taskrc`:

```bash
task parents   # All parent tasks
task quick     # Quick wins (<30 min)
task blocked   # Blocked tasks with dependencies
```

### Time Tracking

```bash
# Start working on a task
task 42 start

# TaskWarrior tracks active time
task +ACTIVE list

# Stop (mark as done)
task 42 done
```

### Recurring Tasks

```bash
# Weekly code review
task add "Review PRs" recur:weekly due:friday +review

# Daily standup
task add "Standup notes" recur:daily due:10am +meeting
```

### Annotations

```bash
# Add notes to tasks
task 42 annotate "Found issue with database connection"
task 42 annotate "Fixed by updating pool size to 20"

# View task with annotations
task 42 info
```

### Syncing with Multiple Services

Edit `.bugwarriorrc`:

```ini
[general]
targets = github, gitlab

[github]
service = github
github.token = YOUR_TOKEN

[gitlab]
service = gitlab
gitlab.token = YOUR_TOKEN
gitlab.host = gitlab.com
```

## NixOS Module

For system-wide installation:

```nix
# In your NixOS configuration
{
  imports = [ ./taskman/flake.nix ];

  services.taskman = {
    enable = true;
    user = "youruser";
    bugwarriorSync = true;
    syncInterval = "hourly";
  };
}
```

## File Structure

```
taskman/
├── flake.nix              # Nix flake definition
├── flake.lock             # Locked dependencies
├── README.md              # This file
├── AGENTS.md              # Detailed agent patterns
├── .taskrc                # TaskWarrior configuration (auto-generated)
├── .bugwarriorrc          # BugWarrior configuration (template)
├── .task/                 # TaskWarrior data directory
└── .claude/
    └── skills/
        ├── task-add.md      # Task creation skill
        ├── task-list.md     # Task querying skill
        ├── task-project.md  # Project management skill
        └── task-sync.md     # BugWarrior sync skill
```

## Documentation

- **AGENTS.md**: Comprehensive patterns for AI agents working with tasks
  - Hierarchical decomposition strategies
  - Project organization patterns
  - Best practices for task breakdown
  - Integration workflows

- **Skills**: Claude Code skills for intelligent task management
  - Automatic task breakdown
  - Context-aware querying
  - Project hierarchy management
  - External system synchronization

## Tips and Tricks

### Morning Routine

```bash
# 1. Sync with GitHub
bugwarrior-pull

# 2. Review what's next
task next

# 3. Check blocked items
task +BLOCKED list

# 4. Start your day
task CHOSEN_ID start
```

### End of Day Review

```bash
# What did I accomplish?
task completed today

# What's still in progress?
task +ACTIVE list

# What's next tomorrow?
task project:myapp next limit:5
```

### Context Switching

```bash
# Pause current project
task project:oldproject +ACTIVE modify +paused

# Switch to new project
task project:newproject next
task NEW_ID start
```

### Finding Tasks

```bash
# Search descriptions
task /authentication/ list

# Combine filters
task +bug +backend priority:H -BLOCKED next

# By date
task entry.after:today-7days list
task due.before:today+7days list
```

## Troubleshooting

### TaskWarrior not initialized

```bash
task version  # This initializes TaskWarrior
```

### BugWarrior sync fails

```bash
# Test configuration
bugwarrior-pull --dry-run

# Verbose logging
bugwarrior-pull --log-level DEBUG
```

### Tasks not showing up

```bash
# Check task status
task ID info

# List all tasks including completed
task all

# Check filters
task rc.verbose=yes next
```

## Contributing

Contributions welcome! Areas for improvement:
- Additional BugWarrior service configurations
- Custom TaskWarrior reports
- More Claude Code skills
- Integration with other tools

## Resources

- [TaskWarrior Documentation](https://taskwarrior.org/docs/)
- [BugWarrior Documentation](https://bugwarrior.readthedocs.io/)
- [Claude Code Documentation](https://github.com/anthropics/claude-code)
- [Getting Things Done (GTD)](https://gettingthingsdone.com/)

## License

MIT License - See LICENSE file for details

## Credits

- TaskWarrior by [Taskwarrior Team](https://taskwarrior.org)
- BugWarrior by [Ralph Bean](https://github.com/ralphbean/bugwarrior)
- Claude Code by [Anthropic](https://www.anthropic.com)

---

**Remember: If a task feels too big, it is. Break it down!** 
