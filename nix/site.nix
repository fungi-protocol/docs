{ inputs, lib, ... }:
{
  perSystem =
    { pkgs, mmdc, relink, ... }:
    let
      repository = "https://github.com/fungi-protocol/docs";
      # Links out of the book name the revision the site is built from; a
      # build of a modified tree names the commit it modifies.
      rev = inputs.self.rev or (lib.removeSuffix "-dirty" (inputs.self.dirtyRev or "main"));
      site = pkgs.stdenvNoCC.mkDerivation {
        name = "fungi-docs";
        src = ../.;

        nativeBuildInputs = [ mmdc relink ] ++ (with pkgs; [
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
          python3 contrib/book.py . src
          export MDBOOK_PREPROCESSOR__RELINK__BLOB=${repository}/blob/${rev}
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
            { nativeBuildInputs = [ (pkgs.python3.withPackages (ps: [ ps.pytest ])) ]; }
            ''
              cd ${../contrib}
              pytest -p no:cacheprovider
              touch $out
            '';
        links = pkgs.runCommand "links" { nativeBuildInputs = [ pkgs.lychee pkgs.cacert ]; } ''
          # Links to the repository are checked against the tree the site is built from.
          lychee --offline --include-fragments --no-progress --root-dir ${site} \
            --remap '^${repository}/blob/${rev}/ file://${../.}/' ${site}
          touch $out
        '';
      };

      packages = {
        inherit site;
        default = site;
      };
    };
}
