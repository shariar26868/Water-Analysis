import os
import re

print("=" * 70)
print("AUTOMATIC .env FIXER")
print("=" * 70)
print()

env_file = ".env"

if not os.path.exists(env_file):
    print(f"❌ {env_file} not found!")
    exit(1)

# Read the current .env file
with open(env_file, 'r', encoding='utf-8') as f:
    content = f.read()

print("Current PHREEQC configuration found:")
print("-" * 70)

# Find and display current PHREEQC settings
for line in content.split('\n'):
    if 'PHREEQC' in line and not line.strip().startswith('#'):
        print(line)

print()
print("-" * 70)
print()

# Create backup
backup_file = ".env.backup"
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✅ Backup created: {backup_file}")
print()

# Fix common issues
original_content = content

# Fix 1: x6in -> x64\bin
content = re.sub(
    r'phreeqc-3\.8\.6-17100-x6in\\',
    r'phreeqc-3.8.6-17100-x64\\bin\\',
    content
)

# Fix 2: Ensure quotes are present
content = re.sub(
    r'PHREEQC_EXECUTABLE_PATH=([^"\n].*phreeqc\.exe)',
    r'PHREEQC_EXECUTABLE_PATH="\1"',
    content
)

content = re.sub(
    r'PHREEQC_DATABASE_PATH=([^"\n].*database)',
    r'PHREEQC_DATABASE_PATH="\1"',
    content
)

# Fix 3: Remove duplicate quotes
content = re.sub(r'""', '"', content)

# Check if changes were made
if content != original_content:
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed the following issues:")
    print("   - Corrected x6in -> x64\\bin")
    print("   - Added proper quotes to paths")
    print()
    
    print("New PHREEQC configuration:")
    print("-" * 70)
    for line in content.split('\n'):
        if 'PHREEQC' in line and not line.strip().startswith('#'):
            print(line)
    print()
    print("=" * 70)
    print("✅ .env file has been fixed!")
    print("=" * 70)
    print()
    print("Now run: python verify_setup.py")
else:
    print("⚠️  No automatic fixes could be applied.")
    print("    You may need to manually edit your .env file.")
    print()
    print("The correct configuration should be:")
    print("-" * 70)
    print('PHREEQC_EXECUTABLE_PATH="C:\\Program Files\\USGS\\phreeqc-3.8.6-17100-x64\\bin\\Release\\phreeqc.exe"')
    print('PHREEQC_DATABASE_PATH="C:\\Program Files\\USGS\\phreeqc-3.8.6-17100-x64\\database"')
    print('PHREEQC_DEFAULT_DATABASE=phreeqc.dat')
    print('PHREEQC_PITZER_DATABASE=pitzer.dat')
    print('PHREEQC_DEBUG=false')

print()