{ ... }:
{
  perSystem =
    { pkgs, ... }:
    {
      devShells.default = pkgs.mkShell {
        packages = with pkgs; [
          mdbook
          mdbook-graphviz
          mdbook-katex
          graphviz
        ];
      };
    };
}
