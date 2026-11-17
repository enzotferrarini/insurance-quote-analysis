"""Create a NEW demo DB, validate it, and export auditable analytical tables."""
import argparse
import csv
from datetime import date, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sqlite3

from src.generate_demo_data import ROOT, TABLES, generate, save_raw

FILTERS = dict(carrier_id=None, product=None, month=None)


def query(conn, name, **filters):
    return conn.execute((ROOT / 'sql' / name).read_text(), {**FILTERS, **filters})


def load_database(payload, path):
    """Exclusive creation; even an unrelated empty existing file is never replaced."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb'):
        pass
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute('PRAGMA foreign_keys = ON')
        conn.executescript((ROOT / 'schema.sql').read_text())
        with conn:
            for table in TABLES:
                for row in payload['tables'][table]:
                    columns = ','.join('"' + col + '"' for col in row)
                    placeholders = ','.join('?' for _ in row)
                    conn.execute(f'INSERT INTO {table} ({columns}) VALUES ({placeholders})', tuple(row.values()))
            conn.execute('CREATE TABLE analytics_snapshot (start_date TEXT NOT NULL, snapshot_date TEXT NOT NULL)')
            conn.execute('INSERT INTO analytics_snapshot VALUES (?,?)',
                         (payload['metadata']['start_date'], payload['metadata']['snapshot_date']))
        conn.executescript((ROOT / 'sql/00_views.sql').read_text())
        return conn
    except Exception:
        conn.close()
        path.unlink()  # only the file exclusively created by this call
        raise


def validate(conn, payload):
    checks = []

    def check(name, expected, actual):
        checks.append(dict(check=name, expected=str(expected), actual=str(actual),
                           result='PASS' if expected == actual else 'FAIL'))

    check('Foreign keys enabled on loader connection', 1, conn.execute('PRAGMA foreign_keys').fetchone()[0])
    check('Unmatched foreign keys', 0, len(conn.execute('PRAGMA foreign_key_check').fetchall()))
    check('SQLite integrity', 'ok', conn.execute('PRAGMA integrity_check').fetchone()[0])
    for table in TABLES:
        check(f'{table}: loaded vs raw count', len(payload['tables'][table]),
              conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0])
        keys = 'quote_id, coverage_id' if table == 'quote_coverages' else 'id'
        check(f'{table}: duplicate keys', 0, conn.execute(
            f'SELECT COUNT(*) FROM (SELECT {keys} FROM {table} GROUP BY {keys} HAVING COUNT(*) > 1)').fetchone()[0])
        required = [r[1] for r in conn.execute(f'PRAGMA table_info({table})') if r[3]]
        if required:
            clause = ' OR '.join(f'"{c}" IS NULL' for c in required)
            check(f'{table}: missing required fields', 0,
                  conn.execute(f'SELECT COUNT(*) FROM {table} WHERE {clause}').fetchone()[0])
    check('Invalid quote status', 0, conn.execute("SELECT COUNT(*) FROM quotes WHERE status NOT IN ('Pending','Presented','Accepted','Declined','Expired')").fetchone()[0])
    check('Invalid prospect status', 0, conn.execute("SELECT COUNT(*) FROM prospects WHERE status NOT IN ('New','Quoting','Quoted','Accepted','Declined')").fetchone()[0])
    check('Invalid product', 0, conn.execute("SELECT COUNT(*) FROM quotes WHERE quote_type NOT IN ('Auto','Home','Umbrella')").fetchone()[0])
    check('Invalid premium cents', 0, conn.execute("SELECT COUNT(*) FROM quotes WHERE premium_cents < 0 OR typeof(premium_cents) != 'integer'").fetchone()[0])
    check('Invalid coverage cents', 0, conn.execute("SELECT COUNT(*) FROM quote_coverages WHERE (limit_cents IS NOT NULL AND (limit_cents < 0 OR typeof(limit_cents) != 'integer')) OR (deductible_cents IS NOT NULL AND (deductible_cents < 0 OR typeof(deductible_cents) != 'integer'))").fetchone()[0])
    start = date.fromisoformat(payload['metadata']['start_date'])
    snapshot = date.fromisoformat(payload['metadata']['snapshot_date'])
    invalid_dates = 0
    for row in conn.execute('SELECT q.*, p.created_at AS prospect_created FROM quotes q JOIN prospects p ON p.id=q.prospect_id'):
        try:
            created = datetime.fromisoformat(row['created_at']).date()
            prospect_created = datetime.fromisoformat(row['prospect_created']).date()
            effective = date.fromisoformat(row['effective_date'])
            expiry = date.fromisoformat(row['expiration_date']) if row['expiration_date'] else None
            valid = (start <= created <= snapshot and prospect_created <= created <= effective
                     and (expiry is None or effective <= expiry)
                     and (row['status'] != 'Expired' or (expiry is not None and expiry <= snapshot)))
            invalid_dates += not valid
        except (ValueError, TypeError):
            invalid_dates += 1
    check('Invalid quote dates / ordering / expired status', 0, invalid_dates)
    invalid_prospect_dates = 0
    for row in conn.execute('SELECT created_at FROM prospects'):
        try:
            invalid_prospect_dates += not (start <= datetime.fromisoformat(row[0]).date() <= snapshot)
        except (ValueError, TypeError):
            invalid_prospect_dates += 1
    check('Invalid prospect dates', 0, invalid_prospect_dates)
    check('One row per quote in analytical view', conn.execute('SELECT COUNT(*) FROM quotes').fetchone()[0],
          conn.execute('SELECT COUNT(*) FROM analytics_quotes').fetchone()[0])
    for row in conn.execute('SELECT id, premium_cents, annual_premium_usd FROM analytics_quotes ORDER BY id LIMIT 5'):
        check(f'Quote {row[0]}: cents to USD', f'{Decimal(row[1]) / 100:.2f}', f'{row[2]:.2f}')
    return checks


def write_csv(path, cursor):
    with Path(path).open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([col[0] for col in cursor.description])
        writer.writerows(cursor.fetchall())


def export(conn, output):
    output.mkdir(parents=True, exist_ok=True)
    for sql in sorted((ROOT / 'sql').glob('0[1-6]_*.sql')):
        write_csv(output / (sql.stem + '.csv'), query(conn, sql.name))
    for name, sql in {
        'Quotes': 'SELECT * FROM analytics_quotes ORDER BY id',
        'Prospects': 'SELECT p.*, a.quote_count, a.has_accepted_quote FROM prospects p JOIN analytics_prospects a ON p.id=a.prospect_id ORDER BY p.id',
        'Carriers': 'SELECT * FROM carriers ORDER BY id',
        'QuoteCoverages': 'SELECT * FROM quote_coverages ORDER BY quote_id, coverage_id',
        'Coverages': 'SELECT * FROM coverages ORDER BY id',
        'Snapshot': 'SELECT * FROM analytics_snapshot',
    }.items():
        write_csv(output / f'{name}.csv', conn.execute(sql))
    write_csv(output / 'ComparableQuotes.csv', query(conn, '05_comparable_premiums.sql'))
    start, end = conn.execute('SELECT * FROM analytics_snapshot').fetchone()
    current, last = date.fromisoformat(start), date.fromisoformat(end)
    with (output / 'Date.csv').open('w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'year', 'month_number', 'year_month', 'is_complete_month'])
        while current <= last:
            next_month = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
            writer.writerow([current, current.year, current.month, current.strftime('%Y-%m'),
                             int(next_month - timedelta(days=1) <= last and current.replace(day=1) >= date.fromisoformat(start))])
            current += timedelta(days=1)


def run(output, seed=42, prospects=100):
    output = Path(output)
    payload = generate(seed, prospects)
    # Refuse before changing raw data or reports on any rerun targeting an existing DB.
    db = output / 'insurance_demo.db'
    if db.exists():
        raise FileExistsError(f'{db} already exists; use a new --output directory')
    digest = save_raw(payload, output / 'raw.json')
    conn = load_database(payload, db)
    try:
        checks = validate(conn, payload)
        (output / 'qa.json').write_text(json.dumps(checks, indent=2) + '\n')
        if any(row['result'] == 'FAIL' for row in checks):
            raise ValueError('Data validation failed; inspect qa.json')
        export(conn, output / 'processed')
        (output / 'manifest.json').write_text(json.dumps({**payload['metadata'],
            'raw_sha256': digest, 'row_counts': {k: len(v) for k, v in payload['tables'].items()}}, indent=2) + '\n')
    finally:
        conn.close()
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'data/demo')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--prospects', type=int, default=100)
    args = parser.parse_args()
    print(run(args.output, args.seed, args.prospects))


if __name__ == '__main__':
    main()
