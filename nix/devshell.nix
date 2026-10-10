{ ... }:
{
  perSystem =
    { pkgs, mmdc, relink, ... }:
    {
      devShells.default = pkgs.mkShell {
        packages = [ mmdc relink ] ++ (with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
          (python3.withPackages (ps: [ ps.pytest ]))
        ]);
      };
    };
}
