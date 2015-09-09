with import <nixpkgs> {};

buildPythonPackage {
  name = "idris_kernel";

  buildInputs = with pkgs.pythonPackages; [ haskellPackages.idris python pyzmq ipython pexpect sexpdata ];

  src = ./.;
}
