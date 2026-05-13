# Open-Interest-Data-Extractor

Fetches the NIFTY & BANKNIFTY option chain from the NSE India website and
displays Open Interest in a colour-coded console table.

![Sample output](https://raw.githubusercontent.com/manddar/Open-Interest-Data-Extractor/main/Screenshot.png)

## Setup

```bash
pip install requests
```

> **VPN users:** NSE blocks requests from non-Indian IPs. Disable your VPN
> before running, or use an Indian exit node.

## Usage

```bash
python main.py
```

### What you'll see

```
----------------------------------------------------------------------
Purple      => Last Price: 12345 Nearest Strike: 12350
----------------------------------------------------------------------
Expiry      => 30MAY2026
----------------------------------------------------------------------
   12350 CE [     123,456 ] PE [     789,012 ]
   12400 CE [      98,765 ] PE [     654,321 ]
   ...
```

- **CE OI** is shown in green, **PE OI** in red — quick comparison at a glance.
- Open Interest values are comma-formatted for readability.

## What's Changed

This branch addresses the original TODOs and a few bugs:

| Fix | Description |
|-----|-------------|
| ✅ Cookie jar bug | Removed the unused manual `cookies` dict that shadowed the global — `requests.Session()` now handles cookies automatically. |
| ✅ 401 retry | Retries the *correct* URL when a session expires, not a hardcoded NIFTY URL. |
| ✅ Error handling | Network errors, HTTP failures, and bad JSON are caught and reported instead of crashing. |
| ✅ Code structure | Data fetching (`fetch_json`) is separated from display (`print_oi_table`), making the code testable and reusable. |
| ✅ Colour helpers | Replaced 10 near-identical functions with a 3-line dict + single `c()` function. |
| ✅ `if __name__` guard | The script can now be imported without executing. |
| ✅ Globals declared | Module-level variables are explicitly declared. |
| ✅ OI formatting | Values now display with comma separators (e.g., `123,456`). |
| ✅ Named constants | `num_strikes=5`, `step=50` are keyword arguments instead of magic numbers. |

### Still TODO

- JSON output mode (`--json` flag)
- CLI argument parsing for symbol selection and row count

## Credits

Inspired by [VarunS2002](https://github.com/VarunS2002/)'s
[Python-NSE-Option-Chain-Analyzer](https://github.com/VarunS2002/Python-NSE-Option-Chain-Analyzer).
