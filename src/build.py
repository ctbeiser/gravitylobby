#!/usr/bin/env python3

"""
Blog builder - converts markdown files to HTML
Requirements: markdown

The script will create its own virtual environment in .venv/
"""

import os
import sys
import venv
import subprocess
from pathlib import Path

def ensure_venv():
    """Create and return path to venv if it doesn't exist"""
    venv_path = Path(__file__).parent.parent / ".venv"
    
    if not venv_path.exists():
        print("Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
        
        # Get the pip path
        pip_path = venv_path / "bin" / "pip" if os.name != "nt" else venv_path / "Scripts" / "pip.exe"
        
        # Install markdown
        print("Installing requirements...")
        subprocess.check_call([str(pip_path), "install", "markdown"])
    
    # Return path to Python interpreter in venv
    python_path = venv_path / "bin" / "python" if os.name != "nt" else venv_path / "Scripts" / "python.exe"
    return python_path

if __name__ == "__main__":
    # Check if we're in the venv
    if not hasattr(sys, "real_prefix") and not sys.base_prefix != sys.prefix:
        # We're not in a venv, so create/activate one and re-run this script
        python_path = ensure_venv()
        os.execl(str(python_path), str(python_path), *sys.argv)
    
    # Everything below this only runs in the venv
    import re
    import markdown

    class BlogConverter:
        def __init__(self):
            self.html_template = '''
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link href="reset.css" rel="stylesheet" type="text/css">
    <link href="//cloud.webtype.com/css/16fc21a3-84ad-48a4-b2ab-80991b0393a0.css" rel="stylesheet" type="text/css" />
</head>
<body>
<div id=container>
<h6><a href="/">{date}</a></h6>
{content}
</div>
</body>
</html>
'''

        def parse_header(self, content: str) -> tuple[str, str, str]:
            """Extract date, title, and content from markdown text."""
            lines = content.split('\n')
            date = None
            title = None
            content_start = 0
            
            if lines[0].startswith('######'):
                date = lines[0].replace('######', '').strip()
                content_start = 1
                
            if len(lines) > content_start and lines[content_start].startswith('# '):
                title = lines[content_start].replace('# ', '').strip()
                content_start += 1
                
            return date, title, '\n'.join(lines[content_start:])

        def convert_file(self, input_path: Path) -> str:
            """Convert a markdown file to HTML."""
            content = input_path.read_text(encoding='utf-8')
            date, title, main_content = self.parse_header(content)
            
            # Add the title as H1 if it exists
            if title:
                main_content = f"# {title}\n\n{main_content}"
            
            # Normalize footnotes
            footnote_counter = 1
            footnotes = []
            result = []
            stack = []
            
            for char in main_content:
                if char == '[':
                    stack.append(len(result))
                    result.append(char)  # Keep the opening bracket
                elif char == ']' and stack:
                    start = stack.pop()
                    text = ''.join(result[start + 1:])  # +1 to skip the opening bracket
                    
                    # Check if this is a footnote
                    if text.startswith('^'):
                        footnote_text = text[1:]  # Remove the ^
                        # Convert footnote content to HTML first
                        md = markdown.Markdown(extensions=['extra'])
                        footnote_html = md.convert(footnote_text)
                        # Strip surrounding <p> tags if present
                        footnote_html = footnote_html.strip()
                        if footnote_html.startswith('<p>') and footnote_html.endswith('</p>'):
                            footnote_html = footnote_html[3:-4]
                        footnotes.append(f"[^{footnote_counter}]: {footnote_html}")
                        result[start:] = f"[^{footnote_counter}]"
                        footnote_counter += 1
                    else:
                        # Not a footnote, keep everything as is
                        result.append(char)
                else:
                    result.append(char)
            
            main_content = ''.join(result)
            if footnotes:
                main_content += "\n\n" + "\n".join(footnotes)
            
            # Convert to HTML
            md = markdown.Markdown(extensions=['extra', 'footnotes'])
            html_content = md.convert(main_content)
            
            return self.html_template.format(
                title=title or input_path.stem,
                date=date or '',
                content=html_content
            ).strip()

    # Main execution
    converter = BlogConverter()
    project_root = Path(__file__).parent.parent
    markdown_dir = project_root / "markdown"
    output_dir = project_root
    
    for md_file in markdown_dir.glob("*.md"):
        html_content = converter.convert_file(md_file)
        output_path = output_dir / f"{md_file.stem}.html"
        output_path.write_text(html_content, encoding='utf-8')
        print(f"Created {output_path}")