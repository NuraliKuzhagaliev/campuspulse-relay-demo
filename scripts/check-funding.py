import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relay.funding import validate_funding
from relay.domain import RelayError

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--record', default='.local/funding-verification.json')
    p.add_argument('--project', required=True)
    p.add_argument('--budget', required=True, type=float)
    p.add_argument('--hours', required=True, type=int)
    a = p.parse_args()
    try:
        print(json.dumps(validate_funding(json.loads(Path(a.record).read_text(encoding='utf-8-sig')), a.project, a.budget, a.hours)))
    except (OSError, ValueError, RelayError) as e:
        print(e.message if isinstance(e, RelayError) else 'A valid verified funding record is required.', file=sys.stderr)
        sys.exit(1)
