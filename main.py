import argparse
import json
import math
import sys

import requests

# ── Colour helpers ───────────────────────────────────────────────
_COLORS = {
    "red": 91, "green": 92, "yellow": 93, "lpurple": 94,
    "purple": 95, "cyan": 96, "lgray": 97, "black": 98, "bold": 1,
}

_ENABLED = True  # toggled off by --no-color / piped output


def c(name: str, text: str) -> str:
    """Return *text* wrapped in the ANSI colour *name*."""
    if not _ENABLED:
        return text
    code = _COLORS.get(name)
    if code is None:
        return text
    return f"\033[{code}m{text}\033[0m"


def bold(text: str) -> str:
    return c("bold", text)


# ── Strike-rounding helpers ──────────────────────────────────────
def round_nearest(x: float, num: int = 50) -> int:
    return int(math.ceil(float(x) / num) * num)


def nearest_strike_bnf(x: float) -> int:
    return round_nearest(x, 100)


def nearest_strike_nf(x: float) -> int:
    return round_nearest(x, 50)


# ── NSE API constants ────────────────────────────────────────────
BASE_OC_URL = "https://www.nseindia.com/option-chain"
URL_BNF = "https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY"
URL_NF = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
URL_INDICES = "https://www.nseindia.com/api/allIndices"

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/80.0.3987.149 Safari/537.36"
    ),
    "accept-language": "en,gu;q=0.9,hi;q=0.8",
    "accept-encoding": "gzip, deflate, br",
}

# ── Session (cookie management is handled automatically) ─────────
_session = requests.Session()


def _prime_session() -> None:
    """Warm up the session so NSE sets initial cookies."""
    try:
        _session.get(BASE_OC_URL, headers=HEADERS, timeout=5)
    except requests.RequestException:
        pass  # best-effort; subsequent calls will retry


def fetch_json(url: str) -> dict | None:
    """Fetch *url* and return parsed JSON, or None on failure."""
    try:
        resp = _session.get(url, headers=HEADERS, timeout=5)
    except requests.RequestException as exc:
        print(c("red", f"[!] Network error: {exc}"), file=sys.stderr)
        return None

    if resp.status_code == 401:
        # Session may have expired — re-prime and retry once
        _prime_session()
        try:
            resp = _session.get(url, headers=HEADERS, timeout=5)
        except requests.RequestException as exc:
            print(c("red", f"[!] Network error on retry: {exc}"), file=sys.stderr)
            return None

    if resp.status_code != 200:
        print(
            c("red", f"[!] HTTP {resp.status_code} for {url}"),
            file=sys.stderr,
        )
        return None

    try:
        return resp.json()
    except json.JSONDecodeError as exc:
        print(c("red", f"[!] Invalid JSON response: {exc}"), file=sys.stderr)
        return None


# ── Index helpers ─────────────────────────────────────────────────
def fetch_indices() -> dict[str, tuple[float, int]]:
    """Return {label: (last_price, nearest_strike)} for NIFTY & BANKNIFTY."""
    data = fetch_json(URL_INDICES)
    if not data:
        return {}

    result: dict[str, tuple[float, int]] = {}
    for idx in data.get("data", []):
        if idx["index"] == "NIFTY 50":
            ul = idx["last"]
            result["Nifty"] = (ul, nearest_strike_nf(ul))
        elif idx["index"] == "NIFTY BANK":
            ul = idx["last"]
            result["Bank Nifty"] = (ul, nearest_strike_bnf(ul))
    return result


# ── Data layer ────────────────────────────────────────────────────
def collect_oi_data(
    url: str,
    nearest: int,
    num_strikes: int,
    step: int,
) -> list[dict] | None:
    """Fetch option-chain data and return a list of strike dicts.

    Each dict::
        {"strike": int, "ce_oi": int, "pe_oi": int, "expiry": str}
    Returns None on failure.
    """
    data = fetch_json(url)
    if not data:
        return None

    records = data.get("records", {})
    expiry_dates = records.get("expiryDates", [])
    if not expiry_dates:
        return None

    curr_expiry = expiry_dates[0]

    start_strike = nearest - (step * num_strikes)
    end_strike = start_strike + (step * num_strikes * 2)
    target_strikes = set(range(start_strike, end_strike, step))

    rows: list[dict] = []
    for item in records.get("data", []):
        if item.get("expiryDate") != curr_expiry:
            continue
        sp = item["strikePrice"]
        if sp not in target_strikes:
            continue
        rows.append({
            "strike": sp,
            "ce_oi": item.get("CE", {}).get("openInterest", 0),
            "pe_oi": item.get("PE", {}).get("openInterest", 0),
            "expiry": curr_expiry,
        })

    # sort ascending by strike
    rows.sort(key=lambda r: r["strike"])
    return rows


# ── Table display ─────────────────────────────────────────────────
def fmt_oi(value: int) -> str:
    """Format Open Interest with comma separators."""
    return f"{value:>12,}"


def print_header(label: str, last: float, nearest: int) -> None:
    print(c("purple", label.ljust(12, " ") + " => "), end="")
    print(
        c("lpurple", "Last Price: ")
        + bold(str(last))
        + c("lpurple", " Nearest Strike: ")
        + bold(str(nearest))
    )


def print_hr() -> None:
    print(c("yellow", "-".rjust(70, "-")))


def print_oi_table(
    label: str,
    last: float,
    nearest: int,
    rows: list[dict],
) -> None:
    """Print a coloured OI table from pre-fetched *rows*."""
    print_hr()
    print_header(label, last, nearest)
    print_hr()

    if not rows:
        print(c("red", f"[!] No data for {label}"), file=sys.stderr)
        return

    expiry = rows[0]["expiry"]
    print(c("purple", "Expiry".ljust(12, " ") + " =>  ") + c("lpurple", expiry))
    print_hr()

    for row in rows:
        print(
            c("cyan", str(row["strike"]).rjust(7))
            + c("green", " CE ")
            + "[ " + bold(fmt_oi(row["ce_oi"])) + " ]"
            + c("red", " PE ")
            + "[ " + bold(fmt_oi(row["pe_oi"])) + " ]"
        )


# ── Index config ──────────────────────────────────────────────────
INDEX_CONFIG = {
    "nifty": {
        "url": URL_NF,
        "label": "Nifty",
        "num_strikes": 5,
        "step": 50,
    },
    "banknifty": {
        "url": URL_BNF,
        "label": "Bank Nifty",
        "num_strikes": 10,
        "step": 100,
    },
}


# ── CLI ───────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fetch NSE option-chain Open Interest data.",
    )
    parser.add_argument(
        "-s", "--symbol",
        choices=["nifty", "banknifty", "both"],
        default="both",
        help="Index to fetch (default: both)",
    )
    parser.add_argument(
        "-n", "--strikes",
        type=int,
        default=None,
        help="Number of strikes above/below ATM (overrides per-index default)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON instead of the coloured table (implies --no-color)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Strip ANSI colour codes from output",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="When used with --json, indent the output",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    global _ENABLED
    if args.no_color or args.json:
        _ENABLED = False

    _prime_session()

    indices = fetch_indices()
    if not indices:
        print(c("red", "[!] Could not fetch index data. Exiting."), file=sys.stderr)
        sys.exit(1)

    # Pick which indices to process
    symbols = ["nifty", "banknifty"] if args.symbol == "both" else [args.symbol]

    # Collect data for each symbol
    all_data: list[dict] = []
    for sym in symbols:
        cfg = INDEX_CONFIG[sym]
        label = cfg["label"]
        ul, near = indices.get(label, (0, 0))
        if ul == 0:
            print(c("red", f"[!] Could not fetch spot price for {label}"), file=sys.stderr)
            continue

        num_strikes = args.strikes if args.strikes is not None else cfg["num_strikes"]

        rows = collect_oi_data(cfg["url"], near, num_strikes, cfg["step"])
        all_data.append({
            "symbol": label,
            "last_price": ul,
            "nearest_strike": near,
            "rows": rows or [],
        })

    # ── Output ────────────────────────────────────────────────
    if args.json:
        print(
            json.dumps(
                {"data": all_data},
                indent=2 if args.pretty else None,
                default=str,
            )
        )
        return

    # Table mode
    print("\033c", end="")  # clear screen
    for entry in all_data:
        print_oi_table(
            label=entry["symbol"],
            last=entry["last_price"],
            nearest=entry["nearest_strike"],
            rows=entry["rows"],
        )
        print_hr()


if __name__ == "__main__":
    main()
