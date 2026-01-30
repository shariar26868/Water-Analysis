import os

print("=" * 70)
print("CHECKING .env FILE CONTENTS")
print("=" * 70)
print()

env_file = ".env"

if not os.path.exists(env_file):
    print(f"❌ {env_file} not found!")
    exit(1)

print(f"Reading: {os.path.abspath(env_file)}")
print()

# Read the actual file content
with open(env_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("PHREEQC-related lines in .env file:")
print("-" * 70)

for i, line in enumerate(lines, 1):
    # Show all PHREEQC lines (including commented ones)
    if 'PHREEQC' in line.upper():
        status = "ACTIVE  " if not line.strip().startswith('#') else "COMMENTED"
        print(f"{i:3d} [{status}] {line.rstrip()}")

print()
print("=" * 70)
print("CHECKING PYTHON ENVIRONMENT")
print("=" * 70)
print()

# Now load with dotenv and check what Python sees
from dotenv import load_dotenv
load_dotenv(override=True)  # Force reload

exe_path = os.getenv('PHREEQC_EXECUTABLE_PATH')
db_path = os.getenv('PHREEQC_DATABASE_PATH')

print("What Python sees after loading .env:")
print(f"PHREEQC_EXECUTABLE_PATH: {exe_path}")
print(f"PHREEQC_DATABASE_PATH: {db_path}")
print()

# Check if the paths match what we expect
expected_exe = r"C:\Program Files\USGS\phreeqc-3.8.6-17100-x64\bin\Release\phreeqc.exe"
expected_db = r"C:\Program Files\USGS\phreeqc-3.8.6-17100-x64\database"

if exe_path == expected_exe:
    print("✅ Executable path is CORRECT!")
else:
    print("❌ Executable path is WRONG!")
    print(f"   Expected: {expected_exe}")
    print(f"   Got:      {exe_path}")
    print()
    
    # Check for the specific typo
    if "x6in" in (exe_path or ""):
        print("⚠️  FOUND THE TYPO: 'x6in' should be 'x64\\bin'")
        print()
        print("POSSIBLE CAUSES:")
        print("1. There might be MULTIPLE PHREEQC_EXECUTABLE_PATH lines in .env")
        print("2. The wrong line is active (not commented)")
        print("3. There's a cached environment variable")
        print()
        print("SOLUTIONS:")
        print("1. Search .env for ALL occurrences of PHREEQC_EXECUTABLE_PATH")
        print("2. Make sure ONLY the correct line is uncommented")
        print("3. Delete any duplicate/wrong lines")

if db_path == expected_db:
    print("✅ Database path is CORRECT!")
else:
    print("❌ Database path might be wrong")
    
print()
print("=" * 70)
print("ACTION REQUIRED")
print("=" * 70)
print()
print("Please manually check your .env file for:")
print("1. Multiple PHREEQC_EXECUTABLE_PATH entries")
print("2. The wrong entry is active")
print("3. Extra spaces or hidden characters")
print()
print("Run this to see all active PHREEQC lines:")
print('  grep "^PHREEQC" .env')
print()