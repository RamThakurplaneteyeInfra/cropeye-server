#!/usr/bin/env python3
"""
Filter script to remove health check requests from Gunicorn access logs.
This script reads from stdin and filters out lines containing /api/health/
"""
import sys
import re

# Pattern to match health check requests in access logs
HEALTH_CHECK_PATTERNS = [
    r'/api/health/',
    r'GET /api/health/',
    r'"GET /api/health/',
    r'"GET.*/api/health/',
    r'curl.*health',
    r'127\.0\.0\.1.*health',  # Docker health checks from localhost
]

def is_health_check(line):
    """Check if a log line is a health check request."""
    # Only check access log lines (not error logs or other output)
    # Access logs typically have IP addresses and HTTP methods
    if not (re.search(r'\d+\.\d+\.\d+\.\d+', line) or 'HTTP' in line.upper()):
        # Not an access log line, pass through
        return False
    
    line_lower = line.lower()
    for pattern in HEALTH_CHECK_PATTERNS:
        if re.search(pattern, line_lower, re.IGNORECASE):
            return True
    return False

def main():
    """Main function to filter health check logs."""
    try:
        for line in sys.stdin:
            # Only filter access log lines that are health checks
            # Pass through error logs and other output
            if not is_health_check(line):
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        # If filtering fails, pass through all logs to avoid breaking the server
        sys.stderr.write(f"Filter error: {e}\n")
        try:
            for line in sys.stdin:
                sys.stdout.write(line)
                sys.stdout.flush()
        except:
            pass

if __name__ == '__main__':
    main()

