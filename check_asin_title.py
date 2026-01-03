import pandas as pd
import os

ARTIFACTS_DIR = 'artifacts'

df = pd.read_parquet(os.path.join(ARTIFACTS_DIR, "items_metadata.parquet"))
row = df[df['asin'] == 'B001D0OSLS']
print(row.to_dict(orient='records'))
