"""
Provider implementations for temuploader.
Each provider has: upload, download_url, max_size, retention, supports_binary.
"""

import os
import json
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class UploadResult:
    """Result of an upload operation."""

    url: str
    download_url: str
    provider: str
    raw_response: str = ""
    extra: dict = field(default_factory=dict)

    def __str__(self):
        return self.download_url


class ProviderError(Exception):
    """Raised when a provider fails."""

    pass


class BaseProvider(ABC):
    """Base class for all upload providers."""

    name: str = ""
    base_url: str = ""
    max_size_mb: int = 10
    retention: str = "unknown"
    supports_binary: bool = True
    supports_text: bool = True

    @abstractmethod
    def upload(self, filepath: str, filename: str = None) -> UploadResult: ...

    def upload_text(self, text: str) -> UploadResult:
        """Upload text content. Override if provider has text-specific API."""
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(text)
            tmp = f.name
        try:
            return self.upload(tmp)
        finally:
            os.unlink(tmp)


def _curl(args: list, timeout: int = 30) -> str:
    """Run curl with args and return stdout."""
    cmd = ["curl", "-s", "--max-time", str(timeout)] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5)
        if r.returncode != 0:
            raise ProviderError(f"curl failed: {r.stderr.strip()}")
        return r.stdout.strip()
    except subprocess.TimeoutExpired:
        raise ProviderError("Request timed out")


# ─────────────────────────────────────────────
# File Upload Providers
# ─────────────────────────────────────────────


class TmpFilesOrg(BaseProvider):
    name = "tmpfiles.org"
    base_url = "https://tmpfiles.org"
    max_size_mb = 100
    retention = "60min"
    supports_binary = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        resp = _curl(["-F", f"file=@{filepath}", f"{self.base_url}/api/v1/upload"])
        data = json.loads(resp)
        if data.get("status") != "success":
            raise ProviderError(f"Upload failed: {resp}")
        url = data["data"]["url"]
        # Convert to direct download URL
        dl_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        return UploadResult(
            url=url, download_url=dl_url, provider=self.name, raw_response=resp
        )


class Litterbox(BaseProvider):
    name = "litterbox.catbox.moe"
    base_url = "https://litterbox.catbox.moe/resources/internals/api.php"
    max_size_mb = 100
    retention = "72h"
    supports_binary = True

    def __init__(self, time: str = "72h"):
        self.time = time

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        resp = _curl(
            [
                "-F",
                "reqtype=fileupload",
                "-F",
                f"time={self.time}",
                "-F",
                f"fileToUpload=@{filepath}",
                self.base_url,
            ]
        )
        if not resp.startswith("http"):
            raise ProviderError(f"Upload failed: {resp}")
        return UploadResult(
            url=resp, download_url=resp, provider=self.name, raw_response=resp
        )


class Uguu(BaseProvider):
    name = "uguu.se"
    base_url = "https://uguu.se/upload"
    max_size_mb = 100
    retention = "48h"
    supports_binary = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        resp = _curl(["-F", f"files[]=@{filepath}", self.base_url])
        data = json.loads(resp)
        if not data.get("success"):
            raise ProviderError(f"Upload failed: {resp}")
        url = data["files"][0]["url"]
        return UploadResult(
            url=url, download_url=url, provider=self.name, raw_response=resp
        )


class CatboxMoe(BaseProvider):
    name = "catbox.moe"
    base_url = "https://catbox.moe/user/api.php"
    max_size_mb = 200
    retention = "permanent"
    supports_binary = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        resp = _curl(
            [
                "-F",
                "reqtype=fileupload",
                "-F",
                f"fileToUpload=@{filepath}",
                self.base_url,
            ]
        )
        if not resp.startswith("http"):
            raise ProviderError(f"Upload failed: {resp}")
        return UploadResult(
            url=resp, download_url=resp, provider=self.name, raw_response=resp
        )


class PasteRs(BaseProvider):
    name = "paste.rs"
    base_url = "https://paste.rs"
    max_size_mb = 1
    retention = "long"
    supports_binary = False  # text only
    supports_text = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        resp = _curl(["--data-binary", f"@{filepath}", self.base_url])
        if not resp.startswith("http"):
            raise ProviderError(f"Upload failed: {resp}")
        return UploadResult(
            url=resp, download_url=resp, provider=self.name, raw_response=resp
        )

    def upload_text(self, text: str) -> UploadResult:
        resp = _curl(["-d", text, self.base_url])
        if not resp.startswith("http"):
            raise ProviderError(f"Upload failed: {resp}")
        return UploadResult(
            url=resp, download_url=resp, provider=self.name, raw_response=resp
        )


class DelDog(BaseProvider):
    name = "del.dog"
    base_url = "https://del.dog"
    max_size_mb = 1
    retention = "permanent"
    supports_binary = False
    supports_text = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        with open(filepath, "r") as f:
            text = f.read()
        return self.upload_text(text)

    def upload_text(self, text: str) -> UploadResult:
        resp = _curl(
            [
                "-X",
                "POST",
                "-H",
                "Content-Type: text/plain",
                "-d",
                text,
                f"{self.base_url}/documents",
            ]
        )
        data = json.loads(resp)
        key = data.get("key")
        if not key:
            raise ProviderError(f"Upload failed: {resp}")
        url = f"{self.base_url}/{key}"
        dl_url = f"{self.base_url}/raw/{key}"
        return UploadResult(
            url=url, download_url=dl_url, provider=self.name, raw_response=resp
        )


class RentryCo(BaseProvider):
    name = "rentry.co"
    base_url = "https://rentry.co"
    max_size_mb = 1
    retention = "permanent"
    supports_binary = False
    supports_text = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        with open(filepath, "r") as f:
            text = f.read()
        return self.upload_text(text)

    def upload_text(self, text: str) -> UploadResult:
        resp = _curl(["-X", "POST", "-F", f"text={text}", f"{self.base_url}/api/new"])
        data = json.loads(resp)
        if data.get("status") != "200":
            raise ProviderError(f"Upload failed: {resp}")
        url = data["url"]
        dl_url = f"{url}/raw"
        return UploadResult(
            url=url, download_url=dl_url, provider=self.name, raw_response=resp
        )


class FilebinNet(BaseProvider):
    name = "filebin.net"
    base_url = "https://filebin.net"
    max_size_mb = 100
    retention = "varies"
    supports_binary = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        fname = filename or os.path.basename(filepath)
        import time

        bin_id = f"tem{int(time.time())}"
        resp = _curl(
            [
                "-X",
                "POST",
                "-H",
                "Content-Type: application/octet-stream",
                "--data-binary",
                f"@{filepath}",
                f"{self.base_url}/{bin_id}/{fname}",
            ]
        )
        url = f"{self.base_url}/{bin_id}/{fname}"
        return UploadResult(
            url=url, download_url=url, provider=self.name, raw_response=resp
        )


class GofileIo(BaseProvider):
    name = "gofile.io"
    base_url = "https://gofile.io"
    max_size_mb = 500
    retention = "10d"
    supports_binary = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        # Get best server
        resp = _curl(["https://api.gofile.io/servers"])
        servers = json.loads(resp)
        server = servers["data"]["servers"][0]["name"]

        resp = _curl(
            [
                "-F",
                f"file=@{filepath}",
                f"https://{server}.gofile.io/contents/uploadfile",
            ]
        )
        data = json.loads(resp)
        if data.get("status") != "ok":
            raise ProviderError(f"Upload failed: {resp}")
        url = data["data"]["downloadPage"]
        return UploadResult(
            url=url,
            download_url=url,
            provider=self.name,
            raw_response=resp,
            extra={"token": data.get("guestToken", "")},
        )


class Termbin(BaseProvider):
    name = "termbin.com"
    base_url = "https://termbin.com"
    max_size_mb = 1
    retention = "30d"
    supports_binary = False
    supports_text = True

    def upload(self, filepath: str, filename: str = None) -> UploadResult:
        with open(filepath, "r") as f:
            text = f.read()
        return self.upload_text(text)

    def upload_text(self, text: str) -> UploadResult:
        try:
            r = subprocess.run(
                ["nc", "termbin.com", "9999"],
                input=text,
                capture_output=True,
                text=True,
                timeout=10,
            )
            url = r.stdout.strip()
            if not url.startswith("http"):
                raise ProviderError(f"Upload failed: {r.stdout}")
            return UploadResult(url=url, download_url=url, provider=self.name)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            raise ProviderError(f"termbin failed: {e}")


# ─────────────────────────────────────────────
# Provider Registry
# ─────────────────────────────────────────────

PROVIDERS = {
    "tmpfiles.org": TmpFilesOrg,
    "litterbox": Litterbox,
    "uguu": Uguu,
    "catbox": CatboxMoe,
    "paste.rs": PasteRs,
    "del.dog": DelDog,
    "rentry": RentryCo,
    "filebin": FilebinNet,
    "gofile": GofileIo,
    "termbin": Termbin,
}

# Default fallback order (files)
FILE_FALLBACK_ORDER = [
    "tmpfiles.org",
    "litterbox",
    "uguu",
    "catbox",
    "gofile",
    "filebin",
]

# Default fallback order (text)
TEXT_FALLBACK_ORDER = [
    "paste.rs",
    "del.dog",
    "rentry",
    "termbin",
    "tmpfiles.org",
    "litterbox",
]
