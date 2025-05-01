import yaml, json, subprocess, datetime, os, requests
import gspread, google.auth

cfg = yaml.safe_load(open("config.yml", encoding="utf-8"))
since = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()

rows, ping = [], []
def run(cmd): return subprocess.check_output(cmd, shell=True, text=True).splitlines()
def keep(line):
    t = json.loads(line)
    if t["likeCount"]>=cfg["min_likes"] and t["retweetCount"]>=cfg["min_retweets"]:
        rows.append([t["date"][:10], t["user"]["username"], t["content"][:150],
                     t["likeCount"], t["url"]])
        ping.append(f'❤️{t["likeCount"]} {t["url"]}')

for a in cfg["accounts"]:
    for l in run(f"snscrape --jsonl --since {since} twitter-user {a}"): keep(l)
for q in cfg["keywords"]:
    for l in run(f"snscrape --jsonl --since {since} twitter-search \"{q}\" --max-results {cfg['max_results_per_query']}"): keep(l)

if rows:
    creds,_ = google.auth.default(scopes=[
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive"])
    gspread.authorize(creds).open("AnimePainDB").sheet1.append_rows(rows, value_input_option="RAW")

if ping and os.getenv("SLACK_WEBHOOK"):
    requests.post(os.environ["SLACK_WEBHOOK"], json={"text":"\n".join(ping)}, timeout=10)
