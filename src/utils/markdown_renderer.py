"""Markdown渲染工具"""
import markdown


def markdown_to_html(md_text: str) -> str:
    """
    将Markdown转换为HTML，支持LaTeX数学公式

    Args:
        md_text: Markdown文本

    Returns:
        渲染后的HTML
    """
    # 转换Markdown为HTML
    html_content = markdown.markdown(
        md_text,
        extensions=[
            'extra',  # 支持表格、代码块等扩展语法
            'codehilite',  # 代码高亮
            'fenced_code',  # 围栏代码块
        ]
    )

    # 构建完整的HTML页面，包含MathJax支持
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                padding: 20px;
                color: #333;
                background-color: #f5f5f5;
            }}

            h1, h2, h3, h4, h5, h6 {{
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }}

            h1 {{ font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h2 {{ font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: 0.3em; }}
            h3 {{ font-size: 1.25em; }}

            p {{
                margin-bottom: 16px;
            }}

            code {{
                background-color: rgba(27, 31, 35, 0.05);
                border-radius: 3px;
                padding: 0.2em 0.4em;
                font-family: 'Courier New', monospace;
            }}

            pre {{
                background-color: #f6f8fa;
                border-radius: 3px;
                padding: 16px;
                overflow: auto;
                line-height: 1.45;
            }}

            pre code {{
                background-color: transparent;
                padding: 0;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }}

            table th, table td {{
                border: 1px solid #dfe2e5;
                padding: 6px 13px;
            }}

            table th {{
                background-color: #f6f8fa;
                font-weight: 600;
            }}

            blockquote {{
                border-left: 4px solid #dfe2e5;
                padding-left: 16px;
                color: #6a737d;
                margin: 0 0 16px 0;
            }}

            img {{
                max-width: 100%;
            }}

            /* LaTeX 公式样式 */
            .MathJax {{
                font-size: 1.1em;
            }}
        </style>

        <!-- MathJax for LaTeX support -->
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$']],
                    displayMath: [['$$', '$$']],
                    processEscapes: true,
                    processEnvironments: true
                }},
                options: {{
                    skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre']
                }}
            }};
        </script>
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js" async></script>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    return full_html
