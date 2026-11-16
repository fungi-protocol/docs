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
          ../contrib/pdf-layout.lua
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
          (python3.withPackages (ps: [ ps.pyyaml ]))
        ];

        MERMAID_SVG_DIR = mermaidSvgs (
          [ ../README.md ]
          ++ lib.filter (f: lib.hasSuffix ".md" (toString f)) (lib.filesystem.listFilesRecursive ../docs)
        );

        buildPhase = ''
          export FONTCONFIG_FILE=${fontconfig}
          python3 contrib/book.py --pdf ${pdf}/fungi-docs.pdf .
          mdbook build -d $out
        '';

        dontInstall = true;
      };

      pdf = site.overrideAttrs (old: {
        name = "fungi-docs-pdf";
        nativeBuildInputs = old.nativeBuildInputs ++ [
          pkgs.mdbook-pandoc
          pkgs.pandoc
          # pandoc converts the mermaid SVGs to PDF with rsvg-convert.
          pkgs.librsvg
          (pkgs.texlive.combine {
            inherit (pkgs.texlive) scheme-small newunicodechar fvextra;
          })
        ];
        # MDBOOK_OUTPUT replaces the [output] table of book.toml, so this
        # build runs only the pandoc renderer.
        MDBOOK_OUTPUT = builtins.toJSON {
          pandoc.markdown.extensions.math = true;
          pandoc.profile.pdf = {
            output-file = "fungi-docs.pdf";
            pdf-engine = "xelatex";
            filters = [ "contrib/pdf-layout.lua" ];
            variables.header-includes = ''
              \usepackage{newunicodechar}
              \newfontface\robotfont[Path=${pkgs.noto-fonts-monochrome-emoji}/share/fonts/noto/]{NotoEmoji.ttf}
              \newunicodechar{🤖}{{\normalfont\robotfont\char"1F916\relax}}
              \providecommand{\lt}{<}
              \providecommand{\gt}{>}
              \fvset{breaklines,breakanywhere,fontsize=\footnotesize}
              \usepackage{etoolbox}
              % Leave paragraph space around tall images to avoid fvextra's output loop.
              \ifdefined\pandocbounded
                \patchcmd{\pandocbounded}{\textheight}
                  {\dimexpr\textheight-\baselineskip-2\parskip\relax}
                  {}{\errmessage{Cannot reserve image spacing}}
              \fi
            '';
          };
        };
        buildPhase = ''
          export FONTCONFIG_FILE=${fontconfig}
          export XDG_CACHE_HOME=$(mktemp -d)
          python3 contrib/book.py .
          mdbook build -d book
          install -D book/pdf/fungi-docs.pdf $out/fungi-docs.pdf
        '';
      });
    in
    {
      checks = {
        inherit site pdf;
        book =
          pkgs.runCommand "book-tests"
            {
              nativeBuildInputs = [
                pkgs.pandoc
                (pkgs.python3.withPackages (ps: [ ps.pytest ps.pyyaml ]))
              ];
            }
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
        inherit site pdf;
        default = site;
      };
    };
}
