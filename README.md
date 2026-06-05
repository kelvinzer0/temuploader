# 📤 temuploader

### Stop losing files to dead upload links. One command. Auto-fallback. Always works.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Providers: 10](https://img.shields.io/badge/providers-10-orange.svg)](#providers)

---

## 😤 The Problem

You need to share a file. Right now. From the terminal.

You try `transfer.sh` — **dead**. You try `0x0.st` — **uploads disabled**. You try three more — **rate limited**, **Cloudflare blocked**, **404**.

**You just wasted 5 minutes on something that should take 5 seconds.**

Every temp upload tool you've used has the same fatal flaw: **single point of failure**. When that one provider goes down, you're stuck.

---

## 💡 The Solution

```bash
temuploader myfile.txt
```

That's it. **One command.** If the first provider fails, it automatically tries the next. And the next. Until it works.

**It always works.**

---

## ⚡ Quick Start

```bash
# Install
pip install -e .

# Upload a file (auto-fallback)
temuploader myfile.txt

# Upload text directly
temuploader -t "Hello world!"

# Pipe from stdin
cat logs.txt | temuploader -

# Get just the URL (for scripting)
url=$(temuploader myfile.txt --download-url)
```

---

## 🧠 Why This Exists

Every developer has been here:

| Scenario | What happens |
|----------|-------------|
| Sharing a log snippet | Paste service is down |
| Quick file transfer | Provider blocked by Cloudflare |
| CI artifact sharing | Rate limited |
| Debug output | Link expired |

**The problem isn't the tools. It's the dependency on a single tool.**

`temuploader` solves this with **automatic fallback** — the same principle behind load balancers, DNS failover, and redundant systems. But for file uploads.

---

## 🎯 Features That Actually Matter

### 🔄 Automatic Fallback
```
Trying tmpfiles.org... ✗ (timeout)
Trying litterbox... ✗ (rate limited)
Trying uguu.se... ✓ https://n.uguu.se/abc123.txt
```
**No manual retry. No provider research. It just works.**

### 🧪 Smart Detection
Automatically detects text vs binary files and picks the right providers. No flags needed.

### 📊 10 Providers, One Interface
```
tmpfiles.org → litterbox → uguu → catbox → gofile → filebin
paste.rs → del.dog → rentry → termbin → tmpfiles.org → litterbox
```
Files use binary-capable providers. Text uses paste services. Both fallback automatically.

### 🔧 Two Interfaces, Same Power
```bash
# CLI
temuploader myfile.txt --json

# Python
from temuploader import upload
result = upload("myfile.txt")
print(result.download_url)
```

---

## 📦 Providers

| Provider | Max Size | Retention | Binary | Text | Why It's Here |
|----------|----------|-----------|--------|------|---------------|
| **tmpfiles.org** | 100MB | 60 min | ✅ | ✅ | Fast, reliable, direct download |
| **litterbox** | 100MB | 24h–1w | ✅ | ✅ | Flexible retention, catbox ecosystem |
| **uguu.se** | 100MB | 48h | ✅ | ✅ | Clean JSON API, fast |
| **catbox.moe** | 200MB | permanent | ✅ | ✅ | Permanent file hosting |
| **paste.rs** | 1MB | long | ❌ | ✅ | Simplest text upload possible |
| **del.dog** | 1MB | permanent | ❌ | ✅ | Permanent paste, raw URL |
| **rentry.co** | 1MB | permanent | ❌ | ✅ | Markdown support, edit URLs |
| **filebin.net** | 100MB | varies | ✅ | ✅ | Bin system, no signup |
| **gofile.io** | 500MB | 10d | ✅ | ✅ | Largest size limit |
| **termbin.com** | 1MB | 30d | ❌ | ✅ | Netcat-based, zero deps |

---

## 🔥 Real Usage

### Share a log file instantly
```bash
temuploader /var/log/app.log --download-url
# → https://litter.catbox.moe/abc123.log
```

### Pipe debug output
```bash
python app.py 2>&1 | temuploader -
# → https://paste.rs/xyz789
```

### Use in scripts
```bash
URL=$(temuploader report.csv --json | jq -r '.download_url')
echo "Download: $URL"
```

### Python integration
```python
from temuploader import upload, upload_text, quick_share

# Full control
result = upload("data.csv", providers=["tmpfiles.org", "uguu"], verbose=True)
print(f"Uploaded via {result.provider}: {result.download_url}")

# One-liner
url = quick_share("emergency paste!")
```

### Force specific providers
```bash
# Only try these two
temuploader myfile.bin -p litterbox tmpfiles.org

# Text-only providers
temuploader -t "code snippet" -p paste.rs del.dog
```

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   CLI / API │────▶│  Core Engine  │────▶│  Provider 1 │ ✗ fail
│             │     │  (fallback)  │────▶│  Provider 2 │ ✗ fail
└─────────────┘     └──────────────┘────▶│  Provider 3 │ ✓ success!
                                         └─────────────┘
```

**How fallback works:**
1. Detect file type (text vs binary)
2. Filter providers by capability & size
3. Try first provider
4. On failure → automatically try next
5. Return first success
6. If all fail → detailed error report

---

## 📐 Design Decisions

| Decision | Why |
|----------|-----|
| **curl-based** | Zero Python HTTP dependencies. Works everywhere. |
| **No API keys** | All providers are free, no signup required. |
| **Explicit fallback order** | Predictable. You know what gets tried first. |
| **Provider isolation** | One provider failing doesn't affect others. |
| **Dual output (CLI + Python)** | Use it in scripts OR as a library. |

---

## 🛡️ What This Is NOT

- ❌ Not a cloud storage service
- ❌ Not for sensitive/private files (all providers are public)
- ❌ Not for large backups (use S3/R2 for that)
- ❌ Not a permanent hosting solution (except catbox/del.dog)

**This is for:** Quick, temporary file sharing when you need a URL *right now* and don't want to think about which service to use.

---

## 📈 Roadmap

- [ ] Self-hosted provider support (minio, S3-compatible)
- [ ] Encryption before upload
- [ ] Custom provider plugins
- [ ] Progress bar for large files
- [ ] Retry with exponential backoff
- [ ] Provider health check/cache

---

## 🤝 Contributing

```bash
git clone https://github.com/kelvinzer0/temuploader
cd temuploader
pip install -e .
temuploader --list  # verify it works
```

Add a new provider? Create a class in `providers.py` that extends `BaseProvider`. That's it.

---

## 📄 License

MIT — use it however you want.

---

<div align="center">

**Stop fighting with upload services. Start shipping.**

```bash
pip install temuploader
```

[⬆️ Back to top](#-temuploader)

</div>
