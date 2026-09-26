import re

def main():
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove the BOUNDARY section
    boundary_pattern = r'<!-- ─── BOUNDARY ─── -->.*?</section>'
    content = re.sub(boundary_pattern, '', content, flags=re.DOTALL)

    # Update Footer text
    footer_pattern = r'<footer>.*?</footer>'
    new_footer = """<footer>
  <p>This workspace snapshot contains 100 first-pass records, a mixed-provenance 20-app coverage audit, and finalized human-verified evidence. All manual QA limitations are documented within the corresponding sections.</p>
  <p class="mono">Analysis v2.1 · 100 records</p>
</footer>"""
    content = re.sub(footer_pattern, new_footer, content, flags=re.DOTALL)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("HTML updated successfully.")

if __name__ == "__main__":
    main()
