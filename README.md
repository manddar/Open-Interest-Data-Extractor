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
python main.py                  # both indices, table output
python main.py -s nifty         # NIFTY only
python main.py -s banknifty     # BANKNIFTY only
python main.py -n 8             # 8 strikes above/below ATM (overrides default)
python main.py --json           # raw JSON output (pipe to jq, etc.)
python main.py --json --pretty  # indented JSON
python main.py --no-color       # plain text, no ANSI codes
python main.py --help           # full flag reference
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `-s`, `--symbol` | `both` | Index to fetch: `nifty`, `banknifty`, or `both` |
| `-n`, `--strikes` | *per-index* | Number of strikes above/below ATM (Nifty: 5, BNF: 10) |
| `--json` | off | Output raw JSON instead of the coloured table |
| `--pretty` | off | Indent JSON output (only with `--json`) |
| `--no-color` | off | Strip ANSI colour codes from terminal output |

### Example: pipe JSON into another tool

```bash
python main.py -s nifty --json --pretty | jq '.data[0].rows[:3]'
python main.py --json | python -c "
import sys, json
data = json.load(sys.stdin)
for idx in data['data']:
    print(idx['symbol'], sum(r['ce_oi'] + r['pe_oi'] for r in idx['rows']))
"
```

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
| ✅ CLI arguments | `--symbol`, `--strikes`, `--json`, `--pretty`, `--no-color` via `argparse`. |
| ✅ JSON output | `--json` flag dumps raw option-chain data as JSON for pipelines. |

## Credits

Inspired by [VarunS2002](https://github.com/VarunS2002/)'s
[Python-NSE-Option-Chain-Analyzer](https://github.com/VarunS2002/Python-NSE-Option-Chain-Analyzer).
