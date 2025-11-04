#!/usr/bin/env python3
"""
测试QuickLaTeX API
"""
import asyncio

import httpx


async def test_quicklatex():
    client = httpx.AsyncClient(timeout=30.0)

    # 准备测试的LaTeX代码
    latex_code = "\\documentclass{standalone}\\begin{document}\\large $V = \\frac{4}{3}\\pi r^3$\\end{document}"

    payload = {
        "formula": latex_code,
        "fsize": "17px",
        "fcolor": "000000",
        "mode": "0",  # 0=SVG
        "out": "1",
        "remhost": "quicklatex.com",
    }

    print(f"LaTeX代码: {latex_code}")
    print("正在调用QuickLaTeX API...")

    try:
        response = await client.post(
            "https://quicklatex.com/latex3.f",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")

        if response.status_code == 200:
            lines = response.text.strip().split("\n")
            if len(lines) >= 2:
                status = lines[0].strip()
                print(f"QuickLaTeX状态: {status}")
                if status == "0":
                    svg_url = lines[1].strip()
                    print(f"SVG URL: {svg_url}")

                    # 下载SVG
                    svg_response = await client.get(svg_url)
                    print(f"SVG下载状态: {svg_response.status_code}")
                    if svg_response.status_code == 200:
                        print(f"SVG长度: {len(svg_response.text)}")
                        print(f"SVG前100字符: {svg_response.text[:100]}")

                        # 保存SVG文件供查看
                        with open("/tmp/test_formula.svg", "w") as f:
                            f.write(svg_response.text)
                        print("SVG已保存到 /tmp/test_formula.svg")

    except Exception as e:
        print(f"错误: {e}")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(test_quicklatex())
