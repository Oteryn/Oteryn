#!/usr/bin/env python3
"""Fail-closed verifier for the bounded AUDIT186 Semantic-01 historical adoption."""
import csv, hashlib, io, json
from pathlib import Path
import verify_report
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/evidence/organization-audit-20260907'
CANDIDATE_SHA='c160a9f7a198de30df34e2e1dd93341088488a073b8e36f9e1d538a86c5d23ae'
OVERLAY_SHA='d0967fd5a9c16ab81a1a00d9a71b2d0ade8ce14cba56ffd60d8c16fd1bcf21b0'
LEDGER_SHA='d93838bebb6f3690bad3d6182bbc05edd0af8acf8a98d28260e496276b95a22b'
EXPECTED=(4361,335,113,3913,448)
INDEX_SHA='791acc722b78a2c48df93a01b91f948ffadc5e2716dc711112958671be283567'
HISTORICAL_DURABILITY_FRAGMENT='At the R7 transition, the 26 historical repository-audit packet leaves remained UNVERIFIED; the later Semantic-01 adoption below supersedes that coverage state.'
ADOPTION_DURABILITY_FRAGMENT='The immutable reviewed PR #204 26-leaf historical repository-audit packet is adopted exactly once as per-leaf DIRECT through coverage-review-audit186-semantic-01-historical-direct-additions.tsv'
FORBIDDEN_STALE_DURABILITY_FRAGMENT='The 26 historical repository-audit packet leaves remain UNVERIFIED;'
def require(x,m):
 if not x: raise ValueError(m)
def parse_overlay(raw):
 require(hashlib.sha256(raw).hexdigest()==OVERLAY_SHA,'overlay binding drift')
 rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8')),delimiter='\t'))
 require(len(rows)==26 and len({r['path'] for r in rows})==26,'historical path missing/duplicate')
 return rows
def validate_packet(candidate,rows,summary,index):
 require(hashlib.sha256(json.dumps(candidate,indent=2).encode()+b'\n').hexdigest()==CANDIDATE_SHA,'candidate binding drift')
 leaves=candidate['family']['paths']; expected={x['path']:x for x in leaves}
 require(len(expected)==26 and set(expected)=={r['path'] for r in rows},'historical path set drift')
 for r in rows:
  leaf=expected[r['path']]
  require(r['blob_sha']==leaf['blob_sha'],'blob drift')
  require(r['depth']=='SCOPED_SEMANTIC_REVIEW','DIRECT depth drift')
  require(r['scope']==leaf['semantic_scope'] and r['line_ranges']=='[]','semantic scope/current-truth drift')
 require(tuple(summary[k] for k in ('source_leaf_total','scoped_review_paths','grouped_revalidated_paths','unverified_semantics_total','semantically_classified_paths'))==EXPECTED,'accounting projection drift')
 require(summary['ledger_sha256']==LEDGER_SHA,'ledger/summary binding drift')
 durability=summary.get('durability')
 require(type(durability) is str,'durability type drift')
 require(durability.count(HISTORICAL_DURABILITY_FRAGMENT)==1,'historical durability binding drift')
 require(durability.count(ADOPTION_DURABILITY_FRAGMENT)==1,'adoption durability binding drift')
 require(FORBIDDEN_STALE_DURABILITY_FRAGMENT not in durability,'stale current UNVERIFIED durability claim')
 require(hashlib.sha256(json.dumps(index,sort_keys=True,separators=(',',':')).encode()).hexdigest()==INDEX_SHA,'index record drift')
 require(index['canonical_ledger_sha256']==LEDGER_SHA and index['coverage_delta']=={'direct':26,'grouped':0,'unverified':-26,'semantically_classified':26},'index binding drift')
 require(index['semantic_coverage_complete'] is False and index['residual_obligations']==14,'completion boundary drift')
def main():
 c_raw=(BASE/'audit186-semantic-01-historical-candidate.json').read_bytes(); require(hashlib.sha256(c_raw).hexdigest()==CANDIDATE_SHA,'candidate binding drift')
 candidate=json.loads(c_raw); rows=parse_overlay((BASE/verify_report.AUDIT186_SEMANTIC_01_DIRECT_ADDITIONS).read_bytes())
 summary=json.loads((BASE/'coverage-summary.json').read_text()); idx=json.loads((BASE/'verification-index.json').read_text())['audit186_semantic_01_historical_direct_adoption']
 validate_packet(candidate,rows,summary,idx)
 result=verify_report.validate(ROOT/'docs/evidence/OTERYN-ORGANIZATION-COMPREHENSIVE-AUDIT-20260907.json')
 require(tuple(result[k] for k in ('source_leaves','scoped_review_paths','grouped_revalidated_paths','unverified_semantics','semantically_classified_paths'))==EXPECTED,'report binding drift')
 print(json.dumps({'result':'AUDIT186_SEMANTIC_01_ADOPTION_VALID_NOT_CURRENT_TRUTH','paths':26,'ledger_sha256':LEDGER_SHA,'accounting':EXPECTED,'meta':{'direct':122,'unverified':88},'residual_obligations_open':14},sort_keys=True))
if __name__=='__main__': main()
