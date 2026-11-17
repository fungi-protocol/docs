{ ... }:
{
  perSystem =
    {
      pkgs,
      lib,
      fontconfig,
      mermaidSvgs,
      narration,
      ...
    }:
    let
      # The markdown the book's chapters come from.
      markdown = [
        ../README.md
      ]
      ++ lib.filter (f: lib.hasSuffix ".md" (toString f)) (lib.filesystem.listFilesRecursive ../docs);

      # The markdown read aloud: contrib/book.py leaves these out of the chapters.
      chapters = lib.subtractLists [
        ../docs/index.md
        ../docs/log.md
        ../docs/README.md
      ] markdown;

      # Only what the book is built from, so that changes to the nix files,
      # the tests or the spelling dictionaries do not rebuild it.
      src = lib.fileset.toSource {
        root = ../.;
        fileset = lib.fileset.unions [
          ../README.md
          ../book.toml
          ../docs
          ../theme
          (lib.fileset.fileFilter (f: f.hasExt "py" && !lib.hasPrefix "test_" f.name) ../contrib)
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
          pandoc
          (python3.withPackages (ps: [ ps.pyyaml ]))
        ];

        MERMAID_SVG_DIR = mermaidSvgs markdown;
        TTS_AUDIO_DIR = narration chapters;

        buildPhase = ''
          export FONTCONFIG_FILE=${fontconfig}
          python3 contrib/book.py .
          mdbook build -d $out
          cp -rL $TTS_AUDIO_DIR $out/tts
        '';

        dontInstall = true;
      };
    in
    {
      checks = {
        inherit site;
        book =
          pkgs.runCommand "book-tests"
            { nativeBuildInputs = [ pkgs.pandoc (pkgs.python3.withPackages (ps: [ ps.pytest ps.pyyaml ])) ]; }
            ''
              cd ${../contrib}
              pytest -p no:cacheprovider
              touch $out
            '';
        # lychee loads CA certificates to build its HTTP client even with --offline.
        links = pkgs.runCommand "links" { nativeBuildInputs = [ pkgs.lychee pkgs.cacert ]; } ''
          # The site is served from /docs/, so a link from the root leaves it.
          mkdir root && ln -s ${site} root/docs
          # The 404 page needs <base href="/docs/"> for browsers to find its assets.
          # Lychee does not check this, so verify it separately.
          grep -qF '<base href="/docs/">' root/docs/404.html
          lychee --offline --include-fragments --no-progress --root-dir $PWD/root root/docs
          touch $out
        '';
      };

      packages = {
        inherit site;
        narration = narration chapters;
        default = site;
      };
    };
}
