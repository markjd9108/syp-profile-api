{
  description = "theperformancelens.com";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-26.05";
  };

  outputs = { self, nixpkgs }: let
    systems = [ "x86_64-linux" "aarch64-linux" ];
    forAllSystems = nixpkgs.lib.genAttrs systems (system: let
      pkgs = import nixpkgs { inherit system; };
    in {
      packages.dev_tpl-profile = pkgs.mkShell {
        packages = with pkgs; [
          uv
          python314
        ];
      };
      packages.default = self.packages.${system}.dev_tpl-profile;
    });
  in {
    packages = nixpkgs.lib.mapAttrs (_: v: v.packages) (forAllSystems);
  };
}
