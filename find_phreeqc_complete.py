import os
import subprocess
from pathlib import Path

print("=" * 70)
print("PHREEQC COMPLETE INSTALLATION FINDER")
print("=" * 70)
print()

# Your installation directory
install_dir = r"C:\Program Files\USGS\phreeqc-3.8.6-17100-x64"

print(f"Scanning installation directory: {install_dir}")
print()

# Find all phreeqc.exe files
print("=" * 70)
print("FINDING PHREEQC EXECUTABLES")
print("-" * 70)

executables = []
for root, dirs, files in os.walk(install_dir):
    if "phreeqc.exe" in files:
        exe_path = os.path.join(root, "phreeqc.exe")
        executables.append(exe_path)
        print(f"Found: {exe_path}")

# Prefer Release over ClrRelease
preferred_exe = None
for exe in executables:
    if "Release" in exe and "ClrRelease" not in exe:
        preferred_exe = exe
        break
if not preferred_exe and executables:
    preferred_exe = executables[0]

print()
if preferred_exe:
    print(f"✅ Using: {preferred_exe}")
else:
    print("❌ No PHREEQC executable found!")
    exit(1)

print()

# Search for database files (.dat files) in the entire installation
print("=" * 70)
print("SEARCHING FOR DATABASE FILES")
print("-" * 70)

database_locations = {}
for root, dirs, files in os.walk(install_dir):
    dat_files = [f for f in files if f.endswith('.dat')]
    if dat_files:
        database_locations[root] = dat_files

if not database_locations:
    print("❌ No database files found in installation directory!")
else:
    print(f"Found database files in {len(database_locations)} location(s):")
    print()
    
    for location, files in database_locations.items():
        print(f"Location: {location}")
        for file in sorted(files):
            filepath = os.path.join(location, file)
            size = os.path.getsize(filepath) / 1024
            print(f"  - {file} ({size:.1f} KB)")
        print()

# Find the best database directory (one with phreeqc.dat and pitzer.dat)
best_db_dir = None
for location, files in database_locations.items():
    if 'phreeqc.dat' in files and 'pitzer.dat' in files:
        best_db_dir = location
        break

# If not found, use the location with the most .dat files
if not best_db_dir and database_locations:
    best_db_dir = max(database_locations.keys(), key=lambda x: len(database_locations[x]))

print("=" * 70)
print("RECOMMENDED DATABASE DIRECTORY")
print("-" * 70)
if best_db_dir:
    print(f"✅ {best_db_dir}")
    print()
    print("Files in this directory:")
    for file in sorted(database_locations[best_db_dir]):
        print(f"  - {file}")
else:
    print("❌ Could not determine best database directory")

print()

# Test PHREEQC
print("=" * 70)
print("TESTING PHREEQC")
print("-" * 70)

if preferred_exe and best_db_dir:
    # Create test files
    test_dir = os.path.join(os.getcwd(), "phreeqc_test")
    os.makedirs(test_dir, exist_ok=True)
    
    input_file = os.path.join(test_dir, "test.pqi")
    output_file = os.path.join(test_dir, "test.pqo")
    database_file = os.path.join(best_db_dir, "phreeqc.dat")
    
    # Simple test input
    test_input = """TITLE Simple pH 7 solution
SOLUTION 1
    pH 7
    temp 25
END
"""
    
    with open(input_file, 'w') as f:
        f.write(test_input)
    
    print(f"Running test calculation...")
    print(f"  Executable: {preferred_exe}")
    print(f"  Database: {database_file}")
    print(f"  Input: {input_file}")
    print(f"  Output: {output_file}")
    print()
    
    try:
        result = subprocess.run(
            [preferred_exe, input_file, output_file, database_file],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        print(f"Return code: {result.returncode}")
        
        if os.path.exists(output_file):
            file_size = os.path.getsize(output_file)
            print(f"✅ Output file created ({file_size} bytes)")
            
            # Check for errors in output
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                if "ERROR" in content.upper():
                    print("⚠️  Output contains ERROR messages:")
                    for line in content.split('\n'):
                        if "ERROR" in line.upper():
                            print(f"  {line.strip()}")
                else:
                    print("✅ No errors in output - PHREEQC is working correctly!")
                    
                # Show a snippet of output
                print("\nFirst 500 characters of output:")
                print("-" * 70)
                print(content[:500])
        else:
            print("❌ Output file was not created")
            
        if result.stdout:
            print("\nStdout:")
            print(result.stdout[:500])
            
        if result.stderr:
            print("\nStderr:")
            print(result.stderr[:500])
            
    except subprocess.TimeoutExpired:
        print("❌ PHREEQC process timed out (took > 15 seconds)")
    except Exception as e:
        print(f"❌ Error running PHREEQC: {e}")

print()
print("=" * 70)
print("FINAL .env CONFIGURATION")
print("=" * 70)
print()

if preferred_exe and best_db_dir:
    # Check which files exist
    phreeqc_dat_exists = os.path.exists(os.path.join(best_db_dir, "phreeqc.dat"))
    pitzer_dat_exists = os.path.exists(os.path.join(best_db_dir, "pitzer.dat"))
    
    print("Copy this into your .env file:")
    print("-" * 70)
    print(f'PHREEQC_EXECUTABLE_PATH="{preferred_exe}"')
    print(f'PHREEQC_DATABASE_PATH="{best_db_dir}"')
    print(f'PHREEQC_DEFAULT_DATABASE=phreeqc.dat  # {"✅ EXISTS" if phreeqc_dat_exists else "❌ NOT FOUND"}')
    print(f'PHREEQC_PITZER_DATABASE=pitzer.dat    # {"✅ EXISTS" if pitzer_dat_exists else "❌ NOT FOUND"}')
    print('PHREEQC_DEBUG=false')
    print()
    
    if not phreeqc_dat_exists or not pitzer_dat_exists:
        print("⚠️  WARNING: Some database files are missing!")
        print("   Available databases:")
        for file in sorted(database_locations[best_db_dir]):
            print(f"   - {file}")
        print()

print("=" * 70)
print("DIRECTORY STRUCTURE")
print("=" * 70)
print("\nYour PHREEQC installation structure:")

def print_tree(directory, prefix="", max_depth=3, current_depth=0):
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(directory))
        dirs = [item for item in items if os.path.isdir(os.path.join(directory, item))]
        files = [item for item in items if os.path.isfile(os.path.join(directory, item))]
        
        # Show directories first
        for i, dir_name in enumerate(dirs[:5]):  # Limit to 5 dirs
            is_last = (i == len(dirs) - 1) and len(files) == 0
            print(f"{prefix}{'└── ' if is_last else '├── '}{dir_name}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(os.path.join(directory, dir_name), new_prefix, max_depth, current_depth + 1)
        
        # Then show relevant files
        for i, file_name in enumerate(files):
            if file_name.endswith(('.exe', '.dat', '.txt')):
                is_last = i == len(files) - 1
                print(f"{prefix}{'└── ' if is_last else '├── '}{file_name}")
                
    except PermissionError:
        print(f"{prefix}[Permission Denied]")
    except Exception as e:
        print(f"{prefix}[Error: {e}]")

print(f"\n{install_dir}/")
print_tree(install_dir)

print()
print("=" * 70)