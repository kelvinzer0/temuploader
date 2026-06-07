#!/usr/bin/env python3
"""
CLI interface for temuploader.
"""

import argparse
import sys
import os

from . import __version__
from .core import upload_file, upload_text, list_providers, zip_directory
from .providers import PROVIDERS, FILE_FALLBACK_ORDER, TEXT_FALLBACK_ORDER


def main():
    parser = argparse.ArgumentParser(
        prog="temuploader",
        description="Temporary file uploader with automatic fallback.",
        epilog="Examples:\n"
        "  temuploader myfile.txt                  # Upload file\n"
        "  temuploader ./my-folder                 # Upload folder (auto-zip)\n"
        "  echo 'hello' | temuploader -            # Upload from stdin\n"
        "  temuploader -t 'Hello world'             # Upload text directly\n"
        "  temuploader myfile.bin -p litterbox tmpfiles.org\n"
        "  temuploader --list                       # List providers\n"
        "  temuploader myfile.txt --json             # JSON output\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("source", nargs="?", help="File, folder, or '-' for stdin (folders are auto-zipped)")
    parser.add_argument("-t", "--text", help="Upload text directly")
    parser.add_argument(
        "-p",
        "--providers",
        nargs="+",
        help=f"Providers to try (default: auto). Available: {', '.join(PROVIDERS.keys())}",
    )
    parser.add_argument(
        "--no-fallback", action="store_true", help="Don't try fallback providers"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--download-url", action="store_true", help="Output only the download URL"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-l", "--list", action="store_true", help="List providers")
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    # Provider-specific options
    parser.add_argument(
        "--time", default="72h", help="Retention time for litterbox (24h/72h/1w)"
    )

    args = parser.parse_args()

    # List providers
    if args.list:
        providers = list_providers()
        print(
            f"\n{'Provider':<25} {'Max Size':>10} {'Retention':<12} {'Binary':>8} {'Text':>6}"
        )
        print("─" * 65)
        for name, info in providers.items():
            binary = "✓" if info["supports_binary"] else "✗"
            text = "✓" if info["supports_text"] else "✗"
            print(
                f"{name:<25} {info['max_size_mb']:>8}MB {info['retention']:<12} {binary:>8} {text:>6}"
            )
        print(f"\nDefault file order: {' → '.join(FILE_FALLBACK_ORDER)}")
        print(f"Default text order: {' → '.join(TEXT_FALLBACK_ORDER)}")
        return

    # Validate input
    if not args.source and not args.text:
        parser.print_help()
        sys.exit(1)

    # Build kwargs
    kwargs = {}
    if args.time:
        kwargs["time"] = args.time

    try:
        if args.text:
            # Upload text
            if args.verbose:
                print(f"📤 Uploading text ({len(args.text)} bytes)...")
            result = upload_text(
                args.text,
                providers=args.providers,
                fallback=not args.no_fallback,
                verbose=args.verbose,
                **kwargs,
            )
        elif args.source == "-":
            # Read from stdin
            text = sys.stdin.read()
            if args.verbose:
                print(f"📤 Uploading from stdin ({len(text)} bytes)...")
            result = upload_text(
                text,
                providers=args.providers,
                fallback=not args.no_fallback,
                verbose=args.verbose,
                **kwargs,
            )
        else:
            # Upload file or directory
            if not os.path.exists(args.source):
                print(f"✗ Not found: {args.source}", file=sys.stderr)
                sys.exit(1)

            tmp_zip = None
            upload_path = args.source

            if os.path.isdir(args.source):
                # Directory → zip first
                tmp_zip = zip_directory(args.source, verbose=args.verbose)
                upload_path = tmp_zip
                if args.verbose:
                    size = os.path.getsize(upload_path)
                    print(f"📤 Uploading zipped folder {args.source} ({size} bytes)...")
            else:
                if args.verbose:
                    size = os.path.getsize(args.source)
                    print(f"📤 Uploading {args.source} ({size} bytes)...")

            try:
                result = upload_file(
                    upload_path,
                    providers=args.providers,
                    fallback=not args.no_fallback,
                    verbose=args.verbose,
                    **kwargs,
                )
            finally:
                # Cleanup temp zip if we created one
                if tmp_zip and os.path.exists(tmp_zip):
                    os.unlink(tmp_zip)

        # Output
        if args.json:
            import json

            print(
                json.dumps(
                    {
                        "url": result.url,
                        "download_url": result.download_url,
                        "provider": result.provider,
                    },
                    indent=2,
                )
            )
        elif args.download_url:
            print(result.download_url)
        else:
            print(f"\n  ✓ Uploaded via {result.provider}")
            print(f"  URL: {result.url}")
            if result.url != result.download_url:
                print(f"  Download: {result.download_url}")
            print()

    except Exception as e:
        if args.verbose:
            import traceback

            traceback.print_exc()
        else:
            print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
