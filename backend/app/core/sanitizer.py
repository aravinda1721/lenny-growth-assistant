"""
backend/app/core/sanitizer.py

Security sanitization for untrusted user/model-generated HTML artifacts.
Defense-in-depth: removes executable scripts, malicious event handlers, and data URLs
before artifacts are persisted or served to the client.
"""

import re

# Block dangerous tags
BLOCKED_TAGS = [
    r"<\s*script[^>]*>.*?<\s*/\s*script\s*>",
    r"<\s*script[^>]*>",
    r"<\s*/\s*script\s*>",
    r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>",
    r"<\s*object[^>]*>.*?<\s*/\s*object\s*>",
    r"<\s*embed[^>]*>",
    r"<\s*applet[^>]*>.*?<\s*/\s*applet\s*>"
]

# Block inline event handlers (onerror, onload, onclick, onmouseover, etc.)
EVENT_HANDLER_REGEX = re.compile(r"\s+on[a-zA-Z]+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE)
JAVASCRIPT_URI_REGEX = re.compile(r"href\s*=\s*['\"]javascript:[^'\"]*['\"]", re.IGNORECASE)

def sanitize_html_artifact(html_content: str) -> str:
    """
    Sanitizes HTML content by stripping executable script tags, event handlers,
    and javascript: protocol URIs.
    """
    if not html_content:
        return ""

    sanitized = html_content
    for pattern in BLOCKED_TAGS:
        sanitized = re.sub(pattern, "<!-- [Blocked Unsafe Element] -->", sanitized, flags=re.IGNORECASE | re.DOTALL)

    sanitized = EVENT_HANDLER_REGEX.sub(" data-blocked-event='' ", sanitized)
    sanitized = JAVASCRIPT_URI_REGEX.sub(" href='#' ", sanitized)

    return sanitized
