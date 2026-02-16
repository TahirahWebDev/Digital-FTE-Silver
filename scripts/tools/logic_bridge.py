import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from scripts.tools.publisher import publish_content
from scripts.config import SILVER_APPROVED_FOLDER as APPROVED_FOLDER, SILVER_DONE_FOLDER as DONE_FOLDER, SUPPORTED_EXTENSIONS


class ApprovedFolderHandler(FileSystemEventHandler):
    """Handles file system events in the approved folder"""
    
    def on_created(self, event):
        """Called when a file is created in the approved folder"""
        if not event.is_directory:
            file_path = Path(event.src_path)
            if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.process_approved_file(file_path)
    
    def on_moved(self, event):
        """Called when a file is moved to the approved folder"""
        if not event.is_directory:
            dest_path = Path(event.dest_path)
            if dest_path.suffix.lower() in SUPPORTED_EXTENSIONS:
                self.process_approved_file(dest_path)
    
    def process_approved_file(self, file_path: Path):
        """Process an approved file by publishing and moving it to done folder"""
        print(f"New approved file detected: {file_path.name}")
        
        # Read the content of the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return
        
        # Publish the content
        success = publish_content(content)
        
        if success:
            # Move the file to the done folder with a timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Import config fresh to ensure latest values (important for tests)
            from scripts.config import SILVER_DONE_FOLDER
            done_folder_path = Path(SILVER_DONE_FOLDER)
            done_folder_path.mkdir(exist_ok=True)  # Ensure done folder exists
            
            # Create new filename with timestamp
            stem = file_path.stem
            suffix = file_path.suffix
            new_filename = f"{stem}_posted_{timestamp}{suffix}"
            new_file_path = done_folder_path / new_filename
            
            # Move the file
            try:
                shutil.move(str(file_path), str(new_file_path))
                print(f"File moved to done folder: {new_file_path.name}")
                
                # Verify the file was moved
                if new_file_path.exists():
                    print(f"Verification: File exists in done folder: {new_file_path}")
                else:
                    print(f"Error: File does not exist in done folder: {new_file_path}")
                    
            except Exception as e:
                print(f"Error moving file to done folder: {e}")
        else:
            print(f"Failed to publish content from {file_path.name}")


def start_logic_bridge():
    """Starts watching the approved folder for changes"""
    observer = Observer()
    handler = ApprovedFolderHandler()
    
    # Convert to Path object and resolve to absolute path
    from scripts.config import SILVER_APPROVED_FOLDER
    approved_path = Path(SILVER_APPROVED_FOLDER).resolve()
    
    if not approved_path.exists():
        print(f"Approved folder does not exist: {approved_path}")
        approved_path.mkdir(parents=True, exist_ok=True)
        print(f"Created approved folder: {approved_path}")
    
    observer.schedule(handler, str(approved_path), recursive=False)
    observer.start()
    
    print(f"Started watching approved folder: {approved_path}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping the logic bridge...")
    
    observer.join()


if __name__ == "__main__":
    start_logic_bridge()