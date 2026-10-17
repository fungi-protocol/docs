{ ... }:
{
  perSystem =
    { pkgs, mmdc, ... }:
    {
      devShells.default = pkgs.mkShell {
        packages = [ mmdc ] ++ (with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
          (python3.withPackages (ps: [ ps.pytest ]))
        ]);
      };
    };
}
