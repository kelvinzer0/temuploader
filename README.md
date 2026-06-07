# temuploader

Stop losing files to dead upload links. One command, auto-fallback, always works.

## What is this?

A CLI tool that uploads files and text to temporary hosting services. If the first provider is down, it tries the next one automatically. No API keys, no signup, no config.

## Install

```bash
pip install temuploader
```

Or from source:

```bash
git clone https://github.com/kelvinzer0/temuploader
cd temuploader
pip install -e .
```

## Usage

Upload a file:

```bash
temuploader myfile.txt
```

Upload a folder (auto-zips it):

```bash
temuploader ./my-folder
```

Upload text directly:

```bash
temuploader -t "Hello world!"
```

Pipe from stdin:

```bash
cat logs.txt | temuploader -
```

Get just the URL for scripting:

```bash
url=$(temuploader myfile.txt --download-url)
```

JSON output:

```bash
temuploader myfile.txt --json
```

## How it works

When you upload something, temuploader picks the right provider based on file type and size. If that provider fails (timeout, rate limit, down), it automatically tries the next one. You always get a working link.

```
Trying tmpfiles.org...  failed (timeout)
Trying litterbox...     failed (rate limited)
Trying uguu.se...       success!
https://n.uguu.se/abc123.txt
```

## Providers

10 providers, no API keys needed:

- **tmpfiles.org** - 100MB, 60 min retention, fast and reliable
- **litterbox** - 100MB, 24h to 1 week retention (configurable with --time)
- **uguu.se** - 100MB, 48h retention, clean API
- **catbox.moe** - 200MB, permanent hosting
- **gofile.io** - 500MB, 10 day retention, biggest size limit
- **filebin.net** - 100MB, bin system, no signup
- **paste.rs** - 1MB, text only, simplest API
- **del.dog** - 1MB, text only, permanent pastes
- **rentry.co** - 1MB, text only, markdown support
- **termbin.com** - 1MB, text only, netcat-based

Text files use paste services. Binary files use file hosting providers. Both fallback automatically.

## Options

```
-p, --providers    Pick specific providers to try
--no-fallback      Stop after the first provider fails
--json             Output as JSON
--download-url     Output only the download URL
-v, --verbose      Show what's happening
-l, --list         List all providers and their limits
--time             Retention time for litterbox (24h/72h/1w)
```

## Python API

```python
from temuploader import upload, upload_text, quick_share

# Upload a file
result = upload("data.csv")
print(result.download_url)

# Upload a folder (auto-zipped)
result = upload("./my-folder")
print(result.download_url)

# Upload text
result = upload_text("emergency paste!")
print(result.download_url)

# One-liner
url = quick_share("just give me a url")
```

## Why not just use X?

Every temp upload service dies eventually. transfer.sh, 0x0.st, file.io... they all go down, get rate limited, or block your IP. Instead of memorizing which service works this week, use one tool that tries them all.

## Contributing

Add a new provider: create a class in `providers.py` that extends `BaseProvider`. That's it.

## License

MIT
