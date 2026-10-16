# NIYAM reliability tests

These standard-library `unittest` tests check the memory store and restricted desktop-action module.

## What is tested

- Memory persistence across store instances, whitespace normalization, duplicate prevention, and stable IDs
- Input limits, memory capacity, deletion, context selection, and corrupt-file protection
- Explicit-save semantics and the two-step clear-all confirmation flow
- Allowlisted Notepad/Calculator/YouTube actions, expected failures, and rejection of arbitrary commands/URLs

All memory tests use temporary directories and do not touch the real `data/memories.json`. The desktop-action tests mock OS/browser calls and do not launch applications.

## Run on Windows PowerShell

From the NIYAM project root:

```powershell
.\.venv\Scripts\python.exe -m py_compile .\main.py .\tools.py .\memory_store.py
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -p "test_*.py" -v
```

Or run `.un_tests.ps1`, which also writes `test-reports\latest-test-report.txt`.

## Interpretation

A passing unit-test run is evidence for the tested functions only. It does not guarantee model factual accuracy, real microphone transcription quality, latency, or end-to-end application reliability. Those require separate repeatable manual or integration tests.
