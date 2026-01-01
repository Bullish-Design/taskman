{
  description = "TaskWarrior + BugWarrior NixOS Flake for integrated task management with GitHub issues";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
        };

        # Custom wrapper script for taskwarrior with helpful aliases
        taskWrapper = pkgs.writeShellScriptBin "tw" ''
          # TaskWarrior wrapper with common operations
          case "$1" in
            init)
              echo "Initializing TaskWarrior..."
              ${pkgs.taskwarrior}/bin/task rc.confirmation=off rc.verbose=nothing version
              echo "TaskWarrior initialized successfully!"
              ;;
            sync)
              echo "Syncing with BugWarrior..."
              ${pkgs.bugwarrior}/bin/bugwarrior-pull
              echo "Sync complete!"
              ;;
            *)
              ${pkgs.taskwarrior}/bin/task "$@"
              ;;
          esac
        '';

        # Helper script for project management
        projectHelper = pkgs.writeShellScriptBin "task-project" ''
          #!/usr/bin/env bash

          case "$1" in
            create)
              shift
              PROJECT="$1"
              shift
              DESCRIPTION="$@"
              echo "Creating project: $PROJECT"
              ${pkgs.taskwarrior}/bin/task add project:"$PROJECT" "$DESCRIPTION" +project
              ;;
            list)
              echo "Available projects:"
              ${pkgs.taskwarrior}/bin/task projects
              ;;
            tasks)
              shift
              PROJECT="$1"
              echo "Tasks in project: $PROJECT"
              ${pkgs.taskwarrior}/bin/task project:"$PROJECT" list
              ;;
            *)
              echo "Usage: task-project {create|list|tasks} [args]"
              echo "  create <project> <description> - Create a new project"
              echo "  list - List all projects"
              echo "  tasks <project> - List tasks in a project"
              ;;
          esac
        '';

      in
      {
        packages = {
          default = pkgs.buildEnv {
            name = "taskman-env";
            paths = [
              pkgs.taskwarrior
              pkgs.bugwarrior
              taskWrapper
              projectHelper
            ];
          };
        };

        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.taskwarrior
            pkgs.bugwarrior
            pkgs.tasksh         # Interactive shell for taskwarrior
            pkgs.timewarrior    # Time tracking companion
            taskWrapper
            projectHelper

            # Useful tools for integration
            pkgs.jq             # JSON processing
            pkgs.git            # Version control
            pkgs.gh             # GitHub CLI
          ];

          shellHook = ''
            # Set up taskwarrior data directory
            export TASKDATA="''${TASKDATA:-$PWD/.task}"
            export TASKRC="''${TASKRC:-$PWD/.taskrc}"

            # Create directories if they don't exist
            mkdir -p "$TASKDATA"

            # Initialize taskrc if it doesn't exist
            if [ ! -f "$TASKRC" ]; then
              echo "# TaskWarrior Configuration" > "$TASKRC"
              echo "data.location=$TASKDATA" >> "$TASKRC"
              echo "" >> "$TASKRC"
              echo "# Default command (what to show when you run 'task')" >> "$TASKRC"
              echo "default.command=next" >> "$TASKRC"
              echo "" >> "$TASKRC"
              echo "# UDA (User Defined Attributes) for better organization" >> "$TASKRC"
              echo "uda.priority.values=H,M,L," >> "$TASKRC"
              echo "" >> "$TASKRC"
              echo "# Report definitions for better visibility" >> "$TASKRC"
              echo "report.next.columns=id,start.age,entry.age,depends,priority,project,tags,recur,scheduled.countdown,due.relative,until.remaining,description.count,urgency" >> "$TASKRC"
              echo "report.next.labels=ID,Active,Age,Deps,P,Project,Tag,Recur,S,Due,Until,Description,Urg" >> "$TASKRC"
              echo "" >> "$TASKRC"
              echo "# Color theme" >> "$TASKRC"
              echo "include ${pkgs.taskwarrior}/share/doc/task/rc/dark-256.theme" >> "$TASKRC"
              echo "" >> "$TASKRC"
              echo "# BugWarrior integration" >> "$TASKRC"
              echo "uda.githubtitle.type=string" >> "$TASKRC"
              echo "uda.githubtitle.label=Github Title" >> "$TASKRC"
              echo "uda.githuburl.type=string" >> "$TASKRC"
              echo "uda.githuburl.label=Github URL" >> "$TASKRC"
              echo "uda.githubnumber.type=numeric" >> "$TASKRC"
              echo "uda.githubnumber.label=Github Issue #" >> "$TASKRC"
              echo "uda.githubrepo.type=string" >> "$TASKRC"
              echo "uda.githubrepo.label=Github Repo" >> "$TASKRC"

              echo "TaskRC initialized at $TASKRC"
            fi

            # Create bugwarrior config if it doesn't exist
            if [ ! -f "$PWD/.bugwarriorrc" ]; then
              cat > "$PWD/.bugwarriorrc" << 'EOF'
[general]
targets = github
shorten = True
inline_links = False
annotation_links = True
log.level = INFO

[github]
service = github
# Set your GitHub personal access token:
# github.token = YOUR_GITHUB_TOKEN
# Or use GitHub CLI authentication:
github.login = YOUR_GITHUB_USERNAME
github.username = YOUR_GITHUB_USERNAME

# Import issues assigned to you
github.include_user_repos = True
github.include_user_issues = True

# Project prefixes
github.project_template = {{githubrepo}}

# Add custom fields
github.add_tags = github
EOF
              echo "BugWarrior config template created at $PWD/.bugwarriorrc"
              echo "Please edit it with your GitHub credentials!"
            fi

            echo ""
            echo "TaskMan Development Environment"
            echo "================================"
            echo "TaskWarrior: $(task --version)"
            echo "BugWarrior:  $(bugwarrior-pull --version)"
            echo ""
            echo "Data directory: $TASKDATA"
            echo "Config file:    $TASKRC"
            echo ""
            echo "Quick commands:"
            echo "  task add <description>        - Add a new task"
            echo "  task list                     - List all tasks"
            echo "  task next                     - Show next tasks to work on"
            echo "  task-project create <name>    - Create a project"
            echo "  bugwarrior-pull               - Sync GitHub issues"
            echo "  tw sync                       - Quick sync command"
            echo ""
            echo "See AGENTS.md for detailed patterns and best practices!"
            echo ""
          '';
        };

        # NixOS module for system-wide installation
        nixosModules.taskman = { config, lib, pkgs, ... }:
          with lib;
          let
            cfg = config.services.taskman;
          in {
            options.services.taskman = {
              enable = mkEnableOption "TaskMan - TaskWarrior + BugWarrior integration";

              dataDir = mkOption {
                type = types.str;
                default = "/var/lib/taskwarrior";
                description = "Directory for TaskWarrior data";
              };

              user = mkOption {
                type = types.str;
                default = "taskwarrior";
                description = "User to run TaskWarrior as";
              };

              bugwarriorSync = mkOption {
                type = types.bool;
                default = false;
                description = "Enable automatic BugWarrior syncing";
              };

              syncInterval = mkOption {
                type = types.str;
                default = "hourly";
                description = "How often to sync with BugWarrior";
              };
            };

            config = mkIf cfg.enable {
              environment.systemPackages = [
                pkgs.taskwarrior
                pkgs.bugwarrior
                taskWrapper
                projectHelper
              ];

              users.users.${cfg.user} = {
                isSystemUser = true;
                home = cfg.dataDir;
                createHome = true;
                group = cfg.user;
              };

              users.groups.${cfg.user} = {};

              systemd.services.bugwarrior-sync = mkIf cfg.bugwarriorSync {
                description = "BugWarrior GitHub sync";
                serviceConfig = {
                  Type = "oneshot";
                  User = cfg.user;
                  ExecStart = "${pkgs.bugwarrior}/bin/bugwarrior-pull";
                };
              };

              systemd.timers.bugwarrior-sync = mkIf cfg.bugwarriorSync {
                wantedBy = [ "timers.target" ];
                timerConfig = {
                  OnCalendar = cfg.syncInterval;
                  Persistent = true;
                };
              };
            };
          };
      }
    );
}
