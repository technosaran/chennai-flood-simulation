import docx
import os
import sys
from report_styles import setup_page_layout, add_page_number_to_section
from report_frontmatter import generate_front_matter
from report_chapter1 import generate_chapter_1
from report_chapter2 import generate_chapter_2
from report_chapter3 import generate_chapter_3
from report_chapter4 import generate_chapter_4
from report_chapter5 import generate_chapter_5
from report_chapter6 import generate_chapter_6
from report_appendices import generate_appendices
from report_references import generate_references

def main():
    print("=" * 70)
    print("BUILDING OFFICIAL PANIMALAR PROJECT REPORT (TEAM C24)")
    print("AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform")
    print("=" * 70)

    OUTPUT_DIR = r"c:\Users\saran\Desktop\project X\project document"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    DOCX_NAME = "C24 - AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform.docx"
    PDF_NAME = "C24 - AI-Driven Crisis Resource Intelligence & Autonomous Logistics Platform.pdf"
    DOCX_PATH = os.path.join(OUTPUT_DIR, DOCX_NAME)
    PDF_PATH = os.path.join(OUTPUT_DIR, PDF_NAME)

    doc = docx.Document()

    # Section 1: Front Matter (Roman numerals, cover page has no page number)
    sec_front = doc.sections[0]
    setup_page_layout(sec_front, left=1.25, right=1.0, top=1.0, bottom=1.0)
    sec_front.different_first_page_header_footer = True
    add_page_number_to_section(sec_front, start_at=1, num_format='lowerRoman')

    print("[1/9] Generating Front Matter (Cover, Bonafide, Dec, Ack, Abstract, TOC, Tables, Figures, Symbols)...")
    generate_front_matter(doc)

    # Section 2: Chapters & Body (Decimal numerals starting at 1)
    sec_body = doc.add_section()
    setup_page_layout(sec_body, left=1.25, right=1.0, top=1.0, bottom=1.0)
    sec_body.different_first_page_header_footer = False
    add_page_number_to_section(sec_body, start_at=1, num_format='decimal')

    print("[2/9] Generating Chapter 1: INTRODUCTION...")
    generate_chapter_1(doc)

    print("[3/9] Generating Chapter 2: LITERATURE SURVEY...")
    generate_chapter_2(doc)

    print("[4/9] Generating Chapter 3: PROPOSED SYSTEM...")
    generate_chapter_3(doc)

    print("[5/9] Generating Chapter 4: SYSTEM IMPLEMENTATION...")
    generate_chapter_4(doc)

    print("[6/9] Generating Chapter 5: RESULTS AND DISCUSSION...")
    generate_chapter_5(doc)

    print("[7/9] Generating Chapter 6: CONCLUSION AND FUTURE WORK...")
    generate_chapter_6(doc)

    print("[8/9] Generating APPENDICES (SDGs, Source Code, Screenshots)...")
    generate_appendices(doc)

    print("[9/9] Generating REFERENCES (37 IEEE verified citations)...")
    generate_references(doc)

    print(f"\nSaving Word Document: {DOCX_PATH} ...")
    doc.save(DOCX_PATH)
    file_size_mb = os.path.getsize(DOCX_PATH) / (1024 * 1024)
    print(f"Word document saved successfully! File size: {file_size_mb:.2f} MB")

    print("\nExporting to PDF via Microsoft Word COM Automation...")
    try:
        import win32com.client
        import time
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc_com = word.Documents.Open(os.path.abspath(DOCX_PATH))
        # 17 = wdFormatPDF
        doc_com.SaveAs(os.path.abspath(PDF_PATH), FileFormat=17)
        doc_com.Close(SaveChanges=0)
        try:
            word.Quit()
        except Exception:
            pass
        time.sleep(1)
        if os.path.exists(PDF_PATH):
            pdf_size_mb = os.path.getsize(PDF_PATH) / (1024 * 1024)
            print(f"PDF exported successfully! File size: {pdf_size_mb:.2f} MB")
            
            # Count pages using fitz
            try:
                import fitz
                p_doc = fitz.open(PDF_PATH)
                print(f"Total Page Count: {len(p_doc)} pages")
            except Exception as e:
                print(f"Could not read PDF pages: {e}")
        else:
            print("Warning: PDF file was not created.")
    except Exception as e:
        print(f"PDF export encountered error: {e}")

    print("\n" + "=" * 70)
    print("PROJECT REPORT GENERATION COMPLETE!")
    print("=" * 70)

if __name__ == "__main__":
    main()
