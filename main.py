"""
AirSig - Enhanced Real-Time Finger Writing Application
Main entry point to launch the Tkinter GUI
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import main

if __name__ == "__main__":
    print("=" * 60)
    print("AirSig - Real-Time Finger Writing Application")
    print("=" * 60)
    print("Starting application...")
    print("\nGesture Guide:")
    print("  ✏️  Index Finger - Draw")
    print("  👆 Index + Middle - Navigate")
    print("  🖐️  All Fingers - Erase")
    print("  ✊  Fist - Clear Canvas")
    print("  🤚  Palm Open - Pause")
    print("  🤏  Pinch - Change Settings")
    print("\nLaunching GUI...")
    print("=" * 60)
    
    try:
        main()
    except KeyboardInterrupt:
        print("\nApplication closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
