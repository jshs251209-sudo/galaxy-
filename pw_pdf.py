import asyncio
from playwright.async_api import async_playwright
import markdown

def md_to_html(md_file, html_file):
    with open(md_file, "r", encoding="utf-8") as f:
        md_text = f.read()
    
    html_body = markdown.markdown(md_text, extensions=['fenced_code', 'tables'])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; line-height: 1.6; padding: 2em; }}
            pre {{ background-color: #f4f4f4; padding: 1em; border-radius: 5px; white-space: pre-wrap; }}
            code {{ font-family: Consolas, monospace; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

async def html_to_pdf(html_file, pdf_file):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Convert path to file URL
        import os
        file_url = f"file:///{os.path.abspath(html_file).replace(chr(92), '/')}"
        await page.goto(file_url)
        await page.pdf(path=pdf_file, format="A4", print_background=True, margin={"top": "1cm", "bottom": "1cm", "left": "1cm", "right": "1cm"})
        await browser.close()

if __name__ == "__main__":
    md_file = "Comprehensive_Project_Report.md"
    html_file = "temp_report.html"
    pdf_file = "Comprehensive_Project_Report_Playwright.pdf"
    
    md_to_html(md_file, html_file)
    asyncio.run(html_to_pdf(html_file, pdf_file))
