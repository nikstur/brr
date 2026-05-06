let
  sources = import ./lon.nix;
  pkgs = import sources.nixpkgs { };
in
pkgs.mkShell {
  packages = [
    pkgs.nixfmt
    pkgs.lon
    pkgs.ruff
    pkgs.ty
  ];

  inputsFrom = [
    (import ./default.nix { }).packages.brr
  ];

  shellHook = ''
    ${(import ./pre-commit.nix { inherit pkgs; }).shellHook}
  '';
}
