import json
import os
import sys

def convert():
    json_data = os.getenv('COOKIE_JSON_DATA')
    if not json_data:
        print("Error: No COOKIE_JSON_DATA found in environment.")
        sys.exit(1)

    try:
        cookies = json.loads(json_data)
        with open('cookies.txt', 'w', encoding='utf-8') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# http://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n\n")
            
            for c in cookies:
                domain = c.get('domain', '')
                # Netscape format requires specific tab-separated fields
                host_only = "TRUE" if domain.startswith('.') else "FALSE"
                path = c.get('path', '/')
                secure = "TRUE" if c.get('secure', False) else "FALSE"
                expires = int(c.get('expirationDate', 0))
                name = c.get('name', '')
                value = c.get('value', '')
                
                f.write(f"{domain}\t{host_only}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
        print("Successfully created cookies.txt")
    except Exception as e:
        print(f"Failed to convert: {e}")
        sys.exit(1)

if __name__ == "__main__":
    convert()
