{ pkgs }:

let
  sources = import ./lon.nix;
  pre-commit.run = pkgs.callPackage "${sources.pre-commit}/nix/run.nix" {
    inherit pkgs;
    tools = import "${sources.pre-commit}/nix/call-tools.nix" pkgs;
    # Trick pre-commit into not needing gitignore.nix
    isFlakes = true;
    gitignore-nix-src = { };
  };
in
pre-commit.run {
  src = pkgs.nix-gitignore.gitignoreSource [ ] ./.;

  hooks = {
    nixfmt = {
      enable = true;
    };
    ruff = {
      enable = true;
    };
    ruff-format = {
      enable = true;
    };
  };
}
