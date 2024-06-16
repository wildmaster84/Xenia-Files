import xml.etree.ElementTree as ET
import json
import chardet

def parse_xml_to_json(xml_file, json_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
        
    # Namespace dictionary
    ns = {'xlast': 'http://www.xboxlive.com/xlast'}

    properties = "{\n    \"properties\": {\n        "
    # Find all StatsView elements
    for stats_view in root.findall('.//xlast:StatsView', ns):
        stats_view_id = stats_view.get('id')
        stat_hex = f"0x{int(stats_view_id):08x}"
        
        # Find all Field elements within each StatsView
        for field in stats_view.find('xlast:Columns', ns).findall('xlast:Field', ns):
            stat_id = field.get('attributeId')
            friendly_name = field.get('friendlyName')
            property_id = field.find('xlast:Property', ns).get('id')
            type = field.find('xlast:Property/xlast:Aggregation', ns).get('type')
            properties = properties + "\"" + str(property_id) + "\": {\n            "
            properties = properties + "\"info\": \"" + friendly_name + "\",\n            "
            properties = properties + "\"method\": \"" + type.lower() + "\",\n            "
            properties = properties + "\"statId\": " + stat_id + "\n        },\n        "
    properties = properties[:-10]
    properties = properties + "\n    }\n}"
    print(properties)
    # Write to the JSON file
    with open(json_file, 'w') as text_file:
        print("{}".format(properties), file=text_file)
        text_file.close()
        
    print("Successfully converted XML to Xenia stats")

def convert_to_utf16(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()

    # Detect the encoding
    detected_encoding = chardet.detect(content)['encoding']
    print(f"Detected encoding: {detected_encoding}")

    encodings_to_try = [detected_encoding, 'utf-16', 'gbk', 'big5', 'latin1', 'gb2312']

    for encoding in encodings_to_try:
        try:
            decoded_content = content.decode(encoding)
            print(f"Successfully decoded with {encoding}")
            break
        except (UnicodeDecodeError, TypeError) as e:
            print(f"Failed to decode with {encoding}: {e}")
    else:
        raise ValueError("Failed to decode the file with all attempted encodings.")

    with open(file_path, 'w', encoding='utf-16') as file:
        file.write(decoded_content)
    print("File converted to UTF-16.")
# File paths
xml_file_path = input("Enter the XML file name (including path if not in the same directory): ")
json_file_path = 'stats.json'

# Convert XML to UTF-16
convert_to_utf16(xml_file_path)
# Convert XML to JSON
parse_xml_to_json(xml_file_path, json_file_path)
