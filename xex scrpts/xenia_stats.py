import xml.etree.ElementTree as ET
import json
import chardet
import os
import re


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
            if field.find('xlast:Property', ns) is None:
                continue;
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
    # Write to the JSON file
    with open(json_file, 'w') as text_file:
        print("{}".format(properties), file=text_file)
        text_file.close()
        
    print("Successfully converted XML to Xenia stats")

def parse_achievements_to_json(xml_file, json_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Namespace dictionary
    ns = {'xlast': 'http://www.xboxlive.com/xlast'}

    achievements = {}
    index = 0

    # Get the supported locales from the XML
    supported_locales = {}
    for supported_locale in root.findall('.//xlast:SupportedLocale', ns):
        locale = supported_locale.get('locale')
        supported_locales[locale] = []

    # Process Images
    image_paths = {}
    for image in root.findall('.//xlast:Image', ns):
        image_id = image.get('id')
        image_path = image.find('xlast:Path', ns).text if image.find('xlast:Path', ns) is not None else None
        if image_path:
            image_paths[image_id] = image_path

    # Process Achievements
    for achievement in root.findall('.//xlast:Achievement', ns):
        index += 1
        achievement_id = achievement.get('id')
        achievement_number = int(achievement_id)  # Assuming achievement ID is numeric and represents the number
        achievement_secret = achievement.get('showUnachieved')
        achievement_type = achievement.get('achievementType')
        descriptionId = achievement.get('descriptionStringId')
        nameId = achievement.get('titleStringId')
        howtoId = achievement.get('unachievedStringId')
        achievement_credit = achievement.get('cred')
        
        # Attempt to match the imageId to the image path from the Image tags
        image_id = achievement.get('imageId')
        image_path = f"{index:02d}.png"

        # Create regex patterns for achievement name, description, and how-to
        achName = re.compile(rf"ACH(?:_)?(?:IEVEMENT_)?{achievement_number:02d}_NAME|ACH(?:_)?(?:IEVEMENT_)?{achievement_number}_NAME")
        achDesc = re.compile(rf"ACH(?:_)?(?:IEVEMENT_)?{achievement_number:02d}_DESC|ACH(?:_)?(?:IEVEMENT_)?{achievement_number}_DESC")
        achHow = re.compile(rf"ACH(?:_)?(?:IEVEMENT_)?{achievement_number:02d}_HOWTO|ACH(?:_)?(?:IEVEMENT_)?{achievement_number}_HOWTO")

        # Prepare the structure for translations
        translations = {
            'name': {},
            'description': {},
            'howto': {}
        }
        name = root.find(f".//xlast:LocalizedString[@id='{nameId}']", ns)
        desc = root.find(f".//xlast:LocalizedString[@id='{descriptionId}']", ns)
        how = root.find(f".//xlast:LocalizedString[@id='{howtoId}']", ns)
        
        for translation in name.findall('xlast:Translation', ns):
                    locale = translation.get('locale')
                    if locale in supported_locales:
                        translations['name'][locale] = translation.text
        
        for translation in desc.findall('xlast:Translation', ns):
                    locale = translation.get('locale')
                    if locale in supported_locales:
                        translations['description'][locale] = translation.text

        for translation in how.findall('xlast:Translation', ns):
                    locale = translation.get('locale')
                    if locale in supported_locales:
                        translations['howto'][locale] = translation.text

        # Add to achievements dictionary with the image path set
        achievements[achievement_id] = {
            "text": translations,
            "isSecret": achievement_secret,
            "type": achievement_type,
            "credits": achievement_credit,
            "imageId": image_path  # Set imageId to the path found in the Image tag
        }

    # Write to the JSON file
    with open(json_file, 'w', encoding='utf-8') as text_file:
        json.dump({"Achievements": achievements}, text_file, indent=4, ensure_ascii=False)

    print(f"Successfully converted XML to JSON and saved to {json_file}")

def convert_to_utf16(file_path):
    with open(file_path, 'rb') as file:
        content = file.read()

    # Detect the encoding
    detected_encoding = chardet.detect(content)['encoding']
    print(f"Detected encoding: {detected_encoding}")

    encodings_to_try = ['utf-16', 'gbk', 'big5', 'latin1', 'gb2312']

    for encoding in encodings_to_try:
        try:
            decoded_content = content.decode(encoding)
            print(f"Successfully decoded with {encoding}")
            break
        except (UnicodeDecodeError, TypeError) as e:
            print(f"Failed to decode with {encoding}: {e}")
    else:
        print("No need to decode the file with all attempted encodings.")

    with open(file_path, 'w', encoding='utf-16') as file:
        file.write(decoded_content)
    print("File converted to UTF-16.")
# File paths
xml_file_path = input("Enter the XML file name: ")
        
# Convert XML to UTF-16
convert_to_utf16(xml_file_path)
# Convert XML to JSON
tree = ET.parse(xml_file_path)
root = tree.getroot()
ns = {'xlast': 'http://www.xboxlive.com/xlast'}
titleId = root.find('.//xlast:GameConfigProject', ns).get('titleId').replace('0x', '')

if not os.path.exists(titleId):
    os.makedirs(titleId)

parse_xml_to_json(xml_file_path, '{}/stats.json'.format(titleId))
parse_achievements_to_json(xml_file_path, '{}/achievements.json'.format(titleId))
