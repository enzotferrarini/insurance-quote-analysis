"""Generate immutable, deterministic JSON; no actual client or carrier data."""
import argparse
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
START = date(2025, 9, 1)
SNAPSHOT = date(2026, 8, 31)
TABLES = ('prospects', 'carriers', 'coverages', 'quotes', 'quote_coverages')


def generate(seed=42, prospects=100):
    if prospects < 1:
        raise ValueError('prospects must be positive')
    rng = random.Random(seed)
    rows = {table: [] for table in TABLES}
    rows['carriers'] = [dict(id=i, name='Fictional ' + name) for i, name in
                        enumerate(('Alder', 'Birch', 'Cedar', 'Elm', 'Maple', 'Willow'), 1)]
    rows['coverages'] = [dict(id=i, name=name, description='Synthetic coverage definition')
        for i, name in enumerate(('Auto liability', 'Collision', 'Dwelling',
                                  'Home liability', 'Umbrella liability'), 1)]
    for pid in range(1, prospects + 1):
        created = START + timedelta(days=rng.randrange((SNAPSHOT - START).days - 10))
        prospect = dict(id=pid, first_name='Demo', last_name=f'Prospect {pid:04}',
                        email=f'prospect{pid:04}@example.invalid', phone=None,
                        status='New', created_at=created.isoformat() + ' 09:00:00')
        rows['prospects'].append(prospect)
        if pid % 10 == 0:  # exact, documented unquoted segment
            continue
        product = rng.choices(['Auto', 'Home', 'Umbrella'], weights=[55, 30, 15])[0]
        quote_date = created + timedelta(days=rng.randrange(1, 8))
        effective = quote_date + timedelta(days=7)
        expiration = effective + timedelta(days=30)  # quote validity, not policy term
        base = {'Auto': 180000, 'Home': 260000, 'Umbrella': 50000}[product]
        base = int(base * rng.uniform(.7, 1.3))
        count = 4 if pid % 5 == 1 else rng.randint(2, 5)
        accepted_index = rng.randrange(count) if rng.random() < .45 else None
        carrier_ids = rng.sample(range(1, 7), count)
        for index, cid in enumerate(carrier_ids):
            qid = len(rows['quotes']) + 1
            status = rng.choices(['Pending', 'Presented', 'Declined', 'Expired'],
                                 weights=[15, 45, 25, 15])[0]
            if status == 'Expired' and expiration > SNAPSHOT:
                status = 'Presented'
            if index == accepted_index:
                status = 'Accepted'
            rows['quotes'].append(dict(id=qid, prospect_id=pid, carrier_id=cid,
                quote_type=product, premium_cents=int(base * rng.uniform(.8, 1.2)),
                effective_date=effective.isoformat(), expiration_date=expiration.isoformat(),
                status=status, created_at=quote_date.isoformat() + ' 10:00:00'))
            # Exactly three matching quotes for every designated prospect. Other
            # configurations vary by index; never assume same product means same cover.
            tier = 0 if pid % 5 == 1 and index < 3 else index + 1
            configs = {
                'Auto': [(1, 30000000 + tier * 5000000, None), (2, None, 50000 + tier * 25000)],
                'Home': [(3, 35000000 + tier * 5000000, 100000 + tier * 50000), (4, 30000000, None)],
                'Umbrella': [(5, 100000000 + tier * 100000000, None)],
            }
            for coverage, limit, deductible in configs[product]:
                rows['quote_coverages'].append(dict(quote_id=qid, coverage_id=coverage,
                    limit_cents=limit, deductible_cents=deductible,
                    notes='Synthetic terms; all exclusions assumed identical within configuration'))
        prospect['status'] = 'Accepted' if accepted_index is not None else 'Quoted'
    return dict(metadata=dict(seed=seed, prospect_count=prospects,
        start_date=START.isoformat(), snapshot_date=SNAPSHOT.isoformat(),
        synthetic=True, generator_version=1, currency='USD', premium_unit='annualized cents'), tables=rows)


def save_raw(payload, output):
    """Never overwrite raw data; identical reruns reuse it, changed inputs fail."""
    output = Path(output)
    content = json.dumps(payload, indent=2, sort_keys=True) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open('x') as file:
            file.write(content)
    except FileExistsError:
        if output.read_text() != content:
            raise FileExistsError(f'{output} differs; choose a new output directory')
    return hashlib.sha256(content.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--prospects', type=int, default=100)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/demo/raw.json')
    args = parser.parse_args()
    print(save_raw(generate(args.seed, args.prospects), args.output))


if __name__ == '__main__':
    main()
