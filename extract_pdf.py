import PyPDF2
import sys

# Set UTF-8 encoding for output
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = r'c:\Users\panay\.gemini\antigravity\scratch\books\quant trading.pdf'

with open(pdf_path, 'rb') as pdf_file:
    reader = PyPDF2.PdfReader(pdf_file)
    print(f"Total pages: {len(reader.pages)}\n")
    
    # Extract text from first 30 pages (covering intro and main strategies)
    for i in range(min(30, len(reader.pages))):
        text = reader.pages[i].extract_text()
        print(f"\n{'='*80}")
        print(f"PAGE {i+1}")
        print(f"{'='*80}")
        print(text)
