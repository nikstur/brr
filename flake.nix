{
  description = "Make your Nix builds go brr";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      eachSystem = nixpkgs.lib.genAttrs [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-darwin"
        "x86_64-linux"
      ];
    in
    {
      packages = eachSystem (
        system:
        let
          self = import ./. { pkgs = nixpkgs.legacyPackages.${system}; };
        in
        {
          default = self.packages.brr;
          brr = self.packages.brr;
        }
      );

      apps = eachSystem (system: {
        default = {
          type = "app";
          program = nixpkgs.lib.getExe self.packages.${system}.default;
        };
      });
    };
}
