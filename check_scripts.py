import os

print("=" * 70)
print("CHECKING YOUR SCRIPTS")
print("=" * 70)
print()

scripts = ['verify_setup.py', 'test_setup.py', 'check_env.py']

for script in scripts:
    if os.path.exists(script):
        print(f"📄 {script}")
        print("-" * 70)
        with open(script, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Show first 20 lines
        for i, line in enumerate(lines[:20], 1):
            print(f"{i:3d}: {line.rstrip()}")
        
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        print()
    else:
        print(f"❌ {script} not found")
        print()

# Check the actual .env file
print("=" * 70)
print(".ENV FILE - LINE 123")
print("=" * 70)

if os.path.exists('.env'):
    with open('.env', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) >= 123:
        print(f"Line 123: {lines[122]}")
        print()
        print("Hex representation:")
        hex_data = ' '.join(f'{ord(c):02x}' for c in lines[122][:50])
        print(hex_data)
        print()
        
        # Check for the exact string
        if 'x64' in lines[122] and 'bin' in lines[122]:
            print("✅ Contains 'x64' and 'bin'")
        if 'x6in' in lines[122]:
            print("❌ Contains 'x6in' (typo!)")
            
print()