{
  perSystem =
    { pkgs, ... }:
    let
      stale-drafts = pkgs.writeShellApplication {
        name = "stale-drafts";
        runtimeInputs = [
          (pkgs.python3.withPackages (ps: [ ps.pyyaml ]))
          pkgs.gh
        ];
        text = ''python3 ${../../../contrib}/stale.py "$@"'';
      };
    in
    {
      packages.stale-drafts = stale-drafts;
      apps.stale-drafts = {
        type = "app";
        program = "${stale-drafts}/bin/stale-drafts";
        meta.description = "Open an issue for each draft that goes stale within a week";
      };
    };
}
