import pandas as pd
from collections import Counter
from pipeline.cleaning.revenue import parse_revenue

df = pd.read_csv("data/input/tech_news.csv", dtype=str)
c = Counter(parse_revenue(v).status for v in df.revenue)
print(c)
