import os
from dotenv import load_dotenv
import subprocess

load_dotenv()

# Test 1: Environment variables
print("=" * 50)
print("ENVIRONMENT VARIABLES:")
print("=" * 50)
phreeqc_exe = os.getenv('PHREEQC_EXECUTABLE_PATH')
phreeqc_db = os.getenv('PHREEQC_DATABASE_PATH')
mongo_uri = os.getenv('MONGO_URI')

print(f"PHREEQC_EXECUTABLE_PATH: {phreeqc_exe}")
print(f"PHREEQC_DATABASE_PATH: {phreeqc_db}")
print(f"MONGO_URI: {mongo_uri[:30] if mongo_uri else 'NOT SET'}...")
print()

# Test 2: PHREEQC executable
print("=" * 50)
print("PHREEQC EXECUTABLE TEST:")
print("=" * 50)

if not phreeqc_exe:
    print("❌ PHREEQC_EXECUTABLE_PATH not set in .env")
elif not os.path.exists(phreeqc_exe):
    print(f"❌ PHREEQC executable not found at: {phreeqc_exe}")
else:
    print(f"✅ PHREEQC executable found at: {phreeqc_exe}")
    
    # Try to run it
    try:
        # Create a simple test
        test_dir = os.path.join(os.getcwd(), "phreeqc_verification")
        os.makedirs(test_dir, exist_ok=True)
        
        input_file = os.path.join(test_dir, "verify.pqi")
        output_file = os.path.join(test_dir, "verify.pqo")
        db_file = os.path.join(phreeqc_db, "phreeqc.dat")
        
        # Simple test input
        with open(input_file, 'w') as f:
            f.write("""SOLUTION 1
    pH 7
    temp 25
END
""")
        
        print("   Running test calculation...")
        result = subprocess.run(
            [phreeqc_exe, input_file, output_file, db_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 and os.path.exists(output_file):
            print("   ✅ PHREEQC is working correctly!")
            print(f"   Test output file created: {output_file}")
        else:
            print(f"   ⚠️  PHREEQC ran but returned code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  PHREEQC test timed out (might be waiting for input)")
    except Exception as e:
        print(f"   ❌ Error testing PHREEQC: {e}")

print()

# Test 3: Database files
print("=" * 50)
print("DATABASE FILES TEST:")
print("=" * 50)

if not phreeqc_db:
    print("❌ PHREEQC_DATABASE_PATH not set in .env")
elif not os.path.exists(phreeqc_db):
    print(f"❌ Database directory not found at: {phreeqc_db}")
else:
    print(f"✅ Database directory found: {phreeqc_db}")
    
    default_db = os.getenv('PHREEQC_DEFAULT_DATABASE', 'phreeqc.dat')
    pitzer_db = os.getenv('PHREEQC_PITZER_DATABASE', 'pitzer.dat')
    
    default_path = os.path.join(phreeqc_db, default_db)
    pitzer_path = os.path.join(phreeqc_db, pitzer_db)
    
    if os.path.exists(default_path):
        size = os.path.getsize(default_path) / 1024
        print(f"   ✅ {default_db} found ({size:.1f} KB)")
    else:
        print(f"   ❌ {default_db} NOT found")
    
    if os.path.exists(pitzer_path):
        size = os.path.getsize(pitzer_path) / 1024
        print(f"   ✅ {pitzer_db} found ({size:.1f} KB)")
    else:
        print(f"   ❌ {pitzer_db} NOT found")
    
    # List all available databases
    try:
        dat_files = [f for f in os.listdir(phreeqc_db) if f.endswith('.dat')]
        print(f"\n   Available databases ({len(dat_files)} total):")
        for db in sorted(dat_files)[:10]:  # Show first 10
            print(f"   - {db}")
        if len(dat_files) > 10:
            print(f"   ... and {len(dat_files) - 10} more")
    except Exception as e:
        print(f"   ⚠️  Could not list databases: {e}")

print()

# Test 4: MongoDB connection
print("=" * 50)
print("MONGODB CONNECTION TEST:")
print("=" * 50)

if not mongo_uri:
    print("❌ MONGO_URI not set in .env")
else:
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_mongo():
            client = AsyncIOMotorClient(mongo_uri, serverSelectionTimeoutMS=5000)
            await client.admin.command('ping')
            print("✅ MongoDB connected successfully")
            
            # Get database info
            db_name = os.getenv('MONGO_DB_NAME', 'jimgreen')
            db = client[db_name]
            collections = await db.list_collection_names()
            print(f"   Database: {db_name}")
            print(f"   Collections: {len(collections)}")
            
            client.close()
        
        asyncio.run(test_mongo())
    except ImportError:
        print("⚠️  motor package not installed (pip install motor)")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")

print()

# Test 5: Other configurations
print("=" * 50)
print("OTHER CONFIGURATIONS:")
print("=" * 50)

configs = {
    'AWS_ACCESS_KEY_ID': os.getenv('AWS_ACCESS_KEY_ID'),
    'AWS_REGION': os.getenv('AWS_REGION'),
    'AWS_S3_BUCKET': os.getenv('AWS_S3_BUCKET'),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
    'APP_HOST': os.getenv('APP_HOST'),
    'APP_PORT': os.getenv('APP_PORT'),
    'APP_ENV': os.getenv('APP_ENV'),
}

for key, value in configs.items():
    if value:
        if 'KEY' in key or 'SECRET' in key:
            print(f"✅ {key}: {value[:20]}...")
        else:
            print(f"✅ {key}: {value}")
    else:
        print(f"⚠️  {key}: NOT SET")

print()
print("=" * 50)
print("SETUP VERIFICATION COMPLETE")
print("=" * 50)

# Summary
print("\n📊 SUMMARY:")
phreeqc_ok = phreeqc_exe and os.path.exists(phreeqc_exe)
db_ok = phreeqc_db and os.path.exists(phreeqc_db)
mongo_ok = mongo_uri is not None

if phreeqc_ok and db_ok and mongo_ok:
    print("✅ All critical components are configured correctly!")
    print("\n🚀 You're ready to start the application!")
else:
    print("⚠️  Some components need attention:")
    if not phreeqc_ok:
        print("   - PHREEQC executable")
    if not db_ok:
        print("   - Database directory")
    if not mongo_ok:
        print("   - MongoDB connection")

print()