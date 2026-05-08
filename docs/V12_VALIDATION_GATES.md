# HermesCOBOL v1.2 — Validation Gates

This document accumulates the gate commands for each Section.  
Each gate is the single source of truth for "Section N is closed."

---

## Section 1 Gate — Byte Layout

```powershell
# Section 1 Gate — Byte Layout
python scripts\byte_layout.py data\raw\cbl\CBACT01C.cbl > data\byte_layouts\CBACT01C.json

python -c "
import json
d = json.load(open(r'data\\byte_layouts\\CBACT01C.json'))
print('records=',          len(d['records']))
print('unresolved=',       d['unresolved'])

acct = next(r for r in d['records'] if r['name'] == 'ACCOUNT-RECORD')
print('ACCOUNT-RECORD total_bytes=', acct['total_bytes'])

fields = {f['qualified_name'].split('.')[-1]: f for f in acct['fields']}
print('ACCT-ID offset=',          fields['ACCT-ID']['offset'])
print('ACCT-ID length=',          fields['ACCT-ID']['length'])
print('ACCT-ACTIVE-STATUS offset=', fields['ACCT-ACTIVE-STATUS']['offset'])
print('ACCT-ACTIVE-STATUS length=', fields['ACCT-ACTIVE-STATUS']['length'])

print('redefines_groups=',
      [(r['name'], r['redefines_target'])
       for rec in d['records'] for r in rec['redefines_groups']])

occurs = [f for rec in d['records'] for f in rec['fields'] if f.get('occurs',1) > 1]
print('occurs_fields=', len(occurs))
"
```

**Expected output (Section 1 closed):**
```
records= 17
unresolved= []
ACCOUNT-RECORD total_bytes= 300
ACCT-ID offset= 0
ACCT-ID length= 11
ACCT-ACTIVE-STATUS offset= 11
ACCT-ACTIVE-STATUS length= 1
redefines_groups= [('CODATECN-REC.CODATECN-IN-REC.CODATECN-1INP', 'CODATECN-INP-DATE'),
                   ('CODATECN-REC.CODATECN-IN-REC.CODATECN-2INP', 'CODATECN-INP-DATE'),
                   ('CODATECN-REC.CODATECN-OUT-REC.CODATECN-1OUT', 'CODATECN-0UT-DATE'),
                   ('CODATECN-REC.CODATECN-OUT-REC.CODATECN-2OUT', 'CODATECN-0UT-DATE')]
occurs_fields= 1
```

---

## Section 2 Gate — Data Flow Extractor

```powershell
# Section 2 — Data Flow Extractor Gate
# What this proves:
# 1) data_flow.py produces paragraph_data_flow for real programs
# 2) qmap lookup is resolving to ACCOUNT-RECORD fields from byte_layout
# 3) unresolved[] is low and explainable on target paragraphs

python scripts\data_flow.py data\raw\cbl\CBACT01C.cbl > data\data_flow\CBACT01C.json

python -c "
import json
d = json.load(open(r'data\\data_flow\\CBACT01C.json'))
print('program=',         d['program'])
print('paragraph_count=', len(d['paragraph_data_flow']))
print('sample_paragraphs=', list(d['paragraph_data_flow'])[:5])

p = d['paragraph_data_flow'].get('1300-POPUL-ACCT-RECORD')
print('1300_exists=', p is not None)
if p:
    print('1300_reads_count=',   len(p['reads']))
    print('1300_mutates_count=', len(p['mutates']))
    print('1300_first_mutate=',  p['mutates'][0] if p['mutates'] else None)
    print('1300_unresolved=',    p['unresolved'])

p = d['paragraph_data_flow'].get('1350-WRITE-ACCT-RECORD')
print('1350_exists=', p is not None)
if p:
    print('1350_reads=',      p['reads'])
    print('1350_mutates=',    p['mutates'])
    print('1350_unresolved=', p['unresolved'])

print('program_unresolved=', d['program_unresolved'])
"
```

**Expected gate output (Section 2 closed when all true):**
- `paragraph_count` matches v1.1 facts `paragraphs_defined` for CBACT01C (±1).
- `1300-POPUL-ACCT-RECORD.mutates` contains at least one field qualified as `ACCOUNT-RECORD.*`  
  with offsets matching byte layout (`ACCT-ID` offset 0 length 11, `ACCT-ACTIVE-STATUS` offset 11 length 1).
- `1350-WRITE-ACCT-RECORD.reads` and `.mutates` both non-empty,  
  with at least one entry bound to the file-record of `ACCTFILE`.
- `unresolved[]` on both paragraphs is empty (or contains only acceptable CICS operands).
- `program_unresolved=[]`.

```powershell
# Corpus batch run
python scripts\data_flow.py --all

# Confirm 31 files written
python -c "
import glob
files = glob.glob(r'data\\data_flow\\*.json')
print('data_flow_files=', len(files))
print('programs=', sorted([f.split('\\\\')[-1] for f in files]))
"
```
