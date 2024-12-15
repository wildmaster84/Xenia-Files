import struct
import os, subprocess
from xex import Xex
def run_xextool_patch_and_decrypt(xex_file_path):
    xexp_file_path = xex_file_path + 'p'
    """Call xextool to patch and decrypt the XEX file."""
    try:
        if os.path.exists(xexp_file_path):
            # Step 1: Apply patch to the XEX file using xextool
            print("Patching the XEX file...")
            patch_command = ['xextool.exe', '-p', xexp_file_path, xex_file_path]
            patch_process = subprocess.run(patch_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Patch output: {patch_process.stdout.decode()}")

        # Step 2: Decrypt the XEX file using xextool
        print("Decrypting the XEX file...")
        decrypt_command = ['xextool.exe', '-e', 'u', xex_file_path]
        decrypt_process = subprocess.run(decrypt_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Decryption output: {decrypt_process.stdout.decode()}")
        
        # Step 3: Decompress the XEX file using xextool
        print("Decompressing the XEX file...")
        decompress_command = ['xextool.exe', '-c', 'u', xex_file_path]
        decompress_process = subprocess.run(decompress_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Decompress output: {decompress_process.stdout.decode()}")

        # The decrypted file should be saved at 'decrypted_xex_file_path'
        print(f"Decrypted XEX file saved as {xex_file_path}")

    except subprocess.CalledProcessError as e:
        print(f"Error during xextool process: {e.stderr.decode()}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def extract_images(data, output_folder):
    """Extract image files (e.g., PNG, JPEG) from a GPD file with enhanced logging."""
    os.makedirs(output_folder, exist_ok=True)

    IMAGE_SIGNATURES = {
        b'\x89PNG\r\n\x1a\n': b'IEND\xaeB`\x82',  # PNG
        b'\xFF\xD8\xFF': b'\xFF\xD9',  # JPEG
    }

    image_offsets = []
    for header, footer in IMAGE_SIGNATURES.items():
        print(f"Searching for images with header {header} and footer {footer}...")
        offset = 0
        while offset < len(data):
            offset = data.find(header, offset)
            if offset == -1:
                break

            end_offset = data.find(footer, offset)
            if end_offset == -1:
                print(f"Footer not found for header at offset {offset}.")
                break

            end_offset += len(footer)
            image_offsets.append((offset, end_offset))

            offset = end_offset

    extracted_count = len(image_offsets)
    if extracted_count == 0:
        print("No images found. Please verify the GPD structure.")
    else:
        print(f"Found {extracted_count} image(s). Extracting...")

        for i, (start, end) in enumerate(reversed(image_offsets)):
            file_extension = 'png' if data[start:start+4] == b'\x89PNG' else 'jpg'
            index = str(i + 1)
            filename = f"icon-{index.zfill(2)}.{'png' if file_extension == 'png' else 'jpg'}"
            output_path = os.path.join(output_folder, filename)

            with open(output_path, 'wb') as img_file:
                img_file.write(data[start:end])

            print(f"Extracted {filename} (offset: {start} to {end}).")


# Example usage
xex_file_path = "default.xex"  # Replace with the path to your XEX file

run_xextool_patch_and_decrypt(xex_file_path)

xex = Xex(xex_file_path)

xdbf_data = xex.extract_xdbf()

if xdbf_data:
    print(f"Extracted XDBF data and saved as GPD file.")
    extract_images(xdbf_data, xex.get_title_id())
    xex.extract_xlast(xdbf_data)
else:
    print("Failed to extract XDBF data.")
