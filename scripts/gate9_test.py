# Run regression tests
import subprocess
import sys

commands = [
    ['C:\\Users\\AMD\\AppData\\Local\\Programs\\Python\\Python310\\python.exe', 'scripts\\validate_canonical_ir.py'],
    ['C:\\Users\\AMD\\AppData\\Local\\Programs\\Python\\Python310\\python.exe', 'scripts\\validate_roundtrip.py'],
    ['C:\\Users\\AMD\\AppData\\Local\\Programs\\Python\\Python310\\python.exe', '-m', 'pytest', 'tests/', '-q', '--tb=short'],
]

for i, cmd in enumerate(commands, 1):
    print(f'=== Command {i}: {" ".join(cmd)} ===')
    result = subprocess.run(cmd, capture_output=True, text=True)
    lines = result.stdout.split('\n')
    if lines:
        print('\n'.join(lines[-2:]) if len(lines) >= 2 else lines[0])
    if result.stderr:
        print('STDERR:', result.stderr[-200:] if len(result.stderr) > 200 else result.stderr)
    print()