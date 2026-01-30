import os
import sys
from pathlib import Path

print("=" * 70)
print("ENVIRONMENT VARIABLE SOURCE DETECTIVE")
print("=" * 70)
print()

# Check 1: System environment variables
print("1. CHECKING SYSTEM ENVIRONMENT VARIABLES")
print("-" * 70)
sys_phreeqc = os.environ.get('PHREEQC_EXECUTABLE_PATH')
if sys_phreeqc:
    print(f"⚠️  FOUND in system environment!")
    print(f"   Value: {sys_phreeqc}")
    print()
    print("   This is overriding your .env file!")
    print("   You need to:")
    if os.name == 'nt':  # Windows
        print("   - Open System Properties > Environment Variables")
        print("   - Remove or fix PHREEQC_EXECUTABLE_PATH")
    else:
        print("   - Check ~/.bashrc or ~/.bash_profile")
        print("   - Remove the PHREEQC_EXECUTABLE_PATH export")
else:
    print("✅ Not found in system environment variables")
print()

# Check 2: Find all .env files
print("2. SEARCHING FOR ALL .env FILES")
print("-" * 70)

current_dir = Path.cwd()
env_files = []

# Search current directory
for env_file in current_dir.glob('.env*'):
    env_files.append(env_file)
    print(f"Found: {env_file}")

# Search parent directories (up to 3 levels)
parent = current_dir.parent
for _ in range(3):
    for env_file in parent.glob('.env*'):
        if env_file not in env_files:
            env_files.append(env_file)
            print(f"Found: {env_file}")
    parent = parent.parent

print()

# Check 3: Examine each .env file
print("3. CHECKING EACH .env FILE FOR PHREEQC_EXECUTABLE_PATH")
print("-" * 70)

for env_file in env_files:
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        has_phreeqc = False
        for i, line in enumerate(lines, 1):
            if 'PHREEQC_EXECUTABLE_PATH' in line and not line.strip().startswith('#'):
                if not has_phreeqc:
                    print(f"\n📄 File: {env_file}")
                    has_phreeqc = True
                print(f"   Line {i}: {line.rstrip()}")
                
                # Check for the typo
                if 'x6in' in line:
                    print(f"   ⚠️  THIS LINE HAS THE TYPO! ^^^")
                    
    except Exception as e:
        print(f"   Error reading {env_file}: {e}")

print()

# Check 4: What dotenv is actually loading
print("4. TESTING DOTENV LOADING FROM DIFFERENT LOCATIONS")
print("-" * 70)

from dotenv import load_dotenv, find_dotenv

# Find what dotenv thinks is the .env file
dotenv_path = find_dotenv()
print(f"dotenv will load from: {dotenv_path or 'NOT FOUND'}")
print()

if dotenv_path:
    print(f"Contents of {dotenv_path}:")
    try:
        with open(dotenv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if 'PHREEQC_EXECUTABLE_PATH' in line and not line.strip().startswith('#'):
                    print(f"   Line {i}: {line.rstrip()}")
                    if 'x6in' in line:
                        print(f"   ⚠️  TYPO FOUND HERE!")
    except Exception as e:
        print(f"   Error: {e}")

print()
print("=" * 70)
print("SOLUTION")
print("=" * 70)
print()

if sys_phreeqc:
    print("🔧 IMMEDIATE ACTION:")
    print("   Remove PHREEQC_EXECUTABLE_PATH from system environment variables")
    print()
    if os.name == 'nt':
        print("   Windows:")
        print("   1. Press Win + X > System")
        print("   2. Advanced system settings > Environment Variables")
        print("   3. Look in both User and System variables")
        print("   4. Delete or fix PHREEQC_EXECUTABLE_PATH")
        print("   5. Restart your terminal")
else:
    print("🔧 Try these fixes:")
    print()
    print("   Option 1: Force reload with a clean script")
    print("   Run: python -c \"from dotenv import load_dotenv; load_dotenv(override=True); import os; print(os.getenv('PHREEQC_EXECUTABLE_PATH'))\"")
    print()
    print("   Option 2: Manually edit line 123 of .env")
    print("   Check if there are any hidden characters or encoding issues")
    print()
    print("   Option 3: Delete .env and recreate it fresh")

print()