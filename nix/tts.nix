{ ... }:
{
  perSystem =
    { pkgs, lib, ... }:
    let
      # Kokoro's weights, config and voice packs, pinned to one revision of
      # the model repository.
      revision = "f3ff3571791e39611d31c381e3a41a3af07b4987";
      fetchModelFile =
        path: hash:
        pkgs.fetchurl {
          url = "https://huggingface.co/hexgrad/Kokoro-82M/resolve/${revision}/${path}";
          inherit hash;
        };
      config = fetchModelFile "config.json" "sha256-WrsB4kA7ByvwPQT94WBEPiCdeg2tSaQjvhUZa5tDwX8=";
      model = fetchModelFile "kokoro-v1_0.pth" "sha256-SW26EY0aWPXz2y78iNvcIW4Eg/yJ/m5H7h8sU/GK0eQ=";

      # The voices the book is read in. The first, by name, is the default.
      voiceHashes = {
        af_heart = "sha256-CrVwm4/6sZv9hJzRHZj3W2CvdzMlOtDWexI4KhAstP8=";
        am_echo = "sha256-i8/chSvJhftFw5bFYeVx/7kYOTAHH5YvG1DfXJexYeg=";
        bf_emma = "sha256-0KQj3qv0pStPSTGMUXQsVOIbuJu76aEhQed1jdtdpwE=";
        bf_isabella = "sha256-zdTDcAOAUQTR0I+x4FhVyPssaN4kym5x8mSjCqpZ7v0=";
      };
      voices = builtins.attrNames voiceHashes;
      # A directory with one voice's pack, so adding a voice leaves the others
      # cached.
      voicePack =
        voice:
        pkgs.linkFarm "kokoro-voice-${voice}" [
          {
            name = "${voice}.pt";
            path = fetchModelFile "voices/${voice}.pt" voiceHashes.${voice};
          }
        ];

      python =
        (pkgs.python3.override {
          packageOverrides = final: prev: {
            # Its tests fail on darwin against pillow 13. Kokoro only reaches
            # it through wandb, and never calls it.
            imageio = prev.imageio.overridePythonAttrs { doCheck = false; };
            # Its hypothesis tests miss their deadlines on a busy builder.
            wandb = prev.wandb.overridePythonAttrs { doCheck = false; };
          };
        }).withPackages
          (ps: [
            ps.kokoro
            ps.soundfile
            ps.spacy-models.en_core_web_sm
          ]);

      tts = ../contrib/tts.py;

      # The chapter's sections, read at evaluation time from a derivation
      # that needs only pandoc.
      sections =
        file:
        lib.importJSON (
          pkgs.runCommand "sections.json"
            { nativeBuildInputs = [ pkgs.python3 pkgs.pandoc ]; }
            ''
              python ${tts} sections ${file} > $out
            ''
        );

      # One derivation per section and voice, whose inputs are the section's
      # text, the voice and the speaking script, so edits elsewhere in the book,
      # or in the chapter, leave it cached.
      speak =
        voice: text:
        pkgs.runCommand "narration-${voice}-${builtins.substring 0 12 (builtins.hashString "sha256" text)}.flac"
          {
            nativeBuildInputs = [ python ];
            KOKORO_CONFIG = config;
            KOKORO_MODEL = model;
            KOKORO_VOICES = voicePack voice;
            HF_HUB_OFFLINE = "1";
            passAsFile = [ "text" ];
            inherit text;
          }
          ''
            export HOME=$(mktemp -d)
            python ${../contrib/speak.py} $textPath ${voice} $out
          '';

      # The chapter's sections joined into one file per voice.
      render =
        file: voice:
        pkgs.runCommand "narration-${voice}-${builtins.substring 0 12 (builtins.hashFile "sha256" file)}"
          {
            nativeBuildInputs = [
              (pkgs.python3.withPackages (ps: [
                ps.numpy
                ps.soundfile
              ]))
              pkgs.ffmpeg
              pkgs.pandoc
            ];
          }
          ''
            python ${tts} join ${file} $out/${voice} ${toString (map (s: speak voice s.text) (sections file))}
          '';
    in
    {
      _module.args = {
        # The narration of these markdown files, as <voice>/<name>.mp3, with
        # the start of each section in <voice>/<name>.json.
        narration =
          files:
          pkgs.symlinkJoin {
            name = "narration";
            paths = lib.concatMap (file: map (render file) voices) files;
          };
      };
    };
}
