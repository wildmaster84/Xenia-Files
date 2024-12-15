from struct import *
import zlib
from Crypto.Cipher import AES
import xml.etree.ElementTree as ET
import struct


class Xex:

    RETAIL_KEY = b'\x20\xB1\x85\xA5\x9D\x28\xFD\xC3\40\x58\x3F\xBB\x08\x96\xBF\x91'
    XSRC_SIGNATURE = b'XSRC'

    def __init__(self, filename):
        data_counter = 0
        self.optional_headers = []
        self.sections = []
        with open(filename, 'rb') as file:
            filedata = file.read()
            
        if not filedata and not filename:
            print('invalid xex provided')
            exit(1)
        if filename:
            self.data = open(filename, 'rb').read()
        elif filedata:
            self.data = filedata

        #unpack the header
        header_sting = '>4s L L L L L'
        data_counter += calcsize(header_sting)
        self.signature, self.module_flags, self.exe_offset, self.unk, self.cert_offset, self.header_count\
            = unpack(header_sting, self.data[0:data_counter])
        if self.signature != b'XEX2':
            print('signature mismatch', self.signature)
            exit(1)
        optional_header_string = '>L L'
        for i in range(self.header_count):
            self.optional_headers.append(unpack(optional_header_string,
                                                self.data[data_counter:data_counter+calcsize(optional_header_string)]))
            data_counter += 8
        for h in self.optional_headers:
            key = h[0]
            if key == 0x000002FF:  #XEX_HEADER_RESOURCE_INFO
                self.resource_info_count = int((h[0] - 4) / 16)
                self.resource_infos = []
                for i in range(self.resource_info_count):
                    self.resource_infos.append(unpack('>8s L L', self.data[h[1] + 4 + (i * 16):h[1] + 20 + (i * 16)]))
            elif key == 0x000003FF:  #XEX_HEADER_FILE_FORMAT_INFO
                self.info_size, self.encryption_type, self.compession_type = unpack('> L H H ', self.data[h[1]:h[1] + 8])
                if self.compession_type == 1:
                    #XEX_COMPRESSION_BASIC
                    self.compression_type = 'basic'
                    self.block_cont = int((self.info_size - 8) / 8)
                    self.blocks = []
                    for i in range(self.block_cont):
                        self.blocks.append(unpack('> L L', self.data[h[1] + 8 + (i * 8): h[1] + 8 + (i * 8) + 8]))
                elif self.compession_type == 2:
                    #XEX_COMPRESSION_NORMAL
                    self.compression_type = 'normal'
                    self.window_size, self.block_size, self.block_hash = unpack('> L L 20s', self.data[h[1] + 8: h[1] + 36])
            elif key == 0x00030000:  #XEX_HEADER_SYSTEM_FLAGS
                self.system_flags = h[1]
            elif key == 0x000005FF:  #XEX_HEADER_DELTA_PATCH_DESCRIPTOR
                pass
            elif key == 0x00000405:  #XEX_HEADER_DELTA_PATCH_DESCRIPTOR
                pass
            elif key == 0x00010100:  #XEX_HEADER_ENTRY_POINT
                self.entry_point = h[1]
            elif key == 0x00010201:  #XEX_HEADER_IMAGE_BASE_ADDRESS
                self.base_image_address = h[1]
            elif key == 0x000183FF:  #XEX_HEADER_ORIGINAL_PE_NAME
                name_length = unpack('>L', self.data[h[1]:h[1] + 4])[0]
                self.original_pe_name = self.data[h[1] + 4:h[1] + 4 + name_length - 1].decode()
            elif key == 0x00040006:  #XEX_HEADER_EXECUTION_INFO
                execution_info_string = '>L L L L B B B B L'
                self.media_id, self.version, self.base_version, self.title_id, self.platform, self.execution_table, \
                self.disk_number, self.disk_count, self.savegame_id = unpack(execution_info_string, self.data[h[1]:
                                                                                h[1] + calcsize(execution_info_string)])
            elif key == 0x00040310:  #XEX_HEADER_GAME_RATINGS
                game_ratings_string = '> B B B B B B B B B B B B'
                self.esrb, self.pegi, self.pegifi, self.pegipt, self.bbfc, self.cero, self.usk, self.oflcau, \
                self.oflcnz, self.mrb, self.brazil, self.fpb = unpack(game_ratings_string,
                                                                      self.data[h[1]:h[1] + calcsize(game_ratings_string)])
            elif key == 0x00020104:  #XEX_HEADER_TLS_INFO
                tls_string = '>L L L L'
                self.tls_slot_count, self.tls_raw_data_address, self.tls_data_size, self.tls_raw_data_size = unpack(
                    tls_string, self.data[h[1]:h[1] + calcsize(tls_string)]
                )
            elif key == 0x00020200:  #XEX_HEADER_DEFAULT_STACK_SIZE
                self.exe_stack_size = unpack('>L', self.data[h[1]:h[1] + 4])[0]
            elif key == 0x00020401:  #XEX_HEADER_DEFAULT_HEAP_SIZE
                self.exe_heap_size = unpack('>L', self.data[h[1]:h[1] + 4])[0]

        data_counter = self.cert_offset
        loader_string = '> L L 256s L L L 20s L 20s 16s 16s L 20s L L L'
        self.loader_header_size, self.loader_image_size, self.loader_rsa_sig, self.loader_unklength,\
        self.loader_image_flags, self.loader_load_address, self.loader_section_digest, self.loader_import_table_count,\
        self.loader_import_table_digest, self.loader_media_id, self.loader_file_key, self.loader_export_table,\
        self.loader_header_digest, self.loader_game_regions, self.loader_media_flags, self.section_count = \
            unpack(loader_string, self.data[data_counter:data_counter + calcsize(loader_string)])
        data_counter += calcsize(loader_string)

        section_string = '> L L 20s'
        for section in range(self.section_count):
            self.sections.append(unpack(section_string, self.data[data_counter:data_counter + calcsize(section_string)]))
            data_counter += calcsize(section_string)

    def decrypt_header_key(self):
        cipher = AES.new(self.RETAIL_KEY)
        cipher.block_size = 16
        return cipher.decrypt(self.loader_file_key)

    def convert_virtual_address(self, address):
        return address - self.base_image_address
    
    def get_title_id(self):
        return format(self.title_id, '08X')

    def extract_xdbf(self):
        """Extract XDBF (Achievement Icons) from the XEX file."""
        xdbf_signature = b'XDBF'
        xdbf_offset = self.data.find(xdbf_signature)

        if xdbf_offset == -1:
            print("XDBF signature not found in the XEX file.")
            return None

        print(f"XDBF signature found at offset {xdbf_offset}. Extracting data...")

        # Extract the XDBF data starting from the signature
        xdbf_data = self.data[xdbf_offset:]
        
        #gpd_file_path = f"{format(self.title_id, '08X')}.xdbf"
        #with open(gpd_file_path, 'wb') as gpd_file:
        #    gpd_file.write(xdbf_data)

        return xdbf_data
        
    def extract_xlast(self, xdbf_data):
        
        if not xdbf_data:
            print("No XDBF data found, unable to extract XLast.")
            return
        
        xlast_start = xdbf_data.find(b'<XLast')
        xlast_end = xdbf_data.find(b'</XLast>') + len(b'</XLast>')

        if xlast_start == -1 or xlast_end == -1:
            print("XLast tags not found in XDBF data.")
            return
        
        self.xlast_data = xdbf_data[xlast_start:xlast_end]
        with open("output_xlast.xml", 'wb') as file:
            file.write(self.xlast_data)

        print("XLast data extracted successfully.")
        return self.xlast_data