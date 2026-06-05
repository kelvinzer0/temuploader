"""
Core upload logic with fallback mechanism.
"""

import os
import tempfile
from typing import Optional, List, Union
from .providers import (
    PROVIDERS, FILE_FALLBACK_ORDER, TEXT_FALLBACK_ORDER,
    BaseProvider, UploadResult, ProviderError
)


def list_providers() -> dict:
    """List all available providers with their metadata."""
    result = {}
    for name, cls in PROVIDERS.items():
        p = cls()
        result[name] = {
            "name": p.name,
            "max_size_mb": p.max_size_mb,
            "retention": p.retention,
            "supports_binary": p.supports_binary,
            "supports_text": p.supports_text,
        }
    return result


def get_provider(name: str, **kwargs) -> BaseProvider:
    """Get a specific provider instance by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Available: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)


def _get_file_size(filepath: str) -> int:
    return os.path.getsize(filepath)


def _is_text_file(filepath: str) -> bool:
    """Heuristic: check if file is text-based."""
    text_exts = {'.txt', '.md', '.py', '.js', '.ts', '.json', '.yaml', '.yml',
                 '.toml', '.xml', '.html', '.css', '.sh', '.bash', '.zsh',
                 '.rb', '.go', '.rs', '.java', '.c', '.cpp', '.h', '.hpp',
                 '.conf', '.cfg', '.ini', '.env', '.log', '.csv', '.sql'}
    ext = os.path.splitext(filepath)[1].lower()
    if ext in text_exts:
        return True
    # Try reading first bytes
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)
            # If mostly printable, it's text
            text_chars = sum(1 for b in chunk if b < 128 and (b >= 32 or b in (9, 10, 13)))
            return text_chars / max(len(chunk), 1) > 0.9
    except:
        return False


def upload(
    source: str,
    is_text: bool = None,
    providers: List[str] = None,
    fallback: bool = True,
    verbose: bool = False,
    **kwargs,
) -> UploadResult:
    """
    Upload a file or text content with automatic fallback.

    Args:
        source: File path (str) or text content (str starting with content)
        is_text: Force text mode. Auto-detected if None.
        providers: List of provider names to try. None = use defaults.
        fallback: If True, try next provider on failure.
        verbose: Print status messages.
        **kwargs: Extra args passed to provider (e.g. time="72h" for litterbox)

    Returns:
        UploadResult with url and download_url

    Raises:
        ProviderError: If all providers fail.
    """
    # Determine if source is a file path or text content
    is_file = os.path.isfile(source)

    if is_file:
        return upload_file(source, is_text=is_text, providers=providers,
                          fallback=fallback, verbose=verbose, **kwargs)
    else:
        return upload_text(source, providers=providers,
                          fallback=fallback, verbose=verbose, **kwargs)


def upload_file(
    filepath: str,
    is_text: bool = None,
    providers: List[str] = None,
    fallback: bool = True,
    verbose: bool = False,
    **kwargs,
) -> UploadResult:
    """
    Upload a file with automatic fallback.

    Args:
        filepath: Path to file.
        is_text: Force text mode. Auto-detected if None.
        providers: Provider names to try. None = auto-select based on file type.
        fallback: Try next provider on failure.
        verbose: Print status.
        **kwargs: Extra provider args.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Auto-detect text vs binary
    if is_text is None:
        is_text = _is_text_file(filepath)

    # Select provider order
    if providers is None:
        providers = TEXT_FALLBACK_ORDER if is_text else FILE_FALLBACK_ORDER

    # Filter providers that support this file type
    valid_providers = []
    for name in providers:
        if name not in PROVIDERS:
            if verbose:
                print(f"  ⚠ Unknown provider: {name}, skipping")
            continue
        p = PROVIDERS[name]()
        if is_text and not p.supports_text:
            if verbose:
                print(f"  ⚠ {name} doesn't support text, skipping")
            continue
        if not is_text and not p.supports_binary:
            if verbose:
                print(f"  ⚠ {name} doesn't support binary files, skipping")
            continue
        # Check size limit
        size_mb = _get_file_size(filepath) / (1024 * 1024)
        if size_mb > p.max_size_mb:
            if verbose:
                print(f"  ⚠ {name}: file too large ({size_mb:.1f}MB > {p.max_size_mb}MB), skipping")
            continue
        valid_providers.append(name)

    if not valid_providers:
        raise ProviderError("No suitable providers available for this file")

    return _try_providers(filepath, valid_providers, fallback, verbose, **kwargs)


def upload_text(
    text: str,
    providers: List[str] = None,
    fallback: bool = True,
    verbose: bool = False,
    **kwargs,
) -> UploadResult:
    """
    Upload text content with automatic fallback.

    Args:
        text: Text content to upload.
        providers: Provider names to try. None = use text defaults.
        fallback: Try next provider on failure.
        verbose: Print status.
        **kwargs: Extra provider args.
    """
    if providers is None:
        providers = TEXT_FALLBACK_ORDER

    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(text)
        tmp = f.name

    try:
        valid_providers = []
        for name in providers:
            if name not in PROVIDERS:
                continue
            p = PROVIDERS[name]()
            if not p.supports_text:
                continue
            valid_providers.append(name)

        if not valid_providers:
            raise ProviderError("No suitable text providers available")

        return _try_providers(tmp, valid_providers, fallback, verbose, **kwargs)
    finally:
        os.unlink(tmp)


def _try_providers(
    filepath: str,
    provider_names: List[str],
    fallback: bool,
    verbose: bool,
    **kwargs,
) -> UploadResult:
    """Try providers in order with fallback. kwargs are passed to providers that accept them."""
    errors = []

    for name in provider_names:
        # Only pass kwargs to providers that accept them (e.g. Litterbox takes 'time')
        import inspect
        try:
            cls = PROVIDERS[name]
            sig = inspect.signature(cls.__init__)
            # Filter kwargs to only those accepted by this provider
            accepted = {k: v for k, v in kwargs.items() if k in sig.parameters and k != 'self'}
            provider = cls(**accepted)
        except (TypeError, ValueError):
            provider = cls()

        if verbose:
            print(f"  → Trying {provider.name}...")

        try:
            result = provider.upload(filepath)
            if verbose:
                print(f"  ✓ {provider.name}: {result.download_url}")
            return result
        except (ProviderError, Exception) as e:
            errors.append((name, str(e)))
            if verbose:
                print(f"  ✗ {provider.name}: {e}")
            if not fallback:
                raise ProviderError(f"Provider {name} failed: {e}")

    # All failed
    error_summary = "\n".join(f"  - {name}: {err}" for name, err in errors)
    raise ProviderError(f"All providers failed:\n{error_summary}")


def quick_share(text: str, **kwargs) -> str:
    """
    One-liner: upload text, return URL string.
    Perfect for piping and quick sharing.
    """
    result = upload_text(text, **kwargs)
    return result.download_url


def quick_file(filepath: str, **kwargs) -> str:
    """
    One-liner: upload file, return download URL string.
    """
    result = upload(filepath, **kwargs)
    return result.download_url
