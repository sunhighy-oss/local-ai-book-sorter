#!/usr/bin/env python3
import re, json
from pathlib import Path
from collections import defaultdict

LOG_FILE = "clc_classify.log"
OUTPUT_HTML = "classification_chart.html"

def parse_log():
    stats = {"total": 0, "success": 0, "dist_1st": defaultdict(int), "dist_2nd": defaultdict(int), "dist_3rd": defaultdict(int)}
    if not Path(LOG_FILE).exists(): return stats
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if '发现' in line and '个文件待处理' in line:
                m = re.search(r'发现 (\d+) 个文件', line)
                if m: stats["total"] = int(m.group(1))
            if '→ 已移动到：' in line:
                stats["success"] += 1
                m = re.search(r'→ 已移动到：(.+?)/', line)
                if m: stats["dist_1st"][m.group(1)] += 1
                m2 = re.search(r'→ 已移动到：(.+?/.+?)/', line)
                if m2: stats["dist_2nd"][m2.group(1)] += 1
                m3 = re.search(r'→ 已移动到：(.+?/.+?/.+?)$', line)
                if m3: stats["dist_3rd"][m3.group(1)] += 1
    return stats

def generate_chart(stats):
    data = []
    for l1, c1 in stats["dist_1st"].items():
        children = []
        for l2, c2 in stats["dist_2nd"].items():
            if l2.startswith(l1):
                l3_children = [{"name": l3.split('/')[-1], "value": c3} for l3, c3 in stats["dist_3rd"].items() if l3.startswith(l2)]
                children.append({"name": l2.split('/')[-1], "value": c2, "children": l3_children if l3_children else None})
        data.append({"name": l1, "value": c1, "children": children if children else None})

    html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>图书分类统计</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script></head>
    <body><div id="chart" style="width:100%;height:800px;"></div>
    <script>var chart=echarts.init(document.getElementById('chart'));
    chart.setOption({{tooltip:{{trigger:'item'}}, series:{{type:'sunburst',data:{json.dumps(data, ensure_ascii=False)},radius:['0%','90%'],label:{{rotate:'radial'}}}}}});
    </script></body></html>"""
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f: f.write(html)
    print(f"✅ 图表已生成: {OUTPUT_HTML}")

if __name__ == "__main__":
    stats = parse_log()
    print(f"总文件: {stats['total']}, 成功分类: {stats['success']}")
    generate_chart(stats)
