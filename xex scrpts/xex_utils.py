import struct
class XEXParserWithXDBF:
    SECTION_NAMES = {
        0x0001: "Metadata",
        0x0002: "Image",
        0x0003: "String Table",
        # Add additional mappings here as necessary
    }
    
    METADATA_IDS = {
        '58444246': "XDBF",
        '58535443': "XSTC",
        '58414348': "XACH",
        '58505250': "XPRP",
        '58435854': "XCTX",
        '58564332': "XVC2",
        '584D4154': "XMAT",
        '58535243': "XSRC",
        '58544844': "XTHD",
        '5850424D': "XPBM",
        '58474141': "XGAA",
        '58495442': "XITB",
        # Add more metadata ID mappings here if needed
    }

    def __init__(self, filepath):
        with open(filepath, "rb") as f:
            self.data = f.read()

    def parse(self):
        print("Parsing XEX...")
        self.parse_header()
        xdbf_data = self.extract_xdbf()
        if xdbf_data:
            self.parse_xdbf(xdbf_data)
        else:
            print("No embedded XDBF data found.")

    def parse_header(self):
        magic, base_address = struct.unpack_from(">2I", self.data, 0)
        if magic != 0x58455832:  # "XEX2" magic
            raise ValueError("Not a valid XEX file!")
        print(f"XEX Magic: {hex(magic)}")
        print(f"Base Address: {hex(base_address)}")

    def extract_xdbf(self):
        print("Searching for XDBF data...")
        xdbf_magic = 0x58444246  # "XDBF" magic
        for offset in range(len(self.data) - 4):
            potential_magic, = struct.unpack_from(">I", self.data, offset)
            if potential_magic == xdbf_magic:
                print(f"XDBF found at offset {hex(offset)}")
                return self.data[offset:]
        return None

    def parse_xdbf(self, xdbf_data):
        print("\n--- Parsing Embedded XDBF ---")
        self.parse_xdbf_header(xdbf_data)
        self.parse_xdbf_sections(xdbf_data)

    def parse_xdbf_header(self, xdbf_data):
        magic, version, entry_count, entry_used = struct.unpack_from(">4I", xdbf_data, 0)
        print(f"XDBF Magic: {hex(magic)}")
        print(f"Version: {version}")
        print(f"Entry Count: {entry_count}")
        print(f"Entries Used: {entry_used}")

    def parse_xdbf_sections(self, xdbf_data):
        offset = 0x18  # Entries start after the header
        entry_count, = struct.unpack_from(">I", xdbf_data, 0x8)
        print("\n--- XDBF Sections ---")
        for i in range(entry_count):
            entry_offset = offset + i * 18  # Each entry is 18 bytes
            section, entry_id, entry_offset, entry_size = struct.unpack_from(">HQLL", xdbf_data, entry_offset)
            section_name = self.SECTION_NAMES.get(section, f"Unknown Section {hex(section)}")
            print(f"Section: {section_name}, ID: {entry_id}, Offset: {entry_offset}, Size: {entry_size}")

            #if section == 0x0001:  # Metadata Section
            #    self.parse_metadata(xdbf_data, entry_offset, entry_size)

        # Additional section parsing logic can be added here
    
    def parse_metadata(self, xdbf_data, entry_offset, entry_size):
        metadata_data = xdbf_data[entry_offset:entry_offset + entry_size]
        metadata_id = metadata_data[:4]  # First 4 bytes represent the metadata ID
        hex_string = ''.join(f'{byte:02x}' for byte in metadata_id)
        metadata_name = self.METADATA_IDS.get(hex_string, f"Unknown Metadata {hex_string}")
        print(f"Metadata ID: {metadata_id}, Name: {metadata_name}")


def main():
    xex_filepath = "default.xex"

    print("\n--- Parsing XEX with Embedded XDBF ---")
    parser = XEXParserWithXDBF(xex_filepath)
    parser.parse()


if __name__ == "__main__":
    main()
