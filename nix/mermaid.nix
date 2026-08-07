{ ... }:
{
  # The only chromium nixpkgs has for darwin sits inside playwright's prebuilt
  # browsers, under a directory whose name changes with every bump. Resolve it
  # once and bake it in, so no caller has to export a path.
  perSystem =
    { pkgs, ... }:
    {
      _module.args.mmdc = pkgs.symlinkJoin {
        name = "mmdc-with-browser";
        paths = [ pkgs.mermaid-cli ];
        nativeBuildInputs = [ pkgs.makeWrapper ];
        postBuild = ''
          browser=$(find -L ${pkgs.playwright-driver.browsers} \
            \( -name chrome-headless-shell -o -name headless_shell \) \
            -type f | head -1)
          test -n "$browser" || { echo "no chromium in playwright browsers"; exit 1; }

          # --no-sandbox: chromium's own sandbox cannot nest inside the nix
          # build sandbox.
          echo "{\"executablePath\":\"$browser\",\"args\":[\"--no-sandbox\"]}" \
            > $out/puppeteer.json

          wrapProgram $out/bin/mmdc \
            --add-flags "--puppeteerConfigFile $out/puppeteer.json"
        '';
      };
    };
}
