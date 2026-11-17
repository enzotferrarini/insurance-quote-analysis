"""Reconcile SQL with pandas, then generate a two-page static case report."""
import argparse
from html import escape
import json
import os
import re
from pathlib import Path
import sqlite3

from src.generate_demo_data import ROOT
from src.pipeline import query

os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import pandas as pd


def table(frame):
    return frame.to_html(index=False, border=0, classes='data', na_rep='—', float_format=lambda x:f'{x:,.2f}')


def reconcile(conn, quotes):
    cases = [('All quotes', {}), ('Fictional Alder', {'carrier_id':1}),
             ('Auto', {'product':'Auto'}), ('2026-08', {'month':'2026-08'}),
             ('No matching rows', {'carrier_id':999})]
    checks=[]
    for label,filters in cases:
        frame=quotes.copy()
        for key,value in filters.items():
            column={'product':'quote_type','month':'created_month'}.get(key,key)
            frame=frame[frame[column]==value]
        expected_quotes=len(frame)
        expected_prospects=frame.prospect_id.nunique()
        expected_accepted=frame.loc[frame.status.eq('Accepted'),'prospect_id'].nunique()
        expected_nonpending=int(frame.status.isin(['Presented','Accepted','Declined','Expired']).sum())
        expected_accepted_quotes=int(frame.status.eq('Accepted').sum())
        sql_options=dict(query(conn,'02_prospect_options.sql',**filters).fetchone())
        sql_prospects=dict(query(conn,'04_accepted_prospect_share.sql',**filters).fetchone())
        sql_shares=[dict(r) for r in query(conn,'03_accepted_quote_share.sql',**filters)]
        sql_values=[sql_options['quote_count'],sql_prospects['quoted_prospects'],
                    sql_prospects['accepted_prospects'],sum(r['non_pending_quotes'] for r in sql_shares),
                    sum(r['accepted_quotes'] for r in sql_shares)]
        expected=[expected_quotes,expected_prospects,expected_accepted,expected_nonpending,expected_accepted_quotes]
        if sql_values!=expected:
            raise AssertionError(f'{label}: SQL {sql_values} != pandas {expected}')
        checks.append(dict(filter=label,quote_count=expected_quotes,quoted_prospects=expected_prospects,
             accepted_prospects=expected_accepted,accepted_quotes=expected_accepted_quotes,
             non_pending_quotes=expected_nonpending,result='PASS'))
    trend=pd.read_sql_query((ROOT/'sql/06_monthly_trend.sql').read_text(),conn,
                           params=dict(carrier_id=None,product=None,month=None))
    independent=quotes.groupby('created_month').size().reindex(trend.created_month,fill_value=0)
    if list(independent)!=list(trend.quote_count):
        raise AssertionError('Monthly pandas counts disagree with SQL')
    return pd.DataFrame(checks),trend


def chart_style(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#C8D3DD')
    ax.grid(axis='y',color='#E6EBF0',linewidth=.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors='#435364',labelsize=10)


def report(data_dir, output):
    output.mkdir(parents=True,exist_ok=True)
    figures=output/'figures'
    figures.mkdir(exist_ok=True)
    conn=sqlite3.connect(f'file:{(data_dir / "insurance_demo.db").resolve()}?mode=ro',uri=True)
    conn.row_factory=sqlite3.Row
    try:
        quotes=pd.read_sql_query('SELECT * FROM analytics_quotes ORDER BY id',conn)
        checks,trend=reconcile(conn,quotes)
        shares=pd.DataFrame([dict(r) for r in query(conn,'03_accepted_quote_share.sql')])
        compare=pd.DataFrame([dict(r) for r in query(conn,'05_comparable_premiums.sql')],
                             columns=[c[0] for c in query(conn,'05_comparable_premiums.sql').description])
        options=dict(query(conn,'02_prospect_options.sql').fetchone())
        prospects=dict(query(conn,'04_accepted_prospect_share.sql').fetchone())
    finally:
        conn.close()
    manifest=json.loads((data_dir/'manifest.json').read_text())
    qa=json.loads((data_dir/'qa.json').read_text())
    if any(r['result']!='PASS' for r in qa):
        raise ValueError('Refusing to publish a report with failing data QA')
    checks.to_csv(output/'filter_reconciliation.csv',index=False)
    trend.to_csv(output/'monthly_reconciliation.csv',index=False)
    groups=(compare.groupby('comparison_group_id').agg(prospect_id=('prospect_id','first'),
        product=('quote_type','first'),quote_count=('id','size'),
        minimum_usd=('annual_premium_usd','min'),maximum_usd=('annual_premium_usd','max'),
        range_usd=('group_range_usd','first')).reset_index())
    groups.to_csv(output/'comparable_groups.csv',index=False)
    accepted=int(shares.accepted_quotes.sum())
    non_pending=int(shares.non_pending_quotes.sum())
    total=len(quotes)
    aq=accepted/non_pending if non_pending else None
    ap=prospects['accepted_prospect_share']
    qpp=options['quotes_per_quoted_prospect']
    def percent(value): return f'{value:.1%}' if value is not None else '—'
    pct=percent(aq)
    scope=f"{manifest['start_date']} to {manifest['snapshot_date']} · Snapshot {manifest['snapshot_date']}"
    plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'#152E43','axes.labelcolor':'#435364','savefig.facecolor':'white'})
    fig,ax=plt.subplots(figsize=(11,3.1),layout='constrained')
    ax.plot(range(len(trend)),trend.quote_count,color='#287D9A',marker='o',linewidth=2)
    ax.set_xticks(range(len(trend)), [str(m)[2:] for m in trend.created_month])
    ax.set_ylim(bottom=0); ax.set_ylabel('Quotes'); chart_style(ax)
    ax.set_title(f'Quote volume by complete created month · n={total}',loc='left',pad=14,fontweight='bold')
    fig.savefig(figures/'monthly_volume.png',dpi=160); plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,3.6),layout='constrained',gridspec_kw={'width_ratios':[1,1.6]})
    mix=quotes.groupby('quote_type').size().sort_values()
    axes[0].barh(mix.index,mix.values,color='#287D9A')
    axes[0].bar_label(axes[0].containers[0],padding=4)
    axes[0].set_xlim(0,max(mix.max() if len(mix) else 0,1)*1.2)
    axes[0].set_xlabel('Quotes'); axes[0].set_title('Product mix',loc='left',fontweight='bold'); chart_style(axes[0])
    axes[1].barh(shares.carrier.str.replace('Fictional ',''),shares.accepted_quote_share.fillna(0),color='#BE8744')
    for i,row in shares.iterrows():
        ratio=row.accepted_quote_share
        label='— (no eligible denominator)' if pd.isna(ratio) else f'{ratio:.1%} ({row.accepted_quotes}/{row.non_pending_quotes})'
        axes[1].text(0 if pd.isna(ratio) else ratio+.007,i,label,va='center',fontsize=10)
    maximum=shares.accepted_quote_share.max()
    axes[1].set_xlim(0,max(.4,0 if pd.isna(maximum) else maximum+.25))
    axes[1].xaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set_xlabel('Accepted / non-pending quotes')
    axes[1].set_title('Accepted quote share at snapshot',loc='left',fontweight='bold'); chart_style(axes[1])
    fig.savefig(figures/'mix_and_accepted_share.png',dpi=160); plt.close(fig)
    fig,ax=plt.subplots(figsize=(11,4.1),layout='constrained')
    for i,row in groups.head(10).iterrows():
        ax.plot([row.minimum_usd,row.maximum_usd],[i,i],color='#287D9A',linewidth=3,marker='o')
    ax.set_yticks(range(min(10,len(groups))),[f"Prospect {int(r.prospect_id):03} · {r['product']}" for _,r in groups.head(10).iterrows()])
    ax.set_xlim(left=0); ax.set_xlabel('Annualized premium (USD)'); ax.invert_yaxis(); chart_style(ax)
    ax.set_title(f'Recorded-equivalent premium ranges · first {min(10,len(groups))} of {len(groups)} groups',loc='left',fontweight='bold',pad=12)
    fig.savefig(figures/'comparable_ranges.png',dpi=160); plt.close(fig)
    css='''*{box-sizing:border-box}body{margin:0;background:#edf2f5;color:#173248;font:16px/1.55 system-ui,sans-serif}main{max-width:1160px;margin:32px auto;background:white;padding:44px 52px;border-top:7px solid #287d9a}h1{font-size:38px;line-height:1.13;letter-spacing:-1px;margin:10px 0}h2{font-size:21px;margin:30px 0 12px}p{margin:12px 0}a{color:#17637d}.eyebrow{color:#17637d;font-size:12px;letter-spacing:2px;font-weight:700}.scope,.note{color:#526779;font-size:14px}.banner{background:#fff3de;padding:12px 16px;border-left:4px solid #be8744}.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin:26px 0}.kpi{padding:14px 0;border-top:1px solid #d2dde5}.number{font-size:32px;font-weight:650}.label{font-size:14px}.small{font-size:12px;color:#526779}img{width:100%;height:auto;display:block}.chart-scroll{overflow-x:auto}.mobile-note{display:none}.table-wrap{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px;text-align:left}th{background:#edf2f5}td,th{padding:8px 10px;border-bottom:1px solid #e0e7ec}nav{display:flex;gap:24px;margin:18px 0}footer{border-top:1px solid #d2dde5;margin-top:28px;padding-top:16px;font-size:13px;color:#526779}details{margin:16px 0}summary{cursor:pointer;font-weight:600}@media(max-width:720px){main{margin:0;padding:24px 18px}h1{font-size:30px}.kpis{grid-template-columns:repeat(2,1fr)}nav{flex-wrap:wrap}.number{font-size:27px}.chart-scroll img{min-width:760px}.mobile-note{display:block;font-size:13px;color:#526779}}@media print{body{background:white}main{margin:0;padding:15px}nav{display:none}}'''
    def page(title,body):
        body=re.sub(r'(<img[^>]+>)', r'<div class="chart-scroll" tabindex="0" role="region" aria-label="Chart; scroll horizontally on small screens">\1</div>', body)
        body='<p class="mobile-note">Scroll charts sideways for readable labels; exact values are in the expandable data tables.</p>'+body
        return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(title)} | Insurance analytics demo</title><style>{css}</style></head><body><main><div class="eyebrow">ENZO FERRARINI / INSURANCE ANALYTICS</div><h1>{title}</h1><p class="scope">{scope}</p><p class="banner"><strong>Synthetic demonstration data.</strong> All prospects and carriers are fictional. Results illustrate a workflow, not real performance.</p><nav aria-label="Report pages"><a href="index.html">01 · Manager overview</a><a href="comparison.html">02 · Comparison and QA</a><a href="decision_memo.md">Decision memo</a></nav>{body}<footer>Source: fixed-seed generator {manifest['seed']} · v{manifest['generator_version']} · <a href="manifest.json">Generation manifest</a> · <a href="data_quality.md">QA evidence</a><br>Current statuses cannot reconstruct conversion timing. Premiums are annualized USD; no issued policies, revenue, commissions or causal impact are measured.</footer></main></body></html>'''
    cards=[(str(total),'Quotes', 'Distinct quote records'),(str(options['quoted_prospects']),'Quoted prospects',f'{qpp:.2f} quotes per quoted prospect' if qpp is not None else 'No quoted prospects'),(pct,'Accepted quote share',f'{accepted} accepted / {non_pending} non-pending'),(percent(ap),'Accepted prospect share',f"{prospects['accepted_prospects']} / {prospects['quoted_prospects']} quoted prospects")]
    kpis='<div class="kpis">'+''.join(f'<div class="kpi"><div class="number">{value}</div><div class="label">{label}</div><div class="small">{caption}</div></div>' for value,label,caption in cards)+'</div>'
    body=kpis+'''<p>Use this view to frame questions about quoting and follow-up. Acceptance shares use different units: a quote can be one of several options for the same prospect.</p>'''
    body+='<img src="figures/monthly_volume.png" alt="Line chart of quote counts by complete month; exact values are available in the monthly table below.">'
    body+='<img src="figures/mix_and_accepted_share.png" alt="Product quote counts and carrier accepted quote shares; each share shows its numerator and denominator.">'
    body+='<p class="note">Pending quotes are excluded only from accepted quote share. Newer cohorts have had less time to decide. Carrier differences are generated variation, not performance evidence.</p>'
    body+='<details><summary>Accessible data: monthly counts and carrier denominators</summary><div class="table-wrap">'+table(trend)+table(shares)+'</div></details>'
    body+='<p><strong>Next investigation:</strong> collect timestamped follow-up events and observed policy outcomes before recommending a real operational change.</p>'
    (output/'index.html').write_text(page('Manager overview',body))
    failed=sum(r['result']=='FAIL' for r in qa)
    body=f'<div class="kpis"><div class="kpi"><div class="number">{len(groups)}</div><div class="label">Comparable groups</div></div><div class="kpi"><div class="number">{len(compare)}</div><div class="label">Quotes in those groups</div></div><div class="kpi"><div class="number">{len(qa)-failed}/{len(qa)}</div><div class="label">Data checks passed</div></div><div class="kpi"><div class="number">5/5</div><div class="label">SQL ↔ pandas filter checks</div></div></div>'
    body+='<p>Groups require the same prospect, product, effective date, expiration date, and entire recorded coverage set—including limits, deductibles and notes. At least two distinct carriers must remain in the selected population.</p>'
    body+='<img src="figures/comparable_ranges.png" alt="Minimum and maximum annualized premium per comparable group, with all exact values in the table below.">'
    body+='<p class="note">All statuses are included, so these are historical comparison examples, not currently available offers. Matching recorded fields does not prove actual contract equivalence. Cheapest does not mean best.</p>'
    body+='<h2>Reconciliation by selected population</h2><div class="table-wrap">'+table(checks)+'</div><p class="note">The report shows the full sample. Each selection above was calculated separately in SQL and pandas to check that the quote and prospect counts agree.</p>'
    body+='<details><summary>Accessible data: all comparable groups</summary><div class="table-wrap">'+table(groups)+'</div></details>'
    body+='<h2>Quality notes</h2><p>Foreign keys, required fields, status values, dates, integer cents and counts pass. Premium extremes are generated within declared product ranges; this is internal consistency, not market-price validation.</p>'
    (output/'comparison.html').write_text(page('Comparison and QA',body))
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    # Pure Markdown avoids a tabulate dependency.
    lines=['# Data quality','',f'Synthetic data · snapshot {manifest["snapshot_date"]} · seed {manifest["seed"]}.','',
           '| Check | Expected | Actual | Result |','|---|---|---|---|']
    lines += [f'| {r["check"]} | {r["expected"]} | {r["actual"]} | {r["result"]} |' for r in qa]
    lines += ['', '## Reconciliation', '', 'SQL and pandas give the same quote counts for all 12 complete months and the same results for five filter selections. See [filter_reconciliation.csv](filter_reconciliation.csv).', '', '## Premium extremes', '']
    extremes=quotes.groupby('quote_type').annual_premium_usd.agg(['count','min','max'])
    for product,row in extremes.iterrows():
        lines.append(f'- {product}: n={int(row["count"])}, ${row["min"]:,.2f}–${row["max"]:,.2f}.')
    lines += ['', 'The generator bounds each base premium at 70–130% of its product baseline, then applies 80–120% variation. The lowest and highest premiums fall within those generated ranges. They have not been checked against actual insurance prices.', '', '## Limits', '', 'The original SQLite schema is preserved. SQLite affinity does not enforce integer storage or calendar-date validity by itself; Python QA enforces these assumptions and invalid fixtures test detection. Every new SQLite connection must enable foreign keys. Current status has no event history. Exact recorded coverage equality does not establish contractual equivalence. Unquoted prospects are outside quote-based denominators.']
    (output/'data_quality.md').write_text('\n'.join(lines)+'\n')
    median_range=groups.range_usd.median() if len(groups) else 0
    minimum_range=groups.range_usd.min() if len(groups) else 0
    maximum_range=groups.range_usd.max() if len(groups) else 0
    memo=f'''# Decision memo: what to check next

For an independent agency manager reviewing quotes created from {manifest['start_date']} through {manifest['snapshot_date']}. Statuses are recorded as of {manifest['snapshot_date']}. All records are fictional.

Before changing the quoting process, the first step would be to trace a small sample of prospects from their initial request to a final decision. This report can help frame that review, but the data was generated for the project. It cannot tell an agency which carrier to favor or whether its staff are following up effectively.

The sample contains {manifest['row_counts']['prospects']} prospects, six fictional carriers and {total} quotes. It uses a fixed random seed ({manifest['seed']}), so the same inputs reproduce the same records. The analysis checks dates, required fields, relationships and currency units. SQL results were compared with hand-calculated examples and an independent pandas calculation.

## Quote volume does not tell the whole story

The {total} quotes belong to {options['quoted_prospects']} prospects, giving {qpp:.2f} quotes per quoted prospect. Another {manifest['row_counts']['prospects']-options['quoted_prospects']} registered prospects have no quotes. That last group was put into the generator on purpose: every tenth prospect is left unquoted. It should not be read as evidence of a service problem.

With actual agency records, this would be a useful group to review. Some people might be waiting for a quote; others might have incomplete information, be ineligible, or have duplicate records. Request and follow-up dates would help separate those explanations before setting a target.

## Acceptance depends on what is being counted

There are {accepted} accepted quotes out of {non_pending} non-pending quotes, an accepted quote share of {pct}. At the prospect level, {prospects['accepted_prospects']} of {prospects['quoted_prospects']} people with quotes have at least one accepted option: {percent(ap)}. Both calculations are useful, but they answer different questions. An accepted quote also does not confirm that a policy was issued.

Pending quotes are excluded from the quote-level rate by definition. The report has only current statuses, so it cannot show how long a decision took. More recent quotes have had less time to reach a decision. Differences between the fictional carriers come from the generated sample; carrier performance was not modeled.

## Compare the coverage before the price

There are {len(groups)} matching groups containing {len(compare)} quotes. The median difference between the lowest and highest annual premium in a group is ${median_range:,.2f}, with group ranges from ${minimum_range:,.2f} to ${maximum_range:,.2f}. Each group shares a prospect, product, dates and all recorded coverage details. Quotes with missing coverage are excluded.

These groups were deliberately constructed to test the comparison. The ranges are not estimates of customer savings. A real comparison would still need to account for exclusions, endorsements, eligibility and payment terms that this database does not capture.

## Next step

For a real process review, collect quote and response timestamps, status changes, complete coverage terms and linked issued-policy outcomes. Use a consistent follow-up window so newer prospects are not judged against older ones. Questions about revenue would also need issued premiums, commissions and acquisition costs. Once those records are available, the same queries could help identify cases worth reviewing and support a better-informed decision about what to change.
'''
    (output/'decision_memo.md').write_text(memo)
    (output/'summary.json').write_text(json.dumps(dict(quotes=total,quoted_prospects=options['quoted_prospects'],
        accepted_quotes=accepted,non_pending_quotes=non_pending,accepted_quote_share=aq,
        accepted_prospect_share=ap,comparison_groups=len(groups),comparable_quotes=len(compare),
        median_premium_range_usd=median_range),indent=2)+'\n')
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'data/demo')
    parser.add_argument('--output',type=Path,default=ROOT/'reports')
    args=parser.parse_args()
    print(report(args.data,args.output))


if __name__=='__main__': main()
