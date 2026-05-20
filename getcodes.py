import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://airportcod.es/search-data.txt?v=5590971c"

response = requests.get(url=url)
codes = []

data = response.text
with open('codes.txt', "w", encoding="utf-8") as f:
    f.write(data)

with open("codes.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()
for line in lines:
    code = line[:3]
    codes.append({
        "codes":code.upper(),
        })

df = pd.DataFrame(codes)
df.index.name = "id"
df.to_csv("airports.csv", index=True)




