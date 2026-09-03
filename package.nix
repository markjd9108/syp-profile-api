{ pkgs, venv }:
{ dream2nix, config, lib, ... }:
{
  imports = [
    dream2nix.modules.dream2nix.mkDerivation
  ];

  name = "tpl-profile-api";
  version = "0.1.0";

  # dream2nix isn't building anything from source here: `venv` is already
  # a fully-built, uv.lock-pinned virtualenv produced by uv2nix. This
  # module's only job is to be the stable packaging surface — wrap that
  # venv, wire up the Playwright browser binaries, expose bin/tpl-api-server.
  mkDerivation = {
    src = ./.; # unused (dontUnpack = true), just satisfies the option
    dontUnpack = true;
    dontBuild = true;
    nativeBuildInputs = [ pkgs.makeWrapper ];

    installPhase = ''
      mkdir -p $out/bin
      makeWrapper ${venv}/bin/tpl-api-server $out/bin/tpl-api-server \
        --set PLAYWRIGHT_BROWSERS_PATH ${pkgs.playwright-driver.browsers} \
        --set PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD 1
    '';
  };
}
