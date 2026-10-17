{ ... }:
{
  perSystem =
    { pkgs, ... }:
    {
      _module.args.relink = pkgs.rustPlatform.buildRustPackage {
        pname = "relink";
        version = "0.1.0";
        src = ../contrib/relink;
        cargoLock.lockFile = ../contrib/relink/Cargo.lock;
      };
    };
}
