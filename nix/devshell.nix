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
          python3
        ]);
      };

      # Only editing or re-executing a notebook needs the scientific stack, so it
      # stays out of the default shell. Re-executing is deterministic, and
      # without timing metadata a second run leaves the notebook byte-identical:
      #   nix develop .#notebook -c jupyter nbconvert --execute --inplace \
      #     --to notebook --ExecutePreprocessor.record_timing=False NOTEBOOK.ipynb
      devShells.notebook = pkgs.mkShell {
        packages = [
          (pkgs.python3.withPackages (
            p: with p; [
              ipykernel
              jupyterlab
              nbconvert
              matplotlib
              numpy
              pandas
              seaborn
            ]
          ))
        ];
      };
    };
}
