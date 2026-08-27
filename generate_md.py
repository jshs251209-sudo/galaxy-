import os

def generate_report():
    base_dir = r"c:\Users\neato\Desktop\정현\03_과학탐구_대회\YSC_대회"
    output_md = os.path.join(base_dir, "Comprehensive_Project_Report.md")
    
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# 은하 진화 다차원 분석 및 통합 분류 체계 구축 - 종합 프로젝트 보고서\n\n")
        f.write("본 보고서는 해당 프로젝트의 모든 파일 정보, 소스 코드, 문서 내용 및 구조를 빠짐없이 포함하는 종합 보고서입니다.\n\n")
        
        # 1. Project Info (from docs and README)
        f.write("## 1. 프로젝트 핵심 문서\n\n")
        
        docs_to_include = ["README.md", "docs/research_report.md", "docs/data_dictionary.md"]
        for doc in docs_to_include:
            doc_path = os.path.normpath(os.path.join(base_dir, doc))
            if os.path.exists(doc_path):
                f.write(f"### {doc}\n\n")
                with open(doc_path, "r", encoding="utf-8") as df:
                    f.write(df.read() + "\n\n")
        
        # 2. Directory Structure
        f.write("## 2. 프로젝트 디렉토리 구조 및 전체 파일 목록\n\n")
        f.write("```text\n")
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root or ".git" in root or "node_modules" in root:
                continue
            level = root.replace(base_dir, '').count(os.sep)
            indent = ' ' * 4 * (level)
            f.write(f"{indent}{os.path.basename(root)}/\n")
            subindent = ' ' * 4 * (level + 1)
            for file in files:
                f.write(f"{subindent}{file}\n")
        f.write("```\n\n")
        
        # 3. File Details and Source Codes
        f.write("## 3. 파일별 상세 정보 및 소스 코드\n\n")
        
        text_extensions = [".py", ".md", ".txt", ".css", ".js", ".bat"]
        
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in root or ".git" in root or "node_modules" in root:
                continue
                
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
                
                # Skip already included core docs or the report itself
                if rel_path in [d.replace("\\", "/") for d in docs_to_include] or rel_path == "Comprehensive_Project_Report.md":
                    continue
                    
                f.write(f"### 파일: `{rel_path}`\n\n")
                f.write(f"- **경로**: `{file_path}`\n")
                f.write(f"- **크기**: {os.path.getsize(file_path)} bytes\n")
                
                ext = os.path.splitext(file)[1].lower()
                
                if ext in text_extensions or (ext == ".html" and "output" not in rel_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as tf:
                            content = tf.read()
                        f.write(f"- **유형**: 소스 코드 / 텍스트 문서\n\n")
                        f.write("**[내용]**:\n")
                        lang = ext[1:]
                        if lang == "txt": lang = "text"
                        if lang == "html": lang = "html"
                        f.write(f"```{lang}\n{content}\n```\n\n")
                    except UnicodeDecodeError:
                        f.write(f"- **유형**: 텍스트 인코딩 오류 (바이너리 또는 비-UTF8 파일로 추정)\n\n")
                elif ext in [".csv", ".xlsx", ".pkl"]:
                    f.write(f"- **유형**: 데이터 및 모델 파일\n")
                    f.write(f"- **설명**: 해당 파일은 머신러닝 모델, 엑셀 또는 CSV 데이터 파일이므로 전체 내용을 텍스트로 표출하지 않고 존재 여부와 크기 정보만 기록합니다.\n\n")
                elif ext in [".png", ".jpg", ".jpeg"]:
                    f.write(f"- **유형**: 이미지 파일\n")
                    f.write(f"- **설명**: 파이프라인에서 생성된 플롯 결과물 등 이미지 파일입니다.\n\n")
                elif ext == ".html" and "output" in rel_path:
                    f.write(f"- **유형**: 인터랙티브 웹 결과물\n")
                    f.write(f"- **설명**: 용량이 매우 큰 시각화 결과물이므로 텍스트 내용 전체를 수록하지 않고 기록만 남깁니다.\n\n")
                else:
                    f.write(f"- **유형**: 바이너리 또는 기타 파일\n")
                    f.write(f"- **설명**: 텍스트로 표현하기 어려운 파일입니다.\n\n")

if __name__ == "__main__":
    generate_report()
