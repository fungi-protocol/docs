{ inputs, ... }:
{
  # nixpkgs ships mdbook 0.5 alongside preprocessor releases that predate it
  # and still speak the 0.4 protocol, so the packaged set cannot build a book.
  # Take the upstream releases that added 0.5 support instead. Drop this file
  # once nixpkgs catches up.
  perSystem =
    { system, ... }:
    {
      _module.args.pkgs = import inputs.nixpkgs {
        inherit system;
        overlays = [
          (final: prev: {
            mdbook-graphviz = prev.mdbook-graphviz.overrideAttrs (old: rec {
              version = "0.3.1";
              src = final.fetchFromGitHub {
                owner = "dylanowen";
                repo = "mdbook-graphviz";
                tag = "v${version}";
                hash = "sha256-uqNgP1rRgP6NecReqpinsg7u01gNDpIxX2qag8IyklY=";
              };
              cargoDeps = final.rustPlatform.fetchCargoVendor {
                inherit src;
                hash = "sha256-OBCECv9ZN9xjkOestZbjCXNAA/hAl2u0AtfqxA+cV78=";
              };
            });

            mdbook-katex = prev.mdbook-katex.overrideAttrs (old: rec {
              version = "0.10.0";
              src = final.fetchFromGitHub {
                owner = "lzanini";
                repo = "mdbook-katex";
                tag = "v${version}";
                hash = "sha256-bS8SUzpTqQNYKeGPBf1QD4/AL0TWn3NE4M7A8WLEjUE=";
              };
              cargoDeps = final.rustPlatform.fetchCargoVendor {
                inherit src;
                hash = "sha256-YqQ8Uai2mCG+1X/TmWJPszLYumOjF455Aa5WldgGXF0=";
              };
            });
          })
        ];
      };
    };
}
