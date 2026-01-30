#!/usr/bin/env python3
"""
Fresh PHREEQC Setup Verification Script
No caching, direct file reading
"""
import os
import subprocess
import sys

# Force current directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("FRESH SETUP VERIFICATION")
print("=" * 60)
print(f"Working directory: {os.getcwd()}")
print()

# Read .env file directly (no dotenv to avoid caching issues)
env_vars = {}
env_file = '.env'

if os.path.exists(env_file):
    print(f"✅ Found {env_file}")
    with open(env_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            # Skip comments and empty lines
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes
                    value = value.strip('"').strip("'")
                    env_vars[key.strip()] = value
else:
    print(f"❌ {env_file} not found!")
    sys.exit(1)

print()

# Test 1: PHREEQC Executable
print("=" * 60)
print("TEST 1: PHREEQC EXECUTABLE")
print("-" * 60)

phreeqc_exe = env_vars.get('PHREEQC_EXECUTABLE_PATH', '')
print(f"Path from .env: {phreeqc_exe}")

if not phreeqc_exe:
    print("❌ PHREEQC_EXECUTABLE_PATH not set")
elif not os.path.exists(phreeqc_exe):
    print(f"❌ File does not exist!")
    print(f"   Checked: {phreeqc_exe}")
    
    # Try to help find the issue
    if 'x6in' in phreeqc_exe:
        print("\n⚠️  TYPO DETECTED: 'x6in' should be 'x64\\bin'")
        correct = phreeqc_exe.replace('x6in', 'x64\\bin')
        print(f"   Should be: {correct}")
        if os.path.exists(correct):
            print(f"   ✅ Correct path exists!")
else:
    print("✅ PHREEQC executable found!")
    size = os.path.getsize(phreeqc_exe) / 1024 / 1024
    print(f"   Size: {size:.2f} MB")
    
    # Try to run it
    print("\n   Testing PHREEQC...")
    try:
        db_path = env_vars.get('PHREEQC_DATABASE_PATH', '')
        db_file = os.path.join(db_path, 'phreeqc.dat')
        
        if not os.path.exists(db_file):
            print(f"   ⚠️  Database not found: {db_file}")
        else:
            # Create test files
            test_dir = 'phreeqc_final_test'
            os.makedirs(test_dir, exist_ok=True)
            
            input_file = os.path.join(test_dir, 'test.pqi')
            output_file = os.path.join(test_dir, 'test.pqo')
            
            with open(input_file, 'w') as f:
                f.write("SOLUTION 1\n    pH 7\n    temp 25\nEND\n")
            
            result = subprocess.run(
                [phreeqc_exe, input_file, output_file, db_file],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0 and os.path.exists(output_file):
                print("   ✅ PHREEQC test successful!")
            else:
                print(f"   ⚠️  Test returned code: {result.returncode}")
                
    except Exception as e:
        print(f"   ⚠️  Could not test: {e}")

print()

# Test 2: Database Files
print("=" * 60)
print("TEST 2: DATABASE FILES")
print("-" * 60)

db_path = env_vars.get('PHREEQC_DATABASE_PATH', '')
print(f"Database path: {db_path}")

if not db_path:
    print("❌ PHREEQC_DATABASE_PATH not set")
elif not os.path.exists(db_path):
    print("❌ Directory does not exist")
else:
    print("✅ Database directory found")
    
    default_db = env_vars.get('PHREEQC_DEFAULT_DATABASE', 'phreeqc.dat')
    pitzer_db = env_vars.get('PHREEQC_PITZER_DATABASE', 'pitzer.dat')
    
    for db in [default_db, pitzer_db]:
        db_file = os.path.join(db_path, db)
        if os.path.exists(db_file):
            size = os.path.getsize(db_file) / 1024
            print(f"   ✅ {db} ({size:.1f} KB)")
        else:
            print(f"   ❌ {db} not found")

print()

# Test 3: MongoDB
print("=" * 60)
print("TEST 3: MONGODB")
print("-" * 60)

mongo_uri = env_vars.get('MONGO_URI', '')
if not mongo_uri:
    print("❌ MONGO_URI not set")
else:
    print(f"URI: {mongo_uri[:30]}...")
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_mongo():
            client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            db_name = env_vars.get('MONGO_DB_NAME', 'jimgreen')
            db = client[db_name]
            collections = await db.list_collection_names()
            print(f"✅ Connected to MongoDB")
            print(f"   Database: {db_name}")
            print(f"   Collections: {len(collections)}")
            client.close()
        
        asyncio.run(test_mongo())
    except ImportError:
        print("⚠️  motor not installed")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)

phreeqc_ok = phreeqc_exe and os.path.exists(phreeqc_exe)
db_ok = db_path and os.path.exists(db_path)
mongo_ok = bool(mongo_uri)

if phreeqc_ok and db_ok and mongo_ok:
    print("✅ ALL SYSTEMS READY!")
    print("\n🚀 You can now start your application!")
else:
    print("⚠️  Issues found:")
    if not phreeqc_ok:
        print("   ❌ PHREEQC executable")
    if not db_ok:
        print("   ❌ Database directory")
    if not mongo_ok:
        print("   ❌ MongoDB URI")

print()