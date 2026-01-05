import argparse
import os
import sys
from pathlib import Path

import django


def _setup_django():
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = repo_root / "backend"
    sys.path.insert(0, str(backend_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def main():
    parser = argparse.ArgumentParser(description="Update AlgoSkill RELATED edges by co-occurrence.")
    parser.add_argument("--min-co", type=int, default=5)
    parser.add_argument("--pmi-threshold", type=float, default=0.0)
    parser.add_argument("--sigmoid-scale", type=float, default=1.0)
    parser.add_argument("--include-reports", action="store_true", default=True)
    parser.add_argument("--exclude-reports", action="store_false", dest="include_reports")
    args = parser.parse_args()

    _setup_django()

    from graph_sync.algo_similarity import update_algo_similarity

    count = update_algo_similarity(
        min_cooccurrence=args.min_co,
        pmi_threshold=args.pmi_threshold,
        sigmoid_scale=args.sigmoid_scale,
        include_reports=args.include_reports,
    )
    print(f"[algo_similarity] updated edges: {count}")

if __name__ == "__main__":
    main()
