import re

def main():
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Increase hero image visibility
    # Current: opacity: 0.15; mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
    content = re.sub(r'opacity:\s*0\.15;', 'opacity: 0.5;', content)
    content = re.sub(r'mask-image:\s*linear-gradient\(to bottom, black 0%, transparent 100%\);', 'mask-image: linear-gradient(to bottom, black 30%, transparent 100%);', content)
    content = re.sub(r'-webkit-mask-image:\s*linear-gradient\(to bottom, black 0%, transparent 100%\);', '-webkit-mask-image: linear-gradient(to bottom, black 30%, transparent 100%);', content)

    # 2. Add ID to Verification Section to target it easily
    # It currently is: <section class="sect reveal"> followed by <div class="sect-head"><h2>Human-in-the-loop Verification</h2>
    content = content.replace('<section class="sect reveal">\n    <div class="sect-head">\n      <h2>Human-in-the-loop Verification</h2>', '<section class="sect reveal" id="verification-section" style="position: relative;">\n    <div class="sect-head">\n      <h2>Human-in-the-loop Verification</h2>')

    # 3. Add more CSS for new images
    new_css = """
/* ── NEW BACKGROUND IMAGES ── */
.stats {
  position: relative;
  z-index: 1;
}
.stats::before {
  content: '';
  position: absolute; inset: 0; z-index: -1;
  background: url('https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1200&auto=format&fit=crop') center/cover no-repeat;
  opacity: 0.4;
  mix-blend-mode: screen;
}
.stat-card {
  background: rgba(15, 23, 42, 0.7); /* make transparent to show image */
}

#verification-section::before {
  content: '';
  position: absolute; top: -100px; left: -50vw; right: -50vw; bottom: -100px;
  background: url('https://images.unsplash.com/photo-1451187580459-43490279c0fa?q=80&w=2000&auto=format&fit=crop') center/cover no-repeat fixed;
  z-index: -2;
  opacity: 0.25;
  mask-image: radial-gradient(ellipse at center, black 0%, transparent 60%);
  -webkit-mask-image: radial-gradient(ellipse at center, black 0%, transparent 60%);
  pointer-events: none;
}

#explorer {
  position: relative;
}
#explorer::before {
  content: '';
  position: absolute; top: 0; left: -50vw; right: -50vw; height: 1000px;
  background: url('https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2000&auto=format&fit=crop') center top/cover no-repeat;
  z-index: -2;
  opacity: 0.15;
  mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, black 0%, transparent 100%);
  pointer-events: none;
}
"""
    # Insert new_css before </style>
    content = content.replace('</style>', new_css + '\n</style>')

    # 4. Remove the background color from .stat-card in the original CSS to avoid conflicts
    content = re.sub(r'\.stat-card\s*\{[^}]*background:\s*#0f172a;([^}]*)\}', r'.stat-card { \g<1> }', content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("HTML updated successfully with new images.")

if __name__ == "__main__":
    main()
