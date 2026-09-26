import re

def main():
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix the bar chart overlapping text
    # Original: grid-template-columns: 180px 1fr 40px;
    # We'll use: grid-template-columns: 240px 1fr 40px; 
    # to give the label more room so it doesn't overlap the blue bar.
    content = re.sub(r'grid-template-columns:\s*180px\s+1fr\s+40px;', 'grid-template-columns: 250px 1fr 40px;', content)
    
    # Fix the blank blue section issue by replacing the buggy ::before elements with safer CSS
    
    buggy_css_pattern = r'#verification-section::before\s*\{[^}]*\}[\s\S]*?#explorer::before\s*\{[^}]*\}'
    
    safe_css = """
/* ── SAFER BACKGROUNDS ── */
#verification-section::before {
  content: '';
  position: absolute; top: -50px; left: 50%; width: 100vw; transform: translateX(-50%); bottom: -50px;
  background: radial-gradient(ellipse at center, rgba(56, 189, 248, 0.08) 0%, transparent 60%);
  z-index: -1;
  pointer-events: none;
}

#explorer {
  position: relative;
}
#explorer::before {
  content: '';
  position: absolute; top: 0; left: 50%; width: 100vw; transform: translateX(-50%); height: 100%;
  background: radial-gradient(ellipse at top, rgba(139, 92, 246, 0.05) 0%, transparent 80%);
  z-index: -1;
  pointer-events: none;
}
"""
    # Replace the old new_css block inside index.html
    content = re.sub(buggy_css_pattern, safe_css.strip(), content)

    # Let's also make sure the labels wrap properly just in case 250px is not enough
    # Add word-break or white-space to .bar-label
    content = re.sub(r'\.bar-label\s*\{([^\}]+)\}', r'.bar-label {\1 word-break: break-all; overflow-wrap: anywhere; }', content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("HTML layout fixed successfully.")

if __name__ == "__main__":
    main()
