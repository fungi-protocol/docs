{ ... }:
{
  perSystem =
    { pkgs, ... }:
    {
      checks.typos = pkgs.runCommand "typos" { nativeBuildInputs = [ pkgs.typos ]; } ''
        cd ${../.}
        typos
        touch $out
      '';
    };
}
