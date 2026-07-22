import requests
from bs4 import BeautifulSoup
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def debug_dom():
    url = "https://dsebd.org/displayCompany.php?name=SQURPHARMA"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')

    print("=== NAV Search ===")
    for el in soup.find_all(text=re.compile(r'NAV', re.I)):
        parent = el.parent
        print(f"Parent: {parent.name}, text: {parent.text.strip()}")
        # Print children/siblings
        siblings = list(parent.find_next_siblings())
        print(f"Siblings: {[s.text.strip() for s in siblings]}")
        # If it is inside a tr, print the whole tr values
        tr = parent.find_parent('tr')
        if tr:
            print(f"TR values: {[td.text.strip() for td in tr.find_all('td')]}")
        print("-" * 50)

    print("=== CFO / NOCFPS Search ===")
    for el in soup.find_all(text=re.compile(r'NOCFPS|Operating Cash', re.I)):
        parent = el.parent
        print(f"Parent: {parent.name}, text: {parent.text.strip()}")
        tr = parent.find_parent('tr')
        if tr:
            print(f"TR values: {[td.text.strip() for td in tr.find_all('td')]}")
        print("-" * 50)

if __name__ == '__main__':
    debug_dom()
