import os

def rename_images(directory):
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    image_files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]
    
    # Sort files by modification time (oldest to newest)
    image_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    
    # Rename files with a numbered format based on age
    for index, file in enumerate(image_files, start=1):
        new_name = f"{str(index).zfill(2)}.{file.split('.')[-1]}"
        old_path = os.path.join(directory, file)
        new_path = os.path.join(directory, new_name)
        
        os.rename(old_path, new_path)
        print(f"Renamed {file} to {new_name}")

# Example usage
rename_images(input('Enter title id: '))
