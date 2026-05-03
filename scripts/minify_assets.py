#!/usr/bin/env python3
"""
Extract inline <style> from base.html for debugging only.

Do not use this to build static/css/site.min.css — that file is produced by
minifying static/css/site.css (see project docs or: python3 -c minify site.css).

This script writes static/css/extracted-inline-from-base.min.css only.
"""
import re
import os
import sys

# Project paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
BASE_HTML = os.path.join(BASE_DIR, 'core', 'templates', 'core', 'base.html')
CSS_DIR = os.path.join(BASE_DIR, 'static', 'css')
CSS_MIN_OUTPUT = os.path.join(CSS_DIR, 'extracted-inline-from-base.min.css')


def minify_css(css_text):
    """
    Minify CSS by removing comments, extra whitespace, and unnecessary characters.
    Safe for all standard CSS including media queries, keyframes, etc.
    """
    # Remove CSS comments /* ... */
    css_text = re.sub(r'/\*.*?\*/', '', css_text, flags=re.DOTALL)

    # Remove whitespace around structural characters
    css_text = re.sub(r'\s*\{\s*', '{', css_text)
    css_text = re.sub(r'\s*\}\s*', '}', css_text)
    css_text = re.sub(r'\s*;\s*', ';', css_text)
    css_text = re.sub(r'\s*:\s*', ':', css_text)
    css_text = re.sub(r'\s*,\s*', ',', css_text)
    css_text = re.sub(r'\s*>\s*', '>', css_text)
    css_text = re.sub(r'\s*~\s*', '~', css_text)
    css_text = re.sub(r'\s*\+\s*', '+', css_text)

    # Collapse remaining whitespace to single spaces
    css_text = re.sub(r'\s+', ' ', css_text)

    # Remove trailing semicolons before closing braces
    css_text = css_text.replace(';}', '}')

    # Remove leading/trailing whitespace
    css_text = css_text.strip()

    return css_text


def extract_inline_css(html_path):
    """Extract all inline <style> block contents from an HTML file."""
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all <style>...</style> blocks
    blocks = re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL)

    if not blocks:
        print("Warning: No <style> blocks found in base.html")
        return ''

    print(f"Found {len(blocks)} inline <style> blocks")
    return '\n\n'.join(blocks)


def minify_file(input_path, output_path):
    """Minify a standalone CSS file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        original = f.read()

    minified = minify_css(original)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(minified)

    orig_size = len(original.encode('utf-8'))
    min_size = len(minified.encode('utf-8'))
    reduction = (1 - min_size / orig_size) * 100 if orig_size > 0 else 0
    print(f"  {os.path.basename(input_path)}: {orig_size:,} → {min_size:,} bytes ({reduction:.1f}% reduction)")
    return minified


def main():
    print("=" * 60)
    print("CalculatorDrive Asset Minification")
    print("=" * 60)

    # Ensure output directories exist
    os.makedirs(CSS_DIR, exist_ok=True)

    print(f"\n📄 Extracting inline CSS from base.html...")
    combined_css = extract_inline_css(BASE_HTML)

    if not combined_css:
        print("No CSS to extract. Exiting.")
        sys.exit(1)

    orig_size = len(combined_css.encode('utf-8'))
    print(f"  Combined inline CSS: {orig_size:,} bytes")

    print(f"\n🔧 Minifying...")
    minified_css = minify_css(combined_css)

    with open(CSS_MIN_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(minified_css)

    min_size = len(minified_css.encode('utf-8'))
    reduction = (1 - min_size / orig_size) * 100 if orig_size > 0 else 0
    print(f"  → {os.path.basename(CSS_MIN_OUTPUT)}: {min_size:,} bytes ({reduction:.1f}% smaller)")

    # Step 3: Report on vendor files
    print(f"\n📊 Vendor file sizes:")
    vendor_css_dir = os.path.join(BASE_DIR, 'static', 'vendor', 'css')
    vendor_js_dir = os.path.join(BASE_DIR, 'static', 'vendor', 'js')

    for d in [vendor_css_dir, vendor_js_dir]:
        if os.path.exists(d):
            for f in sorted(os.listdir(d)):
                fpath = os.path.join(d, f)
                if os.path.isfile(fpath):
                    size = os.path.getsize(fpath)
                    print(f"  {f}: {size:,} bytes")

    # Step 4: Check for unnecessary files
    source_map = os.path.join(vendor_js_dir, 'chart.umd.js.map')
    if os.path.exists(source_map):
        size = os.path.getsize(source_map)
        print(f"\n⚠️  Found source map: chart.umd.js.map ({size:,} bytes)")
        print(f"   This file is not needed in production and can be deleted.")

    print(f"\n✅ Wrote {CSS_MIN_OUTPUT}")
    print("   To refresh site.min.css, minify static/css/site.css separately.\n")


if __name__ == '__main__':
    main()
