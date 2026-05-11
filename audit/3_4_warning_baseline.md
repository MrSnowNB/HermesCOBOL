# Section 3.4 Baseline Audit Report

**Run timestamp:** 2026-05-11T11:30:52Z
**Baseline main SHA:** 77a5ca5
**Test gate:** 55/55 PASS
**--all summary:** 31 files, 0 errors, 3 warnings, local=0: 0, local=1: 0

## Spec recommendation
spec_complete

The 3.4 specification covers all currently observed warnings. No unexpected warnings of type close-mismatch or other categories were found in the 31-file corpus. Note that COCRDSLC and COCRDUPC currently do not produce warnings, so their inclusion in 3.4 might be for preventative reasons or based on expected schema changes.

## Target file status (the five files named in 3.4)
| File | In spec | close-mismatch | local | facts | delta | other warnings |
|------|---------|----------------|-------|-------|-------|----------------|
| COACTUPC | Yes | YES | 85 | 87 | -2 | none |
| COACTVWC | Yes | YES | 34 | 36 | -2 | none |
| COCRDLIC | Yes | YES | 39 | 41 | -2 | none |
| COCRDSLC | Yes | no | - | - | - | none |
| COCRDUPC | Yes | no | - | - | - | none |

## All WARNINGs by type
| Type | Count | Files |
|------|-------|-------|
| close-mismatch | 3 | COACTUPC, COACTVWC, COCRDLIC |

## Out-of-spec WARNINGs (require spec expansion)
none

## Per-file detail
### COACTUPC
- **close-mismatch**: local=85 facts=87 (delta=-2)
  - `WARNING [COACTUPC]: paragraph count mismatch: local=85 facts=87`
### COACTVWC
- **close-mismatch**: local=34 facts=36 (delta=-2)
  - `WARNING [COACTVWC]: paragraph count mismatch: local=34 facts=36`
### COCRDLIC
- **close-mismatch**: local=39 facts=41 (delta=-2)
  - `WARNING [COCRDLIC]: paragraph count mismatch: local=39 facts=41`
