# AList Media Manager

A shareable Codex skill for organizing AList-mounted movie and TV libraries while preserving files, metadata identity, subtitle associations, and audit evidence.

## Install

Copy this repository into `~/.agents/skills/alist-media-manager`, or use your Codex skill installer with this repository. Codex discovers installed skills automatically; restart or open a new chat if it does not appear. The skill entry point is `SKILL.md`. See [official local skill installation guidance](https://developers.openai.com/codex/skills#where-to-save-skills).

## Configure private access

Create `~/.config/alist/access.json` locally:

```json
{"url":"http://YOUR-ALIST-HOST:PORT","username":"YOUR-USERNAME","password":"YOUR-PASSWORD"}
```

On Linux/macOS, restrict this file to its owner (`chmod 600`). On Windows, use a private user configuration directory. You can instead set `ALIST_CONFIG` to an ignored workspace configuration file. Do not store access configuration in this repository.

## Use

```sh
python3 scripts/alist.py list /YOUR-MOUNT
python3 scripts/alist.py --config /private/access.json crawl /YOUR-MOUNT/Movies
python3 scripts/probe_media.py --config /private/access.json '/YOUR-MOUNT/Movies/Title/video.mkv'
```

The bundled API and MP4/Matroska metadata helpers use the Python standard library. Container inspection uses finite HTTP ranges and a bounded byte budget. Frame sampling, legacy formats, and subtitle timing checks need suitable additional tools. A missing subtitle track does not rule out captions burned into the picture.

Before changing a library, follow `SKILL.md`: inventory both locations, verify metadata, journal exact paths and sizes, preserve distinct editions, and verify every mutation. The skill contains no credentials, account-specific mount paths, or private inventory.
