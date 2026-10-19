{
  perSystem =
    { pkgs, ... }:
    let
      validate-commits = pkgs.writeShellApplication {
        name = "validate-commits";
        runtimeInputs = [
          pkgs.git
          pkgs.nix
        ];
        text = builtins.readFile ./validate-commits.sh;
      };
    in
    {
      packages.validate-commits = validate-commits;
      apps.validate-commits = {
        type = "app";
        program = "${validate-commits}/bin/validate-commits";
        meta.description = "Validate the flake across pull request commits";
      };
    };
}
