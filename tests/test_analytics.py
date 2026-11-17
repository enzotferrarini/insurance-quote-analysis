import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from src.generate_demo_data import ROOT, generate, save_raw, TABLES
from src.pipeline import load_database, query, run, validate


def fixture():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript((ROOT / 'schema.sql').read_text())
    conn.executescript((ROOT / 'tests/fixtures/hand_calculated.sql').read_text())
    payload = dict(metadata=dict(start_date='2026-01-01', snapshot_date='2026-02-28'),
                   tables={t: [dict(r) for r in conn.execute(f'SELECT * FROM {t}')] for t in TABLES})
    conn.execute('CREATE TABLE analytics_snapshot (start_date TEXT, snapshot_date TEXT)')
    conn.execute("INSERT INTO analytics_snapshot VALUES ('2026-01-01','2026-02-28')")
    conn.executescript((ROOT / 'sql/00_views.sql').read_text())
    return conn, payload


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.conn, self.payload = fixture()

    def tearDown(self):
        self.conn.close()

    def rows(self, name, **filters):
        return [dict(r) for r in query(self.conn, name, **filters)]

    def test_hand_calculated_five_questions(self):
        volume = self.rows('01_quote_volume.sql')
        self.assertEqual([r['quote_count'] for r in volume], [3, 2, 2, 1])
        options = self.rows('02_prospect_options.sql')[0]
        self.assertEqual(options, dict(quote_count=8, quoted_prospects=4, quotes_per_quoted_prospect=2.0))
        shares = self.rows('03_accepted_quote_share.sql')
        self.assertEqual([(r['accepted_quotes'],r['non_pending_quotes']) for r in shares], [(2,3),(1,3)])
        self.assertEqual(self.rows('04_accepted_prospect_share.sql')[0],
            dict(accepted_prospects=2,quoted_prospects=4,accepted_prospect_share=.5))
        compare = self.rows('05_comparable_premiums.sql')
        self.assertEqual([r['id'] for r in compare], [1,2])
        self.assertEqual([r['premium_rank'] for r in compare], [1,2])
        self.assertTrue(all(r['group_range_usd']==200 for r in compare))
        self.assertEqual(len(self.conn.execute('SELECT * FROM analytics_prospects').fetchall()), 5)

    def test_no_coverage_fanout(self):
        self.conn.execute("INSERT INTO coverages VALUES (3,'Extra','Fixture')")
        self.conn.execute("INSERT INTO quote_coverages VALUES (1,3,100,NULL,'Extra')")
        self.assertEqual(self.rows('02_prospect_options.sql')[0]['quote_count'],8)
        self.assertEqual(self.conn.execute('SELECT SUM(premium_cents) FROM analytics_quotes').fetchone()[0],1060000)
        self.assertEqual(self.rows('05_comparable_premiums.sql'), [])

    def test_notes_and_missing_coverage_prevent_equivalence(self):
        self.conn.execute("UPDATE quote_coverages SET notes='Excluded event' WHERE quote_id=2")
        self.assertEqual(self.rows('05_comparable_premiums.sql'), [])
        self.conn.execute('DELETE FROM quote_coverages WHERE quote_id IN (1,2)')
        self.assertEqual(self.rows('05_comparable_premiums.sql'), [])

    def test_null_not_same_as_zero_or_empty(self):
        self.conn.execute('UPDATE quote_coverages SET deductible_cents=0 WHERE quote_id=2 AND coverage_id=1')
        self.assertEqual(self.rows('05_comparable_premiums.sql'), [])
        self.conn.execute('UPDATE quote_coverages SET deductible_cents=NULL, notes=NULL WHERE quote_id=2 AND coverage_id=1')
        self.conn.execute("UPDATE quote_coverages SET notes='' WHERE quote_id=1 AND coverage_id=1")
        self.assertEqual(self.rows('05_comparable_premiums.sql'), [])

    def test_tied_premium_ranking(self):
        self.conn.execute('UPDATE quotes SET premium_cents=100000 WHERE id=2')
        self.assertEqual([r['premium_rank'] for r in self.rows('05_comparable_premiums.sql')],[1,1])

    def test_five_filter_scenarios(self):
        cases = [({},8,4,2), ({'carrier_id':1},5,3,2), ({'product':'Auto'},5,2,1),
                 ({'month':'2026-02'},3,2,1), ({'carrier_id':999},0,0,0)]
        for filters, quotes, prospects, accepted_prospects in cases:
            with self.subTest(filters=filters):
                self.assertEqual(self.rows('02_prospect_options.sql',**filters)[0]['quote_count'], quotes)
                p = self.rows('04_accepted_prospect_share.sql',**filters)[0]
                self.assertEqual(p['quoted_prospects'],prospects)
                self.assertEqual(p['accepted_prospects'],accepted_prospects)
        self.assertEqual(self.rows('05_comparable_premiums.sql',carrier_id=1),[])

    def test_empty_and_pending_only_denominators(self):
        self.assertIsNone(self.rows('04_accepted_prospect_share.sql',carrier_id=999)[0]['accepted_prospect_share'])
        self.assertIsNone(self.rows('02_prospect_options.sql',carrier_id=999)[0]['quotes_per_quoted_prospect'])
        self.conn.execute("UPDATE quotes SET status='Pending'")
        self.assertTrue(all(r['accepted_quote_share'] is None for r in self.rows('03_accepted_quote_share.sql')))

    def test_zero_months_and_complete_month_lag(self):
        trend=self.rows('06_monthly_trend.sql')
        self.assertEqual([r['quote_count'] for r in trend],[5,3])
        self.assertEqual(trend[1]['month_over_month_change'],-.4)
        self.assertEqual(self.rows('06_monthly_trend.sql',month='2026-02')[0]['previous_month_quotes'],5)
        self.conn.execute("UPDATE analytics_snapshot SET snapshot_date='2026-04-15'")
        self.assertEqual([r['quote_count'] for r in self.rows('06_monthly_trend.sql')],[5,3,0])
        self.conn.execute("UPDATE analytics_snapshot SET snapshot_date='2026-04-30'")
        self.assertIsNone(self.rows('06_monthly_trend.sql')[-1]['month_over_month_change'])

    def test_snapshot_cutoff(self):
        self.conn.execute("UPDATE analytics_snapshot SET snapshot_date='2026-01-31'")
        self.assertEqual(self.rows('02_prospect_options.sql')[0]['quote_count'],5)

    def test_clean_fixture_qa(self):
        self.assertTrue(all(r['result']=='PASS' for r in validate(self.conn,self.payload)))

    def test_invalid_fixture_rejected_or_flagged(self):
        for case in json.loads((ROOT/'tests/fixtures/invalid_cases.json').read_text()):
            with self.subTest(case=case['name']):
                conn,payload=fixture()
                try:
                    if case['constraint']:
                        with self.assertRaises(sqlite3.IntegrityError): conn.execute(case['sql'])
                    else:
                        conn.execute(case['sql'])
                        self.assertTrue(any(r['result']=='FAIL' for r in validate(conn,payload)))
                finally:
                    conn.close()


class PipelineTests(unittest.TestCase):
    def test_reproducible_and_seed_sensitive(self):
        self.assertEqual(generate(),generate())
        self.assertNotEqual(generate(),generate(seed=43))

    def test_raw_and_database_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'raw.json'
            save_raw(generate(),path)
            before=path.read_bytes()
            save_raw(generate(),path)
            with self.assertRaises(FileExistsError): save_raw(generate(seed=2),path)
            self.assertEqual(path.read_bytes(),before)
            db=Path(tmp)/'work.db'
            db.write_bytes(b'valuable work')
            with self.assertRaises(FileExistsError): load_database(generate(),db)
            self.assertEqual(db.read_bytes(),b'valuable work')

    def test_pipeline_roundtrip_and_rerun_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=run(Path(tmp)/'demo')
            self.assertTrue((out/'processed/Quotes.csv').exists())
            checks=json.loads((out/'qa.json').read_text())
            self.assertTrue(all(r['result']=='PASS' for r in checks))
            raw=(out/'raw.json').read_bytes()
            with self.assertRaises(FileExistsError): run(out)
            self.assertEqual(raw,(out/'raw.json').read_bytes())

    def test_scaled_generator(self):
        payload=generate(prospects=1000)
        self.assertEqual(len(payload['tables']['prospects']),1000)
        self.assertTrue(2000 < len(payload['tables']['quotes']) < 5000)


if __name__=='__main__': unittest.main()
