# flake.nix
{
  description = "TaskMan - Python CLI wrapper for TaskWarrior";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix.url = "github:pyproject-nix/uv2nix";
    pyproject-build-systems.url = "github:pyproject-nix/build-system-pkgs";
  };

  outputs = { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
    in {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python313;
          
          workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
          overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
          
          pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
            inherit python;
          }).overrideScope (pkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]);

          taskman-env = pythonSet.mkVirtualEnv "taskman-env" workspace.deps.default;
          
          taskman-full = pkgs.buildEnv {
            name = "taskman";
            paths = [
              taskman-env
              pkgs.taskwarrior3
              pkgs.vit
              pkgs.tasksh
            ];
          };
        in {
          default = taskman-full;
          taskman = taskman-full;
          taskman-python = taskman-env;
        }
      );

      nixosModules.taskman = { config, lib, pkgs, ... }:
        with lib;
        let
          cfg = config.services.taskman;
        in {
          options.services.taskman = {
            enable = mkEnableOption "TaskMan CLI wrapper";
          };

          config = mkIf cfg.enable {
            environment.systemPackages = [ self.packages.${pkgs.system}.default ];
          };
        };
    };
}

