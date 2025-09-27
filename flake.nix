{
  description = "flake";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };
  outputs = { self, nixpkgs, ... }: let
    pkgs = nixpkgs.legacyPackages."x86_64-linux";
    pythonPackages = pkgs.python312Packages;
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      packages = [
        (pkgs.python312.withPackages (python-pkgs: with python-pkgs; [
	  python
	  pip
	  pandas
	  numpy
	  requests
	  uv
	  discordpy
	  python-dotenv
	  sqlalchemy
	]))
	pkgs.postgresql.pg_config
      ];
      #env.LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      #  pkgs.stdenv.cc.cc.lib
      #   pkgs.libz
      #];
      shellHook = ''
    set -h #remove "bash: hash: hashing disabled" warning !
    # https://nixos.org/manual/nixpkgs/stable/#python-setup.py-bdist_wheel-cannot-create-.whl
    SOURCE_DATE_EPOCH=$(date +%s)
    # Let's allow compiling stuff
    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath (with pkgs; [ zlib stdenv.cc.cc ])}":LD_LIBRARY_PATH;

    export VENVPATH=.venv${pkgs.python312.version}

    if ! [ -d $VENVPATH ]; then
      python -m venv $VENVPATH
    fi

    source $VENVPATH/bin/activate

    export TMPDIR=/tmp/pipcache

    if [ ! -x $VENVPATH/bin/py3dtiles ] > /dev/null 2>&1; then
      python -m pip install --cache-dir=$TMPDIR --upgrade pip
      python -m pip install --cache-dir="$TMPDIR" -e .\[postgres,las,ply,dev,doc,pack\]
      # keep this line after so that ipython deps doesn't conflict with other deps
      python -m pip install ipython debugpy
    fi
    '';
    };
  };
}
