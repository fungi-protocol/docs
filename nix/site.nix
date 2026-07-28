{ ... }:
{
  perSystem =
    { pkgs, ... }:
    let
      site = pkgs.stdenvNoCC.mkDerivation {
        name = "fungi-docs";
        src = ../.;

        nativeBuildInputs = with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
        ];

        buildPhase = ''
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
