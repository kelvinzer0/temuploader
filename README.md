# 📤 temuploader

Temporary file uploader with automatic fallback. Upload files or text, get a URL. If one provider fails, it automatically tries the next.

## Install

```bash
pip install -e .
# or
pip install temuploader
```

## CLI Usage

```bash
# Upload a file
temuploader myfile.txt

# Upload text directly
temuploader -t "Hello world"

# Pipe from stdin
echo "some output" | temuploader -
cat myfile.log | temuploader -

# Choose specific providers
temuploader myfile.bin -p litterbox tmpfiles.org

# JSON output
temuploader myfile.txt --json

# Just the URL (for scripting)
url=$(temuploader myfile.txt --download-url)

# List providers
temuploader --list

# Verbose mode
temuploader myfile.txt -v

# Set retention (litterbox)
temuploader myfile.txt --time 1w
```

## Python API

```python
from temuploader import upload, upload_text, upload_file

# Upload a file (auto-fallback)
result = upload("myfile.txt")
print(result.download_url)
print(result.provider)  # which provider was used

# Upload text
result = upload_text("Hello world!")
print(result.download_url)

# One-liners
from temuploader import quick_share, quick_file

url = quick_share("quick paste this")
url = quick_file("myfile.txt")

# Choose providers
result = upload("myfile.bin", providers=["litterbox", "uguu"])

# Disable fallback (fail fast)
result = upload("myfile.txt", fallback=False, providers=["paste.rs"])

# Verbose output
result = upload("myfile.txt", verbose=True)
```

## Providers

| Provider | Max Size | Retention | Binary | Text |
|----------|----------|-----------|--------|------|
| tmpfiles.org | 100MB | 60 min | ✓ | ✓ |
| litterbox | 100MB | 24h-1w | ✓ | ✓ |
| uguu.se | 100MB | 48h | ✓ | ✓ |
| catbox.moe | 200MB | permanent | ✓ | ✓ |
| paste.rs | 1MB | long | ✗ | ✓ |
| del.dog | 1MB | permanent | ✗ | ✓ |
| rentry.co | 1MB | permanent | ✗ | ✓ |
| filebin.net | 100MB | varies | ✓ | ✓ |
| gofile.io | 500MB | 10d | ✓ | ✓ |
| termbin.com | 1MB | 30d | ✗ | ✓ |

## Default Fallback Order

**Files:** `tmpfiles.org → litterbox → uguu → catbox → gofile → filebin`

**Text:** `paste.rs → del.dog → rentry → termbin → tmpfiles.org → litterbox`

## How It Works

1. Auto-detects file type (text vs binary)
2. Filters providers by capability & size limit
3. Tries providers in order
4. On failure → automatically falls back to next provider
5. Returns first successful result

## Dependencies

- Python 3.8+
- `curl` (must be in PATH)
- `nc` (netcat, optional — only for termbin)
