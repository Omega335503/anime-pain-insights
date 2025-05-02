import yaml, json, subprocess, datetime, os, ssl, requests, certifi
import gspread, google.auth

# ── SSL 回避設定 ───────────────────────────
os.environ["SSL_CERT_FILE"] = certifi.where()                 # certifi ルート
ssl._create_default_https_context = ssl._create_unverified_context  # 検証オフ
# ────────────────────────────────────────

cfg   = yaml.safe_load(open("config.yml", encoding="utf-8"))
since = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
rows, ping = [], []

def run(cmd: str):
    return subprocess.check_output(cmd, shell=True, text=True).splitlines()

def keep(line: str):
    t = json.loads(line)
    if t["likeCount"] >= cfg["min_likes"] and t["retweetCount"] >= cfg["min_retweets"]:
        rows.append([
            t["date"][:10],
            t["user"]["username"],
            t["content"][:150],
            t["likeCount"],
            t["url"],
        ])
        ping.append(f'❤️{t["likeCount"]} {t["url"]}')

# ---------- snscrape 呼び出し（Nitter ミラー経由） ----------
ROOT = "https://nitter.net"

for a in cfg["accounts"]:
    cmd = f"snscrape --jsonl --root-url {ROOT} --since {since} twitter-user {a}"
    for l in run(cmd):
        keep(l)

for q in cfg["keywords"]:
    cmd = (
        f'snscrape --jsonl --root-url {ROOT} --since {since} '
        f'twitter-search "{q}" --max-results {cfg["max_results_per_query"]}'
    )
    for l in run(cmd):
        keep(l)
# ------------------------------------------------------------

# Sheets へ書き込み
if rows:
    creds, _ = google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
    )
    gspread.authorize(creds).open("AnimePainDB").sheet1.append_rows(
        rows, value_input_option="RAW"
    )

# Slack 通知
if ping and os.getenv("SLACK_WEBHOOK"):
    requests.post(os.environ["SLACK_WEBHOOK"], json={"text": "\n".join(ping)}, timeout=10)
