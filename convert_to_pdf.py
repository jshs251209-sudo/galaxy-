from markdown_pdf import Section, MarkdownPdf

def convert_md_to_pdf():
    pdf = MarkdownPdf(toc_level=2)
    with open("Comprehensive_Project_Report.md", "r", encoding="utf-8") as f:
        content = f.read()
    pdf.add_section(Section(content, paper_size="A4"))
    pdf.save("Comprehensive_Project_Report.pdf")

if __name__ == "__main__":
    convert_md_to_pdf()
