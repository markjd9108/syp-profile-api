{
  description = "theperformancelens.com";

  inputs = {
    nixpkgs.url = "nixpkgs/nixos-26.05";
    flake-parts.url = "github:hercules-ci/flake-parts";
  };

  outputs = inputs@{ flake-parts, ... }: flake-parts.lib.mkFlake { inherit inputs; } {
    perSystem = { pkgs, ... }: let
      tpl-api-server = pkgs.writeShellApplication {
        name = "api-server";
        runtimeInputs = [ pkgs.uv python ];
        text = ''
            exec uv run python3 api_server.py "$@"
          '';
      };
      app_tpl-ap-server = {
        type = "app";
        program = "${tpl-api-server}/bin/api-server";
      };
      devShell_tpl-api-server = pkgs.mkShell {
        packages = [
          pkgs.uv python
        ];
        env = {
          UV_PYTHON = "${python}/bin/python3";
        };
      };

      python = pkgs.python314;
    in {
      packages.default = tpl-api-server;
      apps.default = app_tpl-ap-server;
      devShells.default = devShell_tpl-api-server;
    };

    systems = [ "x86_64-linux" "aarch64-linux" ];
  };
}
