import re

def main():
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove 'reveal' class from #explorer so it is always visible
    content = content.replace('<section class="sect reveal" id="explorer">', '<section class="sect" id="explorer">')

    # 2. Fix IntersectionObserver threshold to 0 to prevent similar issues on smaller screens
    content = content.replace('{ threshold: 0.08 }', '{ threshold: 0 }')

    # Just in case it was written without ID earlier (before my previous edit)
    content = content.replace('<!-- ─── EXPLORER ─── -->\n  <section class="sect reveal">', '<!-- ─── EXPLORER ─── -->\n  <section class="sect" id="explorer">')

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("Explorer visibility fixed.")

if __name__ == "__main__":
    main()
