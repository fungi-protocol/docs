{ ... }:
{
  perSystem =
    {
      pkgs,
      lib,
      fontconfig,
      mermaidSvgs,
      ...
    }:
    let
      # Only what the book is built from, so that changes to the nix files,
      # the tests or the spelling dictionaries do not rebuild it.
      src = lib.fileset.toSource {
        root = ../.;
        fileset = lib.fileset.unions [
          ../README.md
          ../book.toml
          ../docs
          ../theme
          (lib.fileset.fileFilter (
            f: f.hasExt "py" && !lib.hasPrefix "test_" f.name && f.name != "robot_marks.py"
          ) ../contrib)
        ];
      };

      site = pkgs.stdenvNoCC.mkDerivation {
        name = "fungi-docs";
        inherit src;

        nativeBuildInputs = with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
          (python3.withPackages (ps: [ ps.pyyaml ]))
        ];

        MERMAID_SVG_DIR = mermaidSvgs (
          [ ../README.md ]
          ++ lib.filter (f: lib.hasSuffix ".md" (toString f)) (lib.filesystem.listFilesRecursive ../docs)
        );

        buildPhase = ''
          export FONTCONFIG_FILE=${fontconfig}
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
            {
              nativeBuildInputs = [
                (pkgs.python3.withPackages (ps: [ ps.hypothesis ps.pytest ps.pyyaml ]))
              ];
              HYPOTHESIS_PROFILE = "nix";
            }
            ''
              # Hypothesis keeps a cache next to the tests.
              cp -r ${../contrib} contrib && chmod -R u+w contrib && cd contrib
              pytest -p no:cacheprovider
              touch $out
            '';
        # A 🤖 mark covers what is under it, so one inside another is
        # redundant, and a chapter's title and index entry must agree.
        robot-marks = pkgs.runCommand "robot-marks" { nativeBuildInputs = [ pkgs.python3 ]; } ''
          python3 ${../contrib/robot_marks.py} --docs ${../docs} check
          touch $out
        '';
        # lychee loads CA certificates to build its HTTP client even with --offline.
        links = pkgs.runCommand "links" { nativeBuildInputs = [ pkgs.lychee pkgs.cacert ]; } ''
          # The site is served from /docs-draft/, so a link from the root leaves it.
          mkdir root && ln -s ${site} root/docs-draft
          # The 404 page needs <base href="/docs-draft/"> for browsers to find its assets.
          # Lychee does not check this, so verify it separately.
          grep -qF '<base href="/docs-draft/">' root/docs-draft/404.html
          lychee --offline --include-fragments --no-progress --root-dir $PWD/root root/docs-draft
          touch $out
        '';
      };

      packages = {
        inherit site;
        default = site;
      };
    };
}
