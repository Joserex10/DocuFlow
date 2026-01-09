from core.capture import CaptureEngine
from core.exporter import ReportExporter
import json
import sys

def main():
    print("Initializing DocuFlow Capture...")
    engine = CaptureEngine()
    
    try:
        engine.start()
    except KeyboardInterrupt:
        print("\nStopped by user.")
        engine.stop()
    
    # Process collected data
    steps = engine.get_steps()
    print(f"\nCapture Complete. {len(steps)} steps recorded.")
    
    if not steps:
        print("No steps captured. Exiting.")
        return

    # Export Report
    exporter = ReportExporter(steps)
    exporter.generate_pdf()
    
    # Optional Cleanup
    response = input("\nDo you want to delete temporary screenshots? (y/n): ").strip().lower()
    if response == 'y':
        exporter.cleanup_temp()

if __name__ == "__main__":
    main()
