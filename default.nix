{
  system ? builtins.currentSystem,
  sources ? import ./lon.nix,
  pkgs ? import sources.nixpkgs { inherit system; },
}:
let
  lib = pkgs.lib;
in
{
  packages.brr = pkgs.callPackage ./package.nix { };

  checks = lib.recurseIntoAttrs {
    pre-commit = import ./nix/pre-commit.nix;
  };
}
