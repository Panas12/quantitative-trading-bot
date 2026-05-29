import pandas as pd
import logging
from data_fetcher import DataFetcher
from cointegration_test import CointegrationAnalyzer

logging.basicConfig(level=logging.WARNING)

candidate_pairs = [
    ('JPM', 'WFC'),
    ('JPM', 'C'),
    ('WFC', 'C'),
    ('C', 'BAC'),
    ('BAC', 'WFC'),
    ('PFE', 'MRK'),
    ('PFE', 'JNJ'),
    ('ABBV', 'BMY'),
    ('UNH', 'ELEV'),
    ('LMT', 'RTX')
]

print(f"{'Pair':<15} | {'Engle-Granger p-val':<20} | {'ADF p-val':<15} | {'Half-life':<10}")
print("-" * 70)

for sym1, sym2 in candidate_pairs:
    try:
        fetcher = DataFetcher(sym1, sym2)
        # Fetch 2 years of data
        data1, data2 = fetcher.fetch_data(start_date='2024-01-01')
        
        analyzer = CointegrationAnalyzer(data1['close'], data2['close'], sym1, sym2)
        results = analyzer.full_analysis()
        
        eg_pval = results['cointegration_pvalue']
        adf_pval = results['adf_pvalue']
        half_life = results['half_life']
        
        print(f"{sym1}-{sym2:<10} | {eg_pval:<20.4f} | {adf_pval:<15.4f} | {half_life:<10.2f}")
    except Exception as e:
        print(f"{sym1}-{sym2:<10} | Error: {e}")
