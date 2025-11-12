"""
Test script to verify AirSig installation and dependencies
Run this before launching the main application
"""

import sys
import importlib

print("=" * 60)
print("AirSig - Installation Test")
print("=" * 60)
print()

# Python version check
print(f"✓ Python version: {sys.version}")
print()

# Required dependencies
dependencies = {
    'cv2': 'opencv-python',
    'mediapipe': 'mediapipe',
    'numpy': 'numpy',
    'PIL': 'Pillow',
    'tkinter': 'tkinter (built-in)'
}

print("Checking dependencies...")
print("-" * 60)

missing = []
installed = []

for module, package in dependencies.items():
    try:
        mod = importlib.import_module(module)
        version = getattr(mod, '__version__', 'unknown')
        print(f"✓ {package}: {version}")
        installed.append(package)
    except ImportError:
        print(f"✗ {package}: NOT FOUND")
        missing.append(package)

print("-" * 60)
print()

# Results
if not missing:
    print("✓ All dependencies installed successfully!")
    print()
    print("You can now run AirSig:")
    print("  python main.py")
    print()
    
    # Test camera
    print("Testing webcam access...")
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                h, w, c = frame.shape
                print(f"✓ Webcam detected: {w}x{h}")
            else:
                print("✗ Webcam detected but cannot read frames")
            cap.release()
        else:
            print("✗ Cannot open webcam (may be in use by another app)")
    except Exception as e:
        print(f"✗ Webcam test failed: {e}")
    
    print()
    print("=" * 60)
    print("Installation test complete! Ready to run AirSig.")
    print("=" * 60)
    
else:
    print("✗ Missing dependencies:")
    for pkg in missing:
        print(f"  - {pkg}")
    print()
    print("Install missing dependencies with:")
    print("  pip install opencv-python mediapipe numpy pillow")
    print()
    print("Or use requirements.txt:")
    print("  pip install -r requirements.txt")
    print()
    print("=" * 60)
    sys.exit(1)
