{ ... }:
{
  perSystem =
    { pkgs, mmdc, ... }:
    let
      site = pkgs.stdenvNoCC.mkDerivation {
        name = "fungi-docs";
        src = ../.;

        nativeBuildInputs = [ mmdc ] ++ (with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
          python3
        ]);

        buildPhase = ''
          # mmdc writes a chromium profile under $HOME.
          export HOME=$(mktemp -d)
          # mermaid measures text with getBBox and rejects a zero-sized box, so
          # the build sandbox has to carry a font of its own.
          export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ pkgs.dejavu_fonts ]; }}
          mdbook build -d $out
        '';

        dontInstall = true;
      };
    in
    {
      checks = {
        inherit site;
      };

      packages = {
        inherit site;
        default = site;
      };
    };
}
