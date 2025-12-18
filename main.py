import os
import shutil
import time
from processor import process_excel_file

# Configuration for Local Folders
BASE_DIR = os.getcwd()
INPUT_DIR = os.path.join(BASE_DIR, 'input_files')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output_files')
PROCESSED_DIR = os.path.join(BASE_DIR, 'processed_files')

def main():
    print("Starting Local Excel Processor...")
    print(f"Monitoring folder: {INPUT_DIR}")
    print(f"Saving to folder:  {OUTPUT_DIR}")
    print("-" * 30)

    # Ensure directories exist
    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    processed_count = 0

    # 1. List files
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.xlsx') and not f.startswith('~$')]
    
    if not files:
        print("No Excel files found in the input folder.")
        return

    print(f"Found {len(files)} files to process.")

    for filename in files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, f"processed_{filename}")
        
        print(f"Processing '{filename}'...")
        
        success = process_excel_file(input_path, output_path)
        
        if success:
            print(f" - Saved to: {output_path}")
            
            # Move source file to 'processed_files' so we don't process it again
            destination = os.path.join(PROCESSED_DIR, filename)
            # Handle duplicate names in processed folder
            if os.path.exists(destination):
                base, ext = os.path.splitext(filename)
                timestamp = int(time.time())
                destination = os.path.join(PROCESSED_DIR, f"{base}_{timestamp}{ext}")
            
            shutil.move(input_path, destination)
            print(f" - Moved source file to: {destination}")
            processed_count += 1
        else:
            print(f" - Failed to process {filename}")

    print("-" * 30)
    print(f"Done. Processed {processed_count} files.")

if __name__ == "__main__":
    main()
