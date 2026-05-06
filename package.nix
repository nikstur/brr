{
  lib,
  python3Packages,
  makeBinaryWrapper,
  ninja,
  tmux,
}:

python3Packages.buildPythonApplication {
  pname = "brr";
  version = "0.1.0";
  pyproject = true;

  src = lib.sourceFilesBySuffices ./. [
    ".py"
    ".toml"
  ];

  build-system = with python3Packages; [ setuptools ];

  nativeBuildInputs = [
    makeBinaryWrapper
  ];

  buildInputs = [
    ninja
    tmux
  ];

  postInstall = ''
    wrapProgram $out/bin/brr \
      --prefix PATH : ${
        lib.makeBinPath [
          ninja
          tmux
        ]
      }
  '';

  meta = {
    mainProgram = "brr";
  };
}
