{ ... }:
{
  perSystem =
    { pkgs, lib, ... }:
    let
      # The only chromium nixpkgs has for darwin sits inside playwright's
      # prebuilt browsers, under a directory whose name changes with every
      # bump. Resolve it once and bake it in, so no caller has to export a
      # path.
      mmdc = pkgs.symlinkJoin {
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

      # mermaid measures text with getBBox and rejects a zero-sized box, so
      # the build sandbox has to carry a font of its own.
      fontconfig = pkgs.makeFontsConf { fontDirectories = [ pkgs.dejavu_fonts ]; };

      # The bodies of the ```mermaid blocks in a markdown text, as FENCE in
      # contrib/mermaid_ssr.py finds them.
      blocks =
        text:
        let
          step =
            state: line:
            if state.fence == null then
              let
                open = builtins.match "(`{3,})mermaid.*" line;
              in
              if open == null then state else state // { fence = builtins.head open; }
            else if builtins.match "${state.fence}[ \t]*" line != null then
              {
                fence = null;
                lines = [ ];
                found = state.found ++ [ (lib.concatMapStrings (l: l + "\n") state.lines) ];
              }
            else
              state // { lines = state.lines ++ [ line ]; };
        in
        (builtins.foldl' step {
          fence = null;
          lines = [ ];
          found = [ ];
        } (lib.splitString "\n" text)).found;

      # One derivation per diagram, whose only input is the diagram's text,
      # so edits elsewhere in the book leave it cached. mermaid_ssr.py finds
      # it by the sha256 of that text, and replaces the placeholder svg ids.
      render =
        body:
        let
          hash = builtins.hashString "sha256" body;
        in
        {
          name = hash;
          path =
            pkgs.runCommand "mermaid-${builtins.substring 0 12 hash}"
              { nativeBuildInputs = [ mmdc ]; }
              ''
                # mmdc writes a chromium profile under $HOME.
                export HOME=$(mktemp -d)
                export FONTCONFIG_FILE=${fontconfig}
                mkdir $out
                for theme in default dark; do
                  mmdc -i ${builtins.toFile "diagram.mmd" body} -o $out/$theme.svg \
                    -b transparent -t $theme -I MERMAID_SSR_ID
                done
              '';
        };
    in
    {
      _module.args = {
        inherit mmdc fontconfig;

        # The diagrams of these markdown files, rendered, as mermaid_ssr.py
        # expects to find them in MERMAID_SVG_DIR.
        mermaidSvgs =
          files:
          pkgs.linkFarm "mermaid-svgs" (
            map render (lib.unique (lib.concatMap (f: blocks (builtins.readFile f)) files))
          );
      };
    };
}
