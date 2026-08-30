import ipaddress
import socket
from urllib.parse import urlparse
from app.core.exceptions import BaseAppException


class SSRFVulnerabilityException(BaseAppException):
    """Exception raised when a URL targets a restricted/private network or non-HTTP scheme."""

    def __init__(self, message: str = "Access to the requested URL is restricted for security reasons") -> None:
        super().__init__(message=message, status_code=400)


def validate_url_against_ssrf(url: str) -> str:
    """
    Validates a URL against Server-Side Request Forgery (SSRF) vulnerabilities.
    
    Checks:
    - Valid URL syntax and scheme (http / https only)
    - Rejects localhost / loopback / local hostnames
    - Resolves hostname to IP addresses and rejects private, link-local, loopback, or multicast IPs.
    """
    if not url or not isinstance(url, str):
        raise SSRFVulnerabilityException("Invalid URL provided")

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as exc:
        raise SSRFVulnerabilityException(f"Invalid URL format: {exc}")

    # Enforce HTTP/HTTPS schemes
    if parsed.scheme.lower() not in ("http", "https"):
        raise SSRFVulnerabilityException(f"Unsupported scheme '{parsed.scheme}'. Only http and https are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFVulnerabilityException("URL missing hostname")

    hostname_lower = hostname.lower()

    # Block common local hostnames
    if hostname_lower in ("localhost", "loopback", "127.0.0.1", "::1", "0.0.0.0"):
        raise SSRFVulnerabilityException("Access to local/loopback endpoints is prohibited.")

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        raise SSRFVulnerabilityException("Access to internal domains is prohibited.")

    # Resolve IP address and check ranges
    try:
        # Get all address info
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise SSRFVulnerabilityException(f"Unable to resolve hostname '{hostname}': {exc}")

    for family, socktype, proto, canonname, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
        except ValueError:
            raise SSRFVulnerabilityException(f"Invalid IP address resolved: {ip_str}")

        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or (ip_obj.is_reserved and not ip_str.startswith("64:ff9b:"))
            or ip_obj.is_unspecified
        ):
            raise SSRFVulnerabilityException(
                f"Resolved IP address '{ip_str}' is in a restricted or private range."
            )

    return url
