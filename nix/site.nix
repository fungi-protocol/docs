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
          mdbook build -d $out
        '';

        dontInstall = true;
      };
    in
    {
      packages = {
        inherit site;
        default = site;
      };
    };
}
