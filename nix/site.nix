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
          (python3.withPackages (ps: [ ps.pyyaml ]))
        ]);

        buildPhase = ''
          # mmdc writes a chromium profile under $HOME.
          export HOME=$(mktemp -d)
          # mermaid measures text with getBBox and rejects a zero-sized box, so
          # the build sandbox has to carry a font of its own.
          export FONTCONFIG_FILE=${pkgs.makeFontsConf { fontDirectories = [ pkgs.dejavu_fonts ]; }}
          python3 contrib/book.py .
          mdbook build -d $out
        '';

        dontInstall = true;
      };
    in
    {
      checks = {
        inherit site;
        book =
          pkgs.runCommand "book-tests"
            { nativeBuildInputs = [ (pkgs.python3.withPackages (ps: [ ps.pytest ps.pyyaml ])) ]; }
            ''
              cd ${../contrib}
              pytest -p no:cacheprovider
              touch $out
            '';
        # lychee loads CA certificates to build its HTTP client even with --offline.
        links = pkgs.runCommand "links" { nativeBuildInputs = [ pkgs.lychee pkgs.cacert ]; } ''
          # The site is served from /docs/, so a link from the root leaves it.
          mkdir root && ln -s ${site} root/docs
          lychee --offline --include-fragments --no-progress --root-dir $PWD/root root/docs
          touch $out
        '';
      };

      packages = {
        inherit site;
        default = site;
      };
    };
}
