
import json
import os

def fix_json_files(directory):
    """
    Reads all JSON files in a directory, parses them, and writes them back out
    to ensure proper escaping of special characters.
    """
    print(f"Scanning and fixing JSON files in: {directory}")
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"  - Fixed: {filename}")

            except json.JSONDecodeError as e:
                print(f"  - ERROR: Could not decode {filename}. Reason: {e}")
            except Exception as e:
                print(f"  - ERROR: An unexpected error occurred with {filename}. Reason: {e}")

if __name__ == '__main__':
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    KNOWLEDGE_BASE_DIR = os.path.join(SCRIPT_DIR, 'knowledge_base')
    fix_json_files(KNOWLEDGE_BASE_DIR)
