import PyPDF2
import sys
import re

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'c:\Users\panay\.gemini\antigravity\scratch\books\quant trading.pdf'

with open(pdf_path, 'rb') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    
    # Extract text from pages 40-100 (estimated range for Chapter 2-4)
    for i in range(39, min(100, len(reader.pages))):
        text = reader.pages[i].extract_text()
        print(text)
        print("\n" + "="*80 + "\n")
