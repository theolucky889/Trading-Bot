import argparse
import json
import sys
from datetime import datetime

# ✅ Local import (same folder)
from sentiment_analysis import analyze


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--num_articles", type=int, default=10)
    ap.add_argument("--model", default="vader")
    args = ap.parse_args()

    result = analyze(args.query, args.num_articles, args.model)

    # Ensure minimum fields exist (frontend expects these)
    result.setdefault("query", args.query)
    result.setdefault("model", args.model)
    result.setdefault("generated_at", datetime.utcnow().isoformat() + "Z")
    result.setdefault("summary", {})
    result["summary"].setdefault("positive", 0)
    result["summary"].setdefault("neutral", 0)
    result["summary"].setdefault("negative", 0)
    result["summary"].setdefault("avg_compound", 0)
    result.setdefault("articles", [])

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
