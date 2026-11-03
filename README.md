<p align="center">
  <a href="https://pianoverse.in"><img src="docs/hero.jpg" alt="Pianoverse: a piano performance video with falling notes, a saber and particles drawn onto the keys" width="760"></a>
</p>

<h1 align="center">Pianoverse</h1>

<p align="center">
  Falling notes, light and sound for your piano videos. Free, for Windows, no login.<br>
  <a href="https://github.com/HetavShah/pianoverse-releases/releases/latest"><b>Download for Windows</b></a> · <a href="https://pianoverse.in"><b>pianoverse.in</b></a>
</p>

## Install

1. Download the latest **`Pianoverse_…_x64-setup.exe`** from [Releases](https://github.com/HetavShah/pianoverse-releases/releases/latest) and run it.
2. That's it. Pianoverse updates itself: when a new version is out, click **Install and restart** in the top bar.

Windows 10 or 11 (64-bit) with DirectX 12. 8 GB of memory recommended.

## Something wrong?

- In the app: **Settings (the gear) › Send feedback**. You can include today's log.
- Or [open an issue](https://github.com/HetavShah/pianoverse-releases/issues/new/choose). **Settings › Show logs** opens the folder with the logs if you want to attach one.

When something goes wrong, Pianoverse sends an error report: the error and what the app was doing, with file paths cut to their names. Never your video, sound or project. Turn it off in **Settings › Send error reports**.

## What's here

This repository holds the releases, the website and the files the app downloads. The app's source is kept elsewhere.

| | |
|---|---|
| [Releases](https://github.com/HetavShah/pianoverse-releases/releases) | Every version, with its installer and the update file the app checks (`latest.json`) |
| `index.html`, `assets/`, … | [pianoverse.in](https://pianoverse.in), served from `main` as it is. The page's source is `website/index.src.html`: after editing it, run `python3 website/build.py page` and commit |
| `assets/piano/` | The grand piano the app plays your notes on, downloaded once when first picked |

## Credits

Grand piano: [Salamander Grand Piano V3](https://archive.org/details/SalamanderGrandPianoV3) by Alexander Holm, [CC-BY 3.0](https://creativecommons.org/licenses/by/3.0/) (changes in [assets/piano](assets/piano/README.md)). Video by [FFmpeg](https://ffmpeg.org).
