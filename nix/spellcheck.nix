{ ... }:
{
  perSystem =
    { pkgs, ... }:
    {
      checks.cspell = pkgs.runCommand "cspell" { nativeBuildInputs = [ pkgs.cspell ]; } ''
        cd ${../.}
        cspell --config cspell.json --no-progress --show-suggestions
        touch $out
      '';

      checks.typos = pkgs.runCommand "typos" { nativeBuildInputs = [ pkgs.typos ]; } ''
        cd ${../.}
        typos
        touch $out
      '';
    };
}
