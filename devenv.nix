{ pkgs, lib, config, inputs, ... }:


let
  # Import the taskman Python package using uv2nix
  taskman = config.languages.python.import ./. { };
in
{
  # https://devenv.sh/basics/
  env.GREET = "TaskMan";

  # https://devenv.sh/packages/
  packages = with pkgs; [ 
    git 
    taskwarrior3
    vit
    tasksh
    taskman
  ];


  languages.python = {
    enable = true;
    version = "3.13";
    venv.enable = true;
    uv.enable = true;
  };

    # https://devenv.sh/processes/
  # processes.dev.exec = "${lib.getExe pkgs.watchexec} -n -- ls -la";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
    echo
  '';

  # https://devenv.sh/basics/
  enterShell = ''
    hello         # Run scripts directly
    git --version # Use packages
    echo
    task --version
    echo
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  outputs = {
    inherit taskman;
  };
  # See full reference at https://devenv.sh/reference/options/
}
