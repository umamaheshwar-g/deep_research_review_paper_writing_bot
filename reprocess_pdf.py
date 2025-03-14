from pdf_processor_pymupdf import process_pdf

# Reprocess the PDF file
pdf_path = 'downloads/b299c41b-caa8-4313-b228-a63eea8ade65/papers/paper_39b5cef1ffe9.pdf'
uuid = 'b299c41b-caa8-4313-b228-a63eea8ade65'

print(f"Reprocessing PDF: {pdf_path}")
process_pdf(pdf_path, uuid)
print("PDF reprocessing completed") 