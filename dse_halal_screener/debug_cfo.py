import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_cfo():
    url = "https://dsebd.org/displayCompany.php?name=SQURPHARMA"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    print("=== Scanning text for NOCFPS / Operating Cash ===")
    for el in soup.find_all(string=re.compile(r'NOCFPS|Operating Cash|Flow', re.I)):
        parent = el.parent
        print(f"Parent: {parent.name}, text: {el.strip()}")
        # Check parents to trace table
        p = parent
        for i in range(3):
            if p:
                print(f"  Parent {i+1}: {p.name} {p.get('class')} {p.get('id')}")
                p = p.parent
        print("-" * 50)

if __name__ == '__main__':
    debug_cfo()
