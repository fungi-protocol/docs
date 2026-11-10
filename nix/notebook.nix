{ ... }:
{
  perSystem =
    { pkgs, ... }:
    let
      # Every dependency of the notebook is packaged in nixpkgs.
      notebookDeps =
        p: with p; [
          ipykernel
          matplotlib
          nbconvert
          numpy
          pandas
          seaborn
        ];
    in
    {
      # The notebook, re-executed. Execution is deterministic and records no
      # timing metadata, so an up to date notebook is byte-identical to the
      # build output.
      packages.notebook =
        pkgs.runCommand "Denominations_and_gap_size_distributions.ipynb"
          { nativeBuildInputs = [ (pkgs.python3.withPackages notebookDeps) ]; }
          ''
            export HOME=$(mktemp -d)
            install -m 644 ${../docs/Denominations_and_gap_size_distributions.ipynb} notebook.ipynb
            jupyter nbconvert --execute --inplace --to notebook \
              --ExecutePreprocessor.record_timing=False notebook.ipynb
            cp notebook.ipynb $out
          '';

      devShells.notebook = pkgs.mkShell {
        packages = [ (pkgs.python3.withPackages (p: notebookDeps p ++ [ p.jupyterlab ])) ];
      };
    };
}
