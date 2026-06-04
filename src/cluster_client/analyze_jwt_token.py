#!/usr/bin/env python3
"""
Debug script to analyze JWT token segments and structure.
"""

import base64
import json
import sys


def analyze_jwt_token(token: str) -> None:
    """
    Analyze a JWT token and print detailed information about its segments.

    Args:
        token: The JWT token string to analyze
    """
    print(f"Token: {token}")
    print(f"Token length: {len(token)} characters")
    print()

    # Split by dots
    segments = token.split(".")
    print(f"Number of segments: {len(segments)}")
    print()

    if len(segments) != 3:
        print(f"⚠️  WARNING: JWT should have exactly 3 segments, found {len(segments)}")
        print()

    # Analyze each segment
    for i, segment in enumerate(segments):
        segment_name = ["Header", "Payload", "Signature"][i] if i < 3 else f"Extra-{i}"
        print(f"Segment {i + 1} ({segment_name}):")
        print(f"  Length: {len(segment)} characters")
        print(f"  Content: {segment[:50]}{'...' if len(segment) > 50 else ''}")

        # Try to decode if it's header or payload (not signature)
        if i < 2:
            try:
                # Add padding if needed
                padding = 4 - (len(segment) % 4)
                if padding != 4:
                    padded = segment + ("=" * padding)
                else:
                    padded = segment

                decoded = base64.urlsafe_b64decode(padded)
                decoded_json = json.loads(decoded)
                print("  Decoded JSON:")
                print(f"    {json.dumps(decoded_json, indent=4)}")
            except Exception as e:
                print(f"  ⚠️  Could not decode: {e}")
        print()

    # Check for common issues
    print("Validation checks:")

    # Check for whitespace
    if token != token.strip():
        print("  ⚠️  Token contains leading/trailing whitespace")

    # Check for newlines
    if "\n" in token or "\r" in token:
        print("  ⚠️  Token contains newline characters")

    # Check for spaces
    if " " in token:
        print("  ⚠️  Token contains space characters")

    # Check segment count
    if len(segments) == 3:
        print("  ✓ Token has correct number of segments (3)")
    else:
        print(f"  ✗ Token has {len(segments)} segments (expected 3)")

    # Check for empty segments
    for i, segment in enumerate(segments):
        if not segment:
            print(f"  ✗ Segment {i + 1} is empty")

    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python debug_token_segments.py <jwt_token>")
        print()
        print("Example:")
        print("  python debug_token_segments.py 'eyJhbGci...token...here'")
        sys.exit(1)

    token = sys.argv[1]
    analyze_jwt_token(token)


if __name__ == "__main__":
    main()

# Made with Bob
