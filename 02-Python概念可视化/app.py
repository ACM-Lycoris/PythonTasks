#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 核心概念可视化教学平台 — Flask 单文件全栈应用
涵盖: 动态类型 | 列表内存(含二维列表) | 函数参数传递 | 深拷贝/浅拷贝 |
      字符串拼接性能
启动: python app.py  →  http://127.0.0.1:5000
"""

import time, copy
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# ============================================================================
# 后端演示路由 — 为每个知识点提供可交互的代码执行
# ============================================================================

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

# --- 动态类型演示 ---
@app.route("/api/demo/dynamic_type")
def demo_dynamic_type():
    steps = []
    x = 42
    steps.append({"code": "x = 42", "type": type(x).__name__, "value": repr(x),
                  "id": id(x), "desc": "x 是整数(int), 占用28字节"})
    x = 3.14
    steps.append({"code": "x = 3.14", "type": type(x).__name__, "value": repr(x),
                  "id": id(x), "desc": "同一个变量名 x, 现在变成了浮点数(float)"})
    x = "Hello Python"
    steps.append({"code": "x = \"Hello Python\"", "type": type(x).__name__, "value": repr(x),
                  "id": id(x), "desc": "x 又变成了字符串(str), 动态类型允许随时改变"})
    x = [1, 2, 3]
    steps.append({"code": "x = [1, 2, 3]", "type": type(x).__name__, "value": repr(x),
                  "id": id(x), "desc": "x 又变成了列表(list), 这在C++/Java中是不可能的!"})
    x = {"key": "value"}
    steps.append({"code": "x = {\"key\": \"value\"}", "type": type(x).__name__, "value": repr(x),
                  "id": id(x), "desc": "x 又变成了字典(dict), 变量只是名字标签!"})
    return jsonify(steps=steps)

# --- 列表内存模型演示 ---
@app.route("/api/demo/list_memory")
def demo_list_memory():
    a = [10, 20, 30]
    b = a
    c = a.copy()
    result = {
        "a_id": id(a), "b_id": id(b), "c_id": id(c),
        "a_val": repr(a), "b_val": repr(b), "c_val": repr(c),
        "a_is_b": a is b, "a_is_c": a is c,
        "a_eq_c": a == c,
    }
    b.append(999)
    result["after_b_append"] = {"a_val": repr(a), "b_val": repr(b), "c_val": repr(c)}
    return jsonify(result)

# --- 二维列表内存模型演示 ---
@app.route("/api/demo/2d_list")
def demo_2d_list():
    matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    row0 = matrix[0]
    shallow = matrix.copy()
    deep = copy.deepcopy(matrix)
    result = {
        "matrix_val": repr(matrix),
        "matrix_id": id(matrix),
        "row0_id": id(row0),
        "matrix_0_id": id(matrix[0]),
        "shallow_id": id(shallow),
        "deep_id": id(deep),
        "inner_ids_matrix": [id(row) for row in matrix],
        "inner_ids_shallow": [id(row) for row in shallow],
        "inner_ids_deep": [id(row) for row in deep],
        "row0_is_matrix0": row0 is matrix[0],
    }
    row0[0] = 999
    result["after_modify"] = {
        "desc": "修改 row0[0]=999 后 — row0就是matrix[0]!",
        "matrix": repr(matrix),
        "shallow": repr(shallow),
        "deep": repr(deep),
    }
    shallow[1][1] = 888
    result["after_shallow_modify"] = {
        "desc": "修改 shallow[1][1]=888 后 — 浅拷贝内层列表共享!",
        "matrix": repr(matrix),
    }
    return jsonify(result)


# --- 函数参数传递演示 ---
@app.route("/api/demo/function_params")
def demo_function_params():
    results = []
    def modify_int(n):
        n += 100
        return n
    x = 10
    ret = modify_int(x)
    results.append({"title": "不可变对象 int — 类似C++传值",
                    "before": "x = 10",
                    "after_func": f"modify_int(x) 返回 {ret}",
                    "after": f"x 仍然是 {x}",
                    "changed": x == 10})
    def modify_list(lst):
        lst.append(999)
        return lst
    my_list = [1, 2, 3]
    ret_list = modify_list(my_list)
    results.append({"title": "可变对象 list — 类似C++传指针/引用",
                    "before": "my_list = [1, 2, 3]",
                    "after_func": f"modify_list(my_list) 返回 {ret_list}",
                    "after": f"my_list 变成了 {my_list}",
                    "changed_id": id(my_list) == id(ret_list)})
    def reassign(lst):
        lst = [4, 5, 6]
        return lst
    my_list2 = [1, 2, 3]
    ret2 = reassign(my_list2)
    results.append({"title": "赋值(=) vs 修改(.append)",
                    "before": "my_list2 = [1, 2, 3]",
                    "after_func": f"函数内 lst=[4,5,6] 返回 {ret2}",
                    "after": f"但 my_list2 仍是 {my_list2} (赋值只改变局部变量!)",
                    "changed": my_list2 == [1, 2, 3]})
    return jsonify(results=results)

# --- 深拷贝 vs 浅拷贝演示 ---
@app.route("/api/demo/copy_demo")
def demo_copy_demo():
    import copy as cp_mod
    original = [1, 2, [10, 20, 30], 3]
    shallow = original.copy()
    deep = cp_mod.deepcopy(original)
    result = {
        "original": repr(original), "shallow": repr(shallow), "deep": repr(deep),
        "original_id": id(original), "shallow_id": id(shallow), "deep_id": id(deep),
        "original_nested_id": id(original[2]), "shallow_nested_id": id(shallow[2]),
        "deep_nested_id": id(deep[2]),
    }
    shallow[2].append(999)
    result["after_shallow_modify"] = {
        "desc": "修改 shallow[2] 后 — 浅拷贝共享嵌套对象!",
        "original": repr(original), "shallow": repr(shallow), "deep": repr(deep),
    }
    return jsonify(result)

# --- 字符串拼接性能分析 ---
@app.route("/api/demo/string_perf")
def demo_string_perf():
    import time
    sizes = [100, 500, 1000, 5000, 10000, 50000, 100000]
    plus_times, join_times = [], []
    for n in sizes:
        start = time.perf_counter()
        s = ""
        for i in range(n):
            s += str(i)
        plus_times.append(round((time.perf_counter() - start) * 1000, 3))
        start = time.perf_counter()
        s = "".join(str(i) for i in range(n))
        join_times.append(round((time.perf_counter() - start) * 1000, 3))
    return jsonify(sizes=sizes, plus_times=plus_times, join_times=join_times,
                   plus_unit="ms", join_unit="ms",
                   note="字符串是不可变对象, 每次+都创建新字符串(O(n²)); join一次分配(O(n))")


# ============================================================================
# 前端 HTML/CSS/JS
# ============================================================================
INDEX_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Python 核心概念可视化教学</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
:root {
  --bg: #0a0e17; --card: #111827; --card2: #161e2c;
  --text: #e2e8f0; --text2: #94a3b8;
  --cyan: #00e5ff; --pink: #ff4081; --green: #00e676;
  --amber: #ffab00; --red: #ff1744; --purple: #b388ff;
  --border: #1e2d45; --radius: 10px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: "Inter","Segoe UI","Microsoft YaHei",sans-serif;
  background: var(--bg); color: var(--text); min-height: 100vh; overflow-x: hidden;
}
body::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image:
    linear-gradient(rgba(0,229,255,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,229,255,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  animation: gridPulse 8s ease-in-out infinite;
}
@keyframes gridPulse { 0%,100% { opacity: 0.5; } 50% { opacity: 1; } }
.app { position: relative; z-index: 1; max-width: 1300px; margin: 0 auto; padding: 16px; }

/* ---- 顶部导航 ---- */
header {
  display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
  margin-bottom: 16px; padding: 14px 20px;
  background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; box-shadow: 0 0 20px rgba(0,229,255,0.12);
}
header h1 {
  font-size: 20px; font-weight: 700; margin-right: auto;
  background: linear-gradient(135deg, var(--cyan), #80deea);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; letter-spacing: 1px;
}
.nav-tag {
  padding: 5px 11px; border-radius: 20px; font-size: 11px; font-weight: 600;
  border: 1px solid var(--border); color: var(--text2);
  cursor: pointer; transition: all 0.2s; white-space: nowrap; background: var(--card2);
}
.nav-tag:hover, .nav-tag.active {
  border-color: var(--cyan); color: var(--cyan);
  box-shadow: 0 0 12px rgba(0,229,255,0.15);
}

/* ---- 主内容 ---- */
.section {
  display: none; background: var(--card); border: 1px solid var(--border);
  border-radius: 12px; padding: 28px 32px; margin-bottom: 16px;
  box-shadow: 0 0 16px rgba(0,229,255,0.05);
  animation: fadeIn 0.3s ease;
}
.section.active { display: block; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
.section h2 {
  font-size: 20px; margin-bottom: 6px;
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.section .subtitle { color: var(--text2); font-size: 13px; margin-bottom: 20px; }

/* ---- 卡片 ---- */
.card {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px; margin-bottom: 16px;
}
.card h3 {
  font-size: 14px; color: var(--cyan); margin-bottom: 10px;
  border-bottom: 1px solid var(--border); padding-bottom: 8px;
}

/* ---- 步骤导航 ---- */
.step-nav {
  display: flex; align-items: center; gap: 12px;
  padding: 14px 20px; margin: 16px 0;
  background: var(--card2); border: 1px solid var(--border); border-radius: var(--radius);
}
.step-nav-btn {
  padding: 7px 16px; border-radius: 6px; cursor: pointer;
  font-size: 12px; font-weight: 600; border: 1px solid var(--border);
  background: var(--card); color: var(--text); transition: all 0.2s;
  white-space: nowrap;
}
.step-nav-btn:hover:not(:disabled) {
  border-color: var(--cyan); color: var(--cyan); box-shadow: 0 0 10px rgba(0,229,255,0.1);
}
.step-nav-btn:disabled { opacity: 0.3; cursor: default; }
.step-dots { display: flex; gap: 8px; align-items: center; }
.step-dot {
  width: 12px; height: 12px; border-radius: 50%; cursor: pointer;
  background: var(--border); transition: all 0.3s; border: none;
}
.step-dot.active { background: var(--cyan); box-shadow: 0 0 10px var(--cyan); transform: scale(1.3); }
.step-dot.done { background: var(--green); }
.step-label { color: var(--text2); font-size: 12px; margin-left: auto; white-space: nowrap; }

/* ---- 步骤内容: SVG + 代码并排 ---- */
.step-content {
  display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;
}
@media (max-width: 950px) { .step-content { grid-template-columns: 1fr; } }
.step-svg {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
  display: flex; align-items: center; justify-content: center; overflow-x: auto;
  min-height: 280px;
}
.step-svg svg { max-width: 100%; height: auto; }

/* ---- 代码面板 (带行号和当前行高亮) ---- */
.code-panel {
  background: #0d1117; border: 1px solid var(--border); border-radius: var(--radius);
  overflow: hidden; display: flex; flex-direction: column;
}
.code-panel-header {
  padding: 8px 16px; background: var(--card2); border-bottom: 1px solid var(--border);
  font-size: 11px; color: var(--text2); font-weight: 600;
}
.code-panel-body {
  padding: 12px 0; overflow-x: auto; flex: 1;
  font-family: "Cascadia Code","Fira Code","Consolas",monospace;
  font-size: 13px; line-height: 1.75;
}
.code-line {
  display: flex; padding: 0 16px; transition: background 0.3s;
}
.code-line.hl {
  background: rgba(0,229,255,0.08); border-left: 3px solid var(--cyan);
  padding-left: 13px;
}
.code-line .ln {
  width: 32px; flex-shrink: 0; text-align: right; margin-right: 16px;
  color: #484f58; user-select: none;
}
.code-line .ct { color: #c9d1d9; white-space: pre; }
.code-line .kw { color: #ff7b72; }
.code-line .fn { color: #d2a8ff; }
.code-line .str { color: #a5d6ff; }
.code-line .num { color: #79c0ff; }
.code-line .cmt { color: #8b949e; font-style: italic; }
.code-line .cyan { color: #00e5ff; }

/* ---- 完整代码折叠区 ---- */
.full-code-wrap { margin-bottom: 16px; }
.full-code-wrap summary {
  cursor: pointer; padding: 10px 20px; background: var(--card2);
  border: 1px solid var(--border); border-radius: var(--radius);
  font-size: 13px; color: var(--purple); font-weight: 600;
  transition: all 0.2s;
}
.full-code-wrap summary:hover { border-color: var(--purple); }
.full-code-wrap .code-block {
  margin-top: 8px; background: #0d1117; border: 1px solid var(--border);
  border-radius: 6px; padding: 16px; font-family: "Cascadia Code","Fira Code","Consolas",monospace;
  font-size: 13px; line-height: 1.7; overflow-x: auto; color: #c9d1d9;
  white-space: pre; word-break: normal;
}

/* ---- 按钮 ---- */
.btn {
  padding: 8px 18px; border: 1px solid transparent; border-radius: 6px;
  cursor: pointer; font-size: 13px; font-weight: 600; letter-spacing: 0.3px;
  transition: all 0.2s; white-space: nowrap;
}
.btn:hover { transform: translateY(-1px); }
.btn-run {
  background: var(--cyan); color: #000; border-color: var(--cyan);
  box-shadow: 0 0 12px rgba(0,229,255,0.2);
}
.btn-demo { background: transparent; color: var(--green); border: 1px solid var(--green); }

/* ---- 输出区域 ---- */
.output-box {
  background: #0d1117; border: 1px solid var(--border); border-radius: 6px;
  padding: 14px 16px; font-family: "Cascadia Code","Fira Code",monospace;
  font-size: 13px; color: var(--green); min-height: 40px;
  white-space: pre-wrap; word-break: break-all; line-height: 1.7;
}

/* ---- 表格 ---- */
.info-table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
.info-table th {
  background: var(--card); color: var(--cyan); padding: 8px 14px;
  text-align: left; border-bottom: 2px solid var(--border); font-weight: 600;
}
.info-table td {
  padding: 8px 14px; border-bottom: 1px solid var(--border);
  font-family: "Cascadia Code","Fira Code",monospace; font-size: 12px;
}

/* ---- Chart.js ---- */
.chart-wrap {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px; margin: 10px 0;
  position: relative; height: 380px;
}
.chart-wrap canvas { max-height: 350px; }

/* ---- 标签 ---- */
.tag {
  display: inline-block; padding: 3px 8px; border-radius: 12px;
  font-size: 10px; font-weight: 700; letter-spacing: 0.5px;
}
.tag-immutable { background: rgba(255,64,129,0.15); color: var(--pink); }
.tag-mutable { background: rgba(0,230,118,0.15); color: var(--green); }

/* ---- 演示面板 ---- */
.demo-panel {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px; margin-top: 12px;
}
.demo-panel h3 {
  font-size: 14px; color: var(--cyan); margin-bottom: 14px;
  padding-bottom: 8px; border-bottom: 1px solid var(--border);
}
.demo-step {
  display: flex; gap: 12px; align-items: flex-start;
  padding: 10px 14px; margin: 6px 0;
  background: #0d1117; border-radius: 6px; border: 1px solid transparent;
  transition: border-color 0.2s;
}
.demo-step:hover { border-color: var(--border); }
.demo-step-num {
  flex-shrink: 0; width: 26px; height: 26px; border-radius: 50%;
  background: var(--cyan); color: #000; display: flex; align-items: center;
  justify-content: center; font-size: 11px; font-weight: 700;
}
.demo-step-body { flex: 1; font-size: 13px; line-height: 1.7; }
.demo-step-body .step-code {
  color: #c9d1d9; font-family: "Cascadia Code","Fira Code",monospace;
  font-size: 12px; background: #161e2c; padding: 2px 8px; border-radius: 4px;
  display: inline-block; margin: 2px 0;
}
.demo-step-body .step-result { color: var(--green); }
.demo-step-body .step-warn { color: var(--amber); }
.demo-step-body .step-error { color: var(--red); }

/* Grid (仅函数参数使用) */
.grid3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
@media (max-width: 900px) { .grid3 { grid-template-columns: 1fr; } }

/* ---- C++对比面板 ---- */
.compare-panel {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 16px 0;
}
@media (max-width: 900px) { .compare-panel { grid-template-columns: 1fr; } }
.compare-col {
  border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border);
}
.compare-col-header {
  padding: 8px 16px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
  font-family: "Orbitron","Inter",sans-serif;
}
.compare-col-header.py { background: rgba(0,240,255,0.12); color: var(--cyan); border-bottom: 1px solid rgba(0,240,255,0.15); }
.compare-col-header.cpp { background: rgba(255,171,0,0.12); color: var(--amber); border-bottom: 1px solid rgba(255,171,0,0.15); }
.compare-col-body {
  padding: 12px 16px; font-family: "Cascadia Code","Fira Code","Consolas",monospace;
  font-size: 12px; line-height: 1.75; background: rgba(6,10,20,0.65);
  color: #c9d1d9; white-space: pre; overflow-x: auto;
}
.compare-col-body .kw { color: #ff7b72; }
.compare-col-body .cmt { color: #8b949e; font-style: italic; }
.compare-col-body .str { color: #a5d6ff; }
.compare-col-body .num { color: #79c0ff; }
.compare-verdict {
  margin-top: 8px; padding: 10px 16px;
  background: rgba(179,102,255,0.06); border-left: 3px solid var(--purple);
  border-radius: 6px; font-size: 13px; line-height: 1.7;
}
.compare-verdict strong { color: var(--purple); }

/* ================================================================
   SCI-FI ENHANCEMENTS — overrides & new effects
   ================================================================ */

/* ---- Override root variables for deeper space palette ---- */
:root {
  --bg: #020510;
  --card: rgba(10, 16, 36, 0.72);
  --card2: rgba(16, 24, 48, 0.65);
  --text: #e0e8ff;
  --text2: #7a8fbf;
  --cyan: #00f0ff;
  --pink: #ff2d78;
  --green: #00ff88;
  --amber: #ffb800;
  --red: #ff4060;
  --purple: #b366ff;
  --border: rgba(0, 240, 255, 0.1);
}

/* ---- Replace grid background with vignette ---- */
body::before {
  content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 50%, rgba(2,5,16,0.75) 100%);
  animation: none;
}

/* ---- Scanline overlay (HUD feel) ---- */
body::after {
  content: ""; position: fixed; inset: 0; z-index: 9998; pointer-events: none;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.045) 2px,
    rgba(0,0,0,0.045) 4px
  );
  animation: scanlines 10s linear infinite;
}
@keyframes scanlines { 0% { transform: translateY(0); } 100% { transform: translateY(100px); } }

/* ---- Starfield canvas ---- */
#starfield {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
}

/* ---- Cursor glow orb ---- */
.cursor-glow {
  position: fixed; width: 220px; height: 220px; border-radius: 50%;
  pointer-events: none; z-index: 10000;
  background: radial-gradient(circle, rgba(0,240,255,0.055) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  transition: opacity 0.5s;
}

/* ---- Header — glass + neon top-edge ---- */
header {
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-color: rgba(0,240,255,0.16);
  box-shadow: 0 0 30px rgba(0,240,255,0.07), 0 0 60px rgba(0,240,255,0.02);
  overflow: hidden;
}
header::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0,240,255,0.55), transparent);
  animation: headerShine 3s ease-in-out infinite;
}
@keyframes headerShine { 0%,100% { opacity: 0.25; } 50% { opacity: 1; } }

header h1 {
  font-family: "Orbitron","Inter","Microsoft YaHei",sans-serif;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #00f0ff 0%, #80f0ff 40%, #b366ff 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 8px rgba(0,240,255,0.4));
}

/* ---- Navigation — neon sci-fi tabs ---- */
.nav-tag {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 0.5px;
  border-color: rgba(255,255,255,0.06);
  background: rgba(255,255,255,0.015);
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  position: relative; overflow: hidden;
}
.nav-tag::before {
  content: ""; position: absolute; inset: 0; border-radius: 20px;
  background: linear-gradient(135deg, rgba(0,240,255,0.12), rgba(179,102,255,0.08));
  opacity: 0; transition: opacity 0.3s;
}
.nav-tag:hover, .nav-tag.active {
  border-color: #00f0ff; color: #00f0ff;
  box-shadow: 0 0 20px rgba(0,240,255,0.2), 0 0 40px rgba(0,240,255,0.05);
  text-shadow: 0 0 8px rgba(0,240,255,0.5);
  transform: translateY(-1px);
}
.nav-tag:hover::before, .nav-tag.active::before { opacity: 1; }
.nav-tag.active {
  background: rgba(0,240,255,0.07);
  box-shadow: 0 0 25px rgba(0,240,255,0.3), inset 0 0 20px rgba(0,240,255,0.05);
}

/* ---- Sections — frosted glass panels ---- */
.section {
  background: rgba(10, 16, 36, 0.68);
  border-color: rgba(0,240,255,0.07);
  border-radius: 16px;
  padding: 32px 36px;
  box-shadow: 0 0 50px rgba(0,240,255,0.025), 0 8px 32px rgba(0,0,0,0.5);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  animation: fadeSlideIn 0.45s cubic-bezier(0.16,1,0.3,1);
}
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(18px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.section h2 {
  font-family: "Orbitron","Inter","Microsoft YaHei",sans-serif;
  letter-spacing: 1px; font-size: 21px;
  background: linear-gradient(135deg, #00f0ff 0%, #80f0ff 50%, #b366ff 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 6px rgba(0,240,255,0.35));
}

/* ---- Cards — frosted with hover lift ---- */
.card {
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-color: rgba(255,255,255,0.04);
  transition: all 0.35s cubic-bezier(0.4,0,0.2,1);
}
.card:hover {
  border-color: rgba(0,240,255,0.13);
  box-shadow: 0 0 35px rgba(0,240,255,0.06), 0 4px 24px rgba(0,0,0,0.35);
  transform: translateY(-2px);
}
.card h3 {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 0.5px;
  border-bottom-color: rgba(255,255,255,0.05);
}

/* ---- Step navigation ---- */
.step-nav {
  background: rgba(16,24,48,0.45);
  border-color: rgba(255,255,255,0.04);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-radius: 12px;
}
.step-nav-btn {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 0.5px;
  border-radius: 8px;
  background: rgba(0,0,0,0.3);
  border-color: rgba(255,255,255,0.06);
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
}
.step-nav-btn:hover:not(:disabled) {
  border-color: #00f0ff; color: #00f0ff;
  box-shadow: 0 0 20px rgba(0,240,255,0.2);
  transform: translateY(-1px);
}
.step-dot.active {
  background: #00f0ff;
  box-shadow: 0 0 12px #00f0ff, 0 0 24px rgba(0,240,255,0.5);
}
.step-dot.done {
  background: rgba(0,255,136,0.5);
  box-shadow: 0 0 8px rgba(0,255,136,0.3);
}

/* ---- Step SVG panel ---- */
.step-svg {
  background: rgba(8,14,30,0.45);
  border-color: rgba(255,255,255,0.04);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

/* ---- Code panel ---- */
.code-panel {
  background: rgba(6,10,20,0.82);
  border-color: rgba(255,255,255,0.05);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.code-panel-header {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 1px; font-size: 10px;
}
.code-line.hl {
  background: rgba(0,240,255,0.05);
  box-shadow: inset 0 0 30px rgba(0,240,255,0.03);
}
.code-line .ln { color: #3a4560; }
.code-line .cyan { color: #00f0ff; }

/* ---- Full code wrap ---- */
.full-code-wrap summary {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 0.5px;
  background: rgba(16,24,48,0.35);
  border-color: rgba(255,255,255,0.05);
  border-radius: 10px;
}
.full-code-wrap summary:hover {
  border-color: #b366ff;
  box-shadow: 0 0 20px rgba(179,102,255,0.15);
}
.full-code-wrap .code-block {
  background: rgba(6,10,20,0.88);
  border-color: rgba(255,255,255,0.04);
}

/* ---- Buttons — neon with shine sweep ---- */
.btn {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 1px; border-radius: 8px;
  padding: 10px 22px;
  transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
  position: relative; overflow: hidden;
}
.btn::after {
  content: ""; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
  transition: left 0.5s;
}
.btn:hover::after { left: 100%; }
.btn-run {
  background: linear-gradient(135deg, rgba(0,240,255,0.16), rgba(0,200,220,0.06));
  color: #00f0ff; border-color: rgba(0,240,255,0.35);
  box-shadow: 0 0 20px rgba(0,240,255,0.12);
}
.btn-run:hover {
  box-shadow: 0 0 40px rgba(0,240,255,0.28), 0 0 70px rgba(0,240,255,0.07);
  border-color: #00f0ff;
}
.btn-demo {
  border-color: rgba(0,255,136,0.25); color: #00ff88;
}
.btn-demo:hover {
  box-shadow: 0 0 28px rgba(0,255,136,0.22);
  border-color: #00ff88;
}

/* ---- Output box ---- */
.output-box {
  background: rgba(6,10,20,0.65);
  border-color: rgba(255,255,255,0.05);
}

/* ---- Info table ---- */
.info-table th {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 0.5px; font-size: 11px;
  background: rgba(10,16,36,0.65);
  border-bottom-color: rgba(0,240,255,0.15);
}
.info-table td { border-bottom-color: rgba(255,255,255,0.03); }

/* ---- Chart wrap ---- */
.chart-wrap {
  background: rgba(8,14,30,0.45);
  border-color: rgba(255,255,255,0.04);
  border-radius: 12px;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

/* ---- Tags ---- */
.tag-immutable { background: rgba(255,45,120,0.1); border: 1px solid rgba(255,45,120,0.18); }
.tag-mutable   { background: rgba(0,255,136,0.1);   border: 1px solid rgba(0,255,136,0.18); }

/* ---- Demo panel ---- */
.demo-panel {
  background: rgba(10,16,36,0.45);
  border-color: rgba(255,255,255,0.04);
  border-radius: 12px;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
.demo-panel h3 {
  font-family: "Orbitron","Inter",sans-serif;
  letter-spacing: 1px;
  border-bottom-color: rgba(255,255,255,0.05);
}
.demo-step {
  background: rgba(6,10,20,0.38);
  border-color: rgba(255,255,255,0.02);
  transition: all 0.3s;
}
.demo-step:hover {
  border-color: rgba(0,240,255,0.08);
  box-shadow: 0 0 20px rgba(0,240,255,0.03);
}
.demo-step-num {
  background: linear-gradient(135deg, rgba(0,240,255,0.28), rgba(0,200,220,0.1));
  box-shadow: 0 0 12px rgba(0,240,255,0.2);
}
.demo-step-body .step-code { background: rgba(16,24,48,0.5); }

/* ---- Keyframe library ---- */
@keyframes pulse-ring {
  0% { transform: scale(0.8); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
}
@keyframes glitch-text {
  0%, 100% { transform: translate(0); }
  20% { transform: translate(-1px, 1px); }
  40% { transform: translate(-1px, -1px); }
  60% { transform: translate(1px, 1px); }
  80% { transform: translate(1px, -1px); }
}

/* ---- HUD corner accents on sections ---- */
.section {
  position: relative;
  --corner-size: 22px;
}
.section::before {
  content: ""; position: absolute; top: 0; left: 0;
  width: 32px; height: 32px;
  border-top: 2px solid rgba(0,240,255,0.25);
  border-left: 2px solid rgba(0,240,255,0.25);
  border-radius: 16px 0 0 0;
  pointer-events: none; z-index: 2;
}
.section::after {
  content: ""; position: absolute; top: 0; right: 0;
  width: 32px; height: 32px;
  border-top: 2px solid rgba(0,240,255,0.25);
  border-right: 2px solid rgba(0,240,255,0.25);
  border-radius: 0 16px 0 0;
  pointer-events: none; z-index: 2;
}

/* ---- Holographic shimmer on card hover ---- */
.card {
  position: relative; overflow: hidden;
}
.card::before {
  content: ""; position: absolute; inset: 0; z-index: 0;
  background: linear-gradient(
    125deg,
    transparent 25%,
    rgba(0,240,255,0.03) 43%,
    rgba(179,102,255,0.04) 48%,
    rgba(0,240,255,0.03) 53%,
    transparent 75%
  );
  background-size: 250% 250%;
  opacity: 0; transition: opacity 0.5s;
  pointer-events: none; border-radius: var(--radius);
}
.card:hover::before {
  opacity: 1;
  animation: holoShimmer 3.5s ease-in-out infinite;
}
@keyframes holoShimmer {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
/* Ensure card content stays above the shimmer */
.card > * { position: relative; z-index: 1; }

/* ---- Section h2 glitch on hover ---- */
.section h2 { transition: text-shadow 0.3s; }
.section h2:hover {
  animation: glitch-text 0.35s steps(1) forwards;
  text-shadow: 0 0 12px rgba(0,240,255,0.5);
}

/* ---- Bottom HUD corners on sections (via box-shadow trick) ---- */
.section {
  box-shadow:
    0 0 50px rgba(0,240,255,0.025),
    0 8px 32px rgba(0,0,0,0.5),
    inset 0 1px 0 rgba(255,255,255,0.02);
}

/* ---- Pulse indicator on active step-dot ---- */
.step-dot.active {
  animation: dotPulse 2s ease-in-out infinite;
}
@keyframes dotPulse {
  0%, 100% { box-shadow: 0 0 12px #00f0ff, 0 0 24px rgba(0,240,255,0.5); }
  50% { box-shadow: 0 0 20px #00f0ff, 0 0 36px rgba(0,240,255,0.7); }
}

/* ---- Nav-tag active glow pulse ---- */
.nav-tag.active {
  animation: navGlow 3s ease-in-out infinite;
}
@keyframes navGlow {
  0%, 100% { box-shadow: 0 0 25px rgba(0,240,255,0.3), inset 0 0 20px rgba(0,240,255,0.05); }
  50% { box-shadow: 0 0 35px rgba(0,240,255,0.45), inset 0 0 30px rgba(0,240,255,0.08); }
}

/* ---- Button hover scale + glow intensify ---- */
.btn:hover {
  transform: translateY(-2px) scale(1.03);
}

/* ---- Code block subtle border pulse ---- */
.code-panel {
  transition: border-color 0.5s, box-shadow 0.5s;
}
.code-panel:hover {
  border-color: rgba(0,240,255,0.15);
  box-shadow: 0 0 25px rgba(0,240,255,0.05);
}
</style>
</head>
<body>
<canvas id="starfield"></canvas>
<div class="cursor-glow" id="cursorGlow"></div>
<div class="app">

<header>
  <h1>Python 核心概念可视化教学</h1>
  <span class="nav-tag active" onclick="switchSection('dynamic')">1. 动态类型</span>
  <span class="nav-tag" onclick="switchSection('listmem')">2. 列表内存</span>
  <span class="nav-tag" onclick="switchSection('2dlist')">2D. 二维列表</span>
  <span class="nav-tag" onclick="switchSection('params')">3. 函数参数</span>
  <span class="nav-tag" onclick="switchSection('copy')">4. 深/浅拷贝</span>
  <span class="nav-tag" onclick="switchSection('string')">5. 字符串性能</span>
</header>

<!-- ================================================================ -->
<!-- 1. 动态类型 -->
<!-- ================================================================ -->
<div id="sec-dynamic" class="section active">
<h2>1. 动态类型 — 变量只是"名字标签"</h2>
<p class="subtitle">对比 C++: <code>int x = 42;</code> 不能变成 <code>string x = "hello";</code> — Python可以!</p>
<div class="card">
  <p style="line-height:1.8;font-size:14px;">
    在Python中, <b style="color:var(--cyan)">变量没有类型, 对象才有类型</b>。变量只是指向内存中对象的<b style="color:var(--pink)">标签/引用</b>。
    同一个变量可以先后指向5种完全不同类型的对象。对比C++: <code>int x = 5; x = "hello"; // ✗ 编译错误!</code> &nbsp; Python: <code>x = 5; x = "hello"  # ✓</code>
  </p>
</div>
<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: 静态类型 vs 动态类型</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — 静态类型 (编译时确定)</div>
      <div class="compare-col-body"><span class="kw">int</span> x = <span class="num">42</span>;        <span class="cmt">// x 的类型被锁定为 int</span>
<span class="kw">float</span> y = <span class="num">3.14f</span>;    <span class="cmt">// 需要声明新变量</span>
<span class="kw">std::string</span> z = <span class="str">"Hello"</span>; <span class="cmt">// 三种类型, 三个变量</span>

<span class="cmt">// C++17 std::variant 勉强模拟:</span>
std::variant&lt;<span class="kw">int</span>, <span class="kw">float</span>, std::string&gt; v;
v = <span class="num">42</span>;            <span class="cmt">// 存 int</span>
v = <span class="num">3.14f</span>;         <span class="cmt">// 存 float</span>
v = <span class="str">"Hello"</span>;       <span class="cmt">// 存 string</span>
<span class="kw">auto</span>* p = std::get_if&lt;std::string&gt;(&amp;v);</div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — 动态类型 (运行时确定)</div>
      <div class="compare-col-body"><span class="cmt"># 同一个变量名, 自由切换类型!</span>
x = <span class="num">42</span>         <span class="cmt"># x -> int 对象</span>
x = <span class="num">3.14</span>       <span class="cmt"># x -> float 对象</span>
x = <span class="str">"Hello"</span>    <span class="cmt"># x -> str 对象</span>
x = [<span class="num">1</span>, <span class="num">2</span>, <span class="num">3</span>]  <span class="cmt"># x -> list 对象</span>
x = {<span class="str">"key"</span>: <span class="str">"val"</span>} <span class="cmt"># x -> dict 对象</span>

<span class="cmt"># Python 变量本质: PyObject* 指针</span>
<span class="cmt"># 每次赋值只是改变指针指向</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ 变量在<b>编译时</b>绑定类型, 类型安全但缺乏灵活性; Python 变量只是一个<b>名字标签</b>, 在<b>运行时</b>指向带类型信息的对象, 灵活但运行时开销大。C++ <code>std::variant</code> 可模拟动态类型, 但使用远不如 Python 自然。</div>
</div>

<div id="dynamic-stepnav"></div>
<div class="step-content">
  <div class="step-svg" id="dynamic-svg"></div>
  <div class="code-panel" id="dynamic-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block">x = 42                # 步骤1: x是一个整数(int)
x = 3.14              # 步骤2: 同一个x, 现在变成了浮点数(float)
x = "Hello Python"    # 步骤3: x又变成了字符串(str)
x = [1, 2, 3]         # 步骤4: x又变成了列表(list)
x = {"key": "value"}  # 步骤5: x又变成了字典(dict)
# 这在C++/Java中是不可能的! 变量只是名字标签!</div>
</details>
<button class="btn btn-run" onclick="runDynamicDemo()">▶ 运行完整演示 (查看实际id值)</button>
<div id="dynamic-output" style="margin-top:10px;"></div>
</div>

<!-- ================================================================ -->
<!-- 2. 列表内存模型 -->
<!-- ================================================================ -->
<div id="sec-listmem" class="section">
<h2>2. 列表内存模型 — 列表存的是"引用"不是"值"</h2>
<p class="subtitle">对比C++: <code>int arr[3] = {1,2,3};</code> 数组存的是值本身 — Python列表存的是指针!</p>
<div class="card">
  <p style="line-height:1.8;font-size:14px;">
    Python的列表本质是一个<b style="color:var(--pink)">PyObject* 的数组</b>。每个元素都是指向实际对象的指针。
    <code>b = a</code> 只拷贝列表对象的引用, 而 <code>b = a.copy()</code> 创建新列表(但内部元素仍共享!).
  </p>
</div>
<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: 数组存值 vs 列表存指针</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — 数组/vector 存值 (连续内存)</div>
      <div class="compare-col-body"><span class="kw">int</span> arr[<span class="num">3</span>] = {<span class="num">10</span>, <span class="num">20</span>, <span class="num">30</span>};
<span class="cmt">// 内存布局: [10][20][30]  值紧挨着存放</span>

std::vector&lt;<span class="kw">int</span>&gt; a = {<span class="num">10</span>, <span class="num">20</span>, <span class="num">30</span>};
<span class="kw">auto</span> b = a;    <span class="cmt">// 深拷贝! b是a的完整副本</span>
b.push_back(<span class="num">999</span>);
<span class="cmt">// a 仍然是 {10,20,30}  — a和b完全独立!</span>

<span class="kw">int</span>* p = arr;   <span class="cmt">// 指针/引用 才共享</span>
p[<span class="num">3</span>] = <span class="num">999</span>;     <span class="cmt">// 这会修改 arr</span>
<span class="cmt">// C++ 默认赋值 = 拷贝, 必须显式用 &/* 才共享</span></div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — 列表存指针 (PyObject* 数组)</div>
      <div class="compare-col-body"><span class="cmt"># Python 列表内存: [*ptr][*ptr][*ptr]</span>
<span class="cmt"># 每个槽是一个指向 PyObject 的指针</span>
a = [<span class="num">10</span>, <span class="num">20</span>, <span class="num">30</span>]
b = a         <span class="cmt"># 浅拷贝! b和a指向同一个列表</span>
b.append(<span class="num">999</span>)
<span class="cmt"># a 也变成了 [10,20,30,999]!</span>

c = a.copy()  <span class="cmt"># 浅拷贝: 新列表, 但元素仍共享!</span>
<span class="cmt"># c[0] 和 a[0] 指向同一个 int 对象 10</span>
<span class="cmt"># 对不可变元素无影响, 可变元素则共享!</span>

<span class="cmt"># Python 赋值永远只是指针拷贝</span>
<span class="cmt"># 要独立副本必须显式 .copy() 或 deepcopy</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ 默认<b>值语义</b> — 赋值/传参会拷贝整个对象; Python 默认<b>引用语义</b> — 赋值/传参只拷贝指针。这导致 Python 中 <code>b = a</code> 后修改 b 会影响 a, 而 C++ 中不会。C++ 需要显式使用 <code>&amp;</code> 或 <code>*</code> 才能共享, Python 需要显式 <code>.copy()</code> 才能独立。</div>
</div>

<div id="listmem-stepnav"></div>
<div class="step-content">
  <div class="step-svg" id="listmem-svg"></div>
  <div class="code-panel" id="listmem-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block">a = [10, 20, 30]      # 步骤1: 创建一个列表对象
b = a                  # 步骤2: b和a指向同一个列表对象!
c = a.copy()           # 步骤3: c是一个新的列表(浅拷贝)
print(a is b)  # True  — 同一个对象!
print(a is c)  # False — 不同对象,但内容相同
print(a == c)  # True  — 值相等

b.append(999)          # 步骤4: 通过b修改列表
print(a)  # [10, 20, 30, 999] ← a也变了! (同一对象)
print(c)  # [10, 20, 30]      ← c不受影响 (独立对象)</div>
</details>
<button class="btn btn-run" onclick="runListMemDemo()">▶ 运行完整演示 (查看实际id对比)</button>
<div id="listmem-output" style="margin-top:10px;"></div>
</div>

<!-- ================================================================ -->
<!-- 2D. 二维列表内存模型 -->
<!-- ================================================================ -->
<div id="sec-2dlist" class="section">
<h2>2D. 二维列表 — 嵌套指针数组的内存结构</h2>
<p class="subtitle">二维列表本质: 外层列表存的是指向内层列表的指针 — matrix[i][j] 经过两次指针跳转!</p>
<div class="card">
  <p style="line-height:1.8;font-size:14px;">
    Python的<b style="color:var(--pink);">二维列表</b>不是连续矩阵, 而是<b style="color:var(--cyan);">指针的数组的数组</b>。
    <code>matrix = [[1,2,3],[4,5,6],[7,8,9]]</code> 实际上是:
    外层列表对象 → [*ptr0, *ptr1, *ptr2] → 每个ptr指向一个内层列表对象。
    这意味着 <b style="color:var(--amber);">matrix[0]</b> 得到的是指向内层列表的引用,
    <b style="color:var(--pink);">浅拷贝(matrix.copy())</b> 只复制外层, 内层列表仍然共享!
  </p>
</div>
<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: 连续二维数组 vs 指针链</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — 连续内存的二维数组</div>
      <div class="compare-col-body"><span class="cmt">// C++ 二维数组: 一块连续内存</span>
<span class="kw">int</span> matrix[<span class="num">3</span>][<span class="num">3</span>] = {
    {<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>},
    {<span class="num">4</span>,<span class="num">5</span>,<span class="num">6</span>},
    {<span class="num">7</span>,<span class="num">8</span>,<span class="num">9</span>}
};
<span class="cmt">// 内存布局: [1][2][3][4][5][6][7][8][9] 连续!</span>
<span class="cmt">// matrix[1][2] = 直接地址计算: *(matrix+1*3+2)</span></div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — 指针链结构</div>
      <div class="compare-col-body"><span class="cmt"># Python 二维列表: 指针的指针</span>
matrix = [[<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>],
          [<span class="num">4</span>,<span class="num">5</span>,<span class="num">6</span>],
          [<span class="num">7</span>,<span class="num">8</span>,<span class="num">9</span>]]
<span class="cmt"># 外层列表 → [*][*][*]</span>
<span class="cmt">#              ↓  ↓  ↓</span>
<span class="cmt"># 内层列表   [1,2,3] [4,5,6] [7,8,9]</span>
<span class="cmt"># matrix[1][2] = 先找外层[1]→内层, 再找[2]</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ 的二维数组是<b>连续内存块</b>, 通过简单的地址计算访问 (O(1)); Python 的二维列表是<b>指针链</b>, 需要两次指针跳转才能访问到元素。Python 这种结构更灵活 (每行长度可以不同), 但访问速度较慢且内存不连续。另外 Python 浅拷贝只复制外层指针数组, 内层列表全部<b>共享</b> — 这是常见的 bug 来源!</div>
</div>

<div id="2dlist-stepnav"></div>
<div class="step-content" style="grid-template-columns:1fr;">
  <div class="step-svg" id="2dlist-svg"></div>
  <div class="code-panel" id="2dlist-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block">matrix = [[1, 2, 3],        # 步骤1: 创建3x3二维列表
         [4, 5, 6],        # 外层列表有3个元素, 每个是指向内层列表的指针
         [7, 8, 9]]

row0 = matrix[0]             # 步骤2: row0指向第一行 (同一个对象!)
shallow = matrix.copy()      # 步骤3: 浅拷贝 — 只复制外层, 内层共享!
deep = copy.deepcopy(matrix) # 步骤4: 深拷贝 — 递归复制, 完全独立

row0[0] = 999                # 步骤5: 修改row0 → matrix[0]也变了!
shallow[1][1] = 888          # 步骤6: 修改浅拷贝内层 → matrix也变了!</div>
</details>
<button class="btn btn-run" onclick="run2DListDemo()">▶ 运行完整演示 (查看实际id对比)</button>
<div id="2dlist-output" style="margin-top:10px;"></div>
</div>

<!-- ================================================================ -->
<!-- 3. 函数参数传递 -->
<!-- ================================================================ -->
<div id="sec-params" class="section">
<h2>3. 函数参数传递 — "传对象引用"</h2>
<p class="subtitle">对比C++: 有传值/传指针/传引用三种 — Python只有一种: 传对象引用!</p>

<div class="grid3">
  <div class="card" style="margin-bottom:0;">
    <h3><span class="tag tag-immutable">不可变</span> int/str/tuple</h3>
    <p style="font-size:13px;line-height:1.7;">类似C++的<b>传值</b>。<span style="color:var(--text2);">不可变对象无法原地修改, n+=100其实是创建新对象。</span></p>
    <div class="code-block"><span class="kw">def</span> <span class="fn">modify</span>(n):
    n += <span class="num">100</span>
x = <span class="num">10</span>; modify(x)
<span class="cmt"># x 仍然是 10!</span></div>
  </div>
  <div class="card" style="margin-bottom:0;">
    <h3><span class="tag tag-mutable">可变</span> list/dict/set</h3>
    <p style="font-size:13px;line-height:1.7;">类似C++的<b>传指针</b>。<span style="color:var(--text2);">通过引用找到对象, 原地修改(.append)外部可见。</span></p>
    <div class="code-block"><span class="kw">def</span> <span class="fn">modify</span>(lst):
    lst.append(<span class="num">999</span>)
my_list = [<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>]; modify(my_list)
<span class="cmt"># my_list → [1,2,3,999]!</span></div>
  </div>
  <div class="card" style="margin-bottom:0;">
    <h3>赋值 vs 修改 (关键!)</h3>
    <p style="font-size:13px;line-height:1.7;">函数内<b>= 赋值</b>只改变局部变量。<span style="color:var(--text2);">= 让局部变量指向新对象, 原变量不变。</span></p>
    <div class="code-block"><span class="kw">def</span> <span class="fn">reassign</span>(lst):
    lst = [<span class="num">4</span>,<span class="num">5</span>,<span class="num">6</span>]
my_list = [<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>]; reassign(my_list)
<span class="cmt"># my_list 还是 [1,2,3]!</span></div>
  </div>
</div>

<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: 三种参数传递 vs Python 一种</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — 三种传递方式 (显式选择)</div>
      <div class="compare-col-body"><span class="cmt">// ① 传值: 拷贝整个对象</span>
<span class="kw">void</span> modify(<span class="kw">int</span> n) { n += <span class="num">100</span>; }
<span class="kw">int</span> x = <span class="num">10</span>; modify(x); <span class="cmt">// x 还是 10</span>

<span class="cmt">// ② 传指针: 共享原对象</span>
<span class="kw">void</span> modify(vector&lt;<span class="kw">int</span>&gt;* p) { p-&gt;push_back(<span class="num">999</span>); }
vector&lt;<span class="kw">int</span>&gt; v{<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>}; modify(&amp;v); <span class="cmt">// v 变了</span>

<span class="cmt">// ③ 传引用: 语法糖, 像值但共享</span>
<span class="kw">void</span> modify(vector&lt;<span class="kw">int</span>&gt;&amp; r) { r.push_back(<span class="num">999</span>); }
modify(v); <span class="cmt">// v 变了 (像传值语法, 但有共享语义)</span>

<span class="cmt">// 选择权在调用方 — 显式决定语义</span></div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — 统一"传对象引用"</div>
      <div class="compare-col-body"><span class="cmt"># Python 只有一种: 传对象引用 (Call by Sharing)</span>
<span class="cmt"># 实际传递的是指向对象的指针的拷贝</span>

<span class="kw">def</span> <span class="fn">modify_int</span>(n):
    n += <span class="num">100</span>    <span class="cmt"># int 不可变 -> 创建新对象, n指向新int</span>
x = <span class="num">10</span>; modify_int(x)  <span class="cmt"># x 不变! (类似传值)</span>

<span class="kw">def</span> <span class="fn">modify_list</span>(lst):
    lst.append(<span class="num">999</span>)  <span class="cmt"># list 可变 -> 原地修改</span>
my = [<span class="num">1</span>,<span class="num">2</span>,<span class="num">3</span>]; modify_list(my) <span class="cmt"># my 变了! (类似传指针)</span>

<span class="cmt"># 行为取决于对象是否可变, 不取决于语法!</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ 提供<b>传值/传指针/传引用</b>三种方式, 调用方显式选择语义; Python 统一使用<b>传对象引用</b> (传指针的拷贝), 行为取决于对象的可变性。Python 的 <code>=</code> 赋值在函数内只改变局部变量名的指向, 永远不影响外部变量 — 这类似于 C++ 中修改指针形参本身不影响实参。</div>
</div>

<div id="params-stepnav"></div>
<div class="step-content">
  <div class="step-svg" id="params-svg"></div>
  <div class="code-panel" id="params-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block"># 场景1: 不可变对象 (int)
def modify_int(n):
    n += 100        # n指向新对象, x不变
    return n
x = 10
modify_int(x)        # x 仍然是 10

# 场景2: 可变对象 (list)
def modify_list(lst):
    lst.append(999)  # 原地修改, 外部可见
my_list = [1, 2, 3]
modify_list(my_list) # my_list → [1,2,3,999]

# 场景3: 赋值 vs 修改
def reassign(lst):
    lst = [4,5,6]    # 仅局部变量指向新列表!
my_list2 = [1, 2, 3]
reassign(my_list2)   # my_list2 还是 [1,2,3]</div>
</details>
<button class="btn btn-run" onclick="runParamsDemo()">▶ 运行完整演示</button>
<div id="params-output" style="margin-top:10px;"></div>
</div>

<!-- ================================================================ -->
<!-- 4. 深拷贝 vs 浅拷贝 -->
<!-- ================================================================ -->
<div id="sec-copy" class="section">
<h2>4. 深拷贝 vs 浅拷贝 — 嵌套结构的"克隆"难题</h2>
<p class="subtitle">对比C++: 默认拷贝构造函数是浅拷贝 — Python需要显式使用 copy.deepcopy()!</p>
<div class="card">
  <p style="line-height:1.8;font-size:14px;">
    <b style="color:var(--pink);">浅拷贝 (.copy / list() / [:])</b>: 只复制<b>第一层</b>, 嵌套子对象仍是<b>共享</b>的!
    &nbsp; | &nbsp;
    <b style="color:var(--green);">深拷贝 (copy.deepcopy)</b>: 递归复制<b>所有层</b>, 原对象和新对象<b>完全独立</b>.
  </p>
</div>
<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: 拷贝构造函数 vs copy 模块</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — 默认拷贝是浅拷贝</div>
      <div class="compare-col-body"><span class="cmt">// C++ 默认拷贝构造函数 = 浅拷贝 (逐成员复制)</span>
<span class="kw">struct</span> Node { <span class="kw">int</span> val; Node* next; };
Node* a = <span class="kw">new</span> Node{<span class="num">1</span>, <span class="kw">new</span> Node{<span class="num">2</span>, <span class="kw">nullptr</span>}};
Node b = *a;  <span class="cmt">// 浅拷贝! b.next == a->next (共享!)</span>
b.next->val = <span class="num">999</span>; <span class="cmt">// a->next->val 也变成了 999!</span>

<span class="cmt">// 需要深拷贝必须手动实现:</span>
<span class="kw">struct</span> Node {
    <span class="kw">int</span> val; Node* next;
    Node* deep_copy() {
        <span class="kw">auto</span>* p = <span class="kw">new</span> Node{val, <span class="kw">nullptr</span>};
        <span class="kw">if</span> (next) p->next = next->deep_copy();
        <span class="kw">return</span> p;
    }
};
<span class="kw">auto</span>* c = a->deep_copy(); <span class="cmt">// 完全独立!</span></div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — .copy() 是浅拷贝, deepcopy 需 import</div>
      <div class="compare-col-body"><span class="kw">import</span> copy
original = [<span class="num">1</span>, <span class="num">2</span>, [<span class="num">10</span>, <span class="num">20</span>, <span class="num">30</span>], <span class="num">3</span>]

shallow = original.copy()  <span class="cmt"># 浅拷贝: 嵌套对象共享!</span>
<span class="cmt"># shallow[2] is original[2]  -> True!</span>

deep = copy.deepcopy(original)  <span class="cmt"># 深拷贝: 递归复制</span>
<span class="cmt"># deep[2] is original[2]  -> False!</span>

shallow[<span class="num">2</span>].append(<span class="num">999</span>)
<span class="cmt"># original[2] 也变了! 但 deep[2] 不受影响</span>

<span class="cmt"># Python 浅拷贝手段: .copy(), list(), [:]</span>
<span class="cmt"># 它们都只复制第一层, 内层仍共享!</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ 默认拷贝是<b>浅拷贝</b> (逐成员复制指针值), 深拷贝需手写递归函数; Python 同样默认浅拷贝, 但提供了 <code>copy.deepcopy()</code> 一键深拷贝。Python 的优势是内置了通用的深拷贝机制 (通过 __deepcopy__ 协议), C++ 则需要为每个类型手动实现深拷贝 (五法则)。</div>
</div>

<div id="copy-stepnav"></div>
<div class="step-content">
  <div class="step-svg" id="copy-svg"></div>
  <div class="code-panel" id="copy-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block">import copy
original = [1, 2, [10, 20, 30], 3]   # 步骤1: 原始嵌套列表

shallow = original.copy()             # 步骤2: 浅拷贝 — 内层列表共享!
deep = copy.deepcopy(original)        # 步骤3: 深拷贝 — 完全独立

# 验证: 查看嵌套对象的id
print(id(original[2]))  # 内层列表的id
print(id(shallow[2]))   # 和original[2]的id相同! (共享)
print(id(deep[2]))      # 不同的id (独立)

shallow[2].append(999)  # 步骤4: 修改浅拷贝的内层列表
print(original)  # [1, 2, [10, 20, 30, 999], 3] ← 也变了!
print(shallow)   # [1, 2, [10, 20, 30, 999], 3]
print(deep)      # [1, 2, [10, 20, 30], 3]       ← 不受影响!</div>
</details>
<button class="btn btn-run" onclick="runCopyDemo()">▶ 运行完整演示 (查看实际id对比)</button>
<div id="copy-output" style="margin-top:10px;"></div>
</div>

<!-- ================================================================ -->
<!-- 5. 字符串拼接性能 -->
<!-- ================================================================ -->
<div id="sec-string" class="section">
<h2>5. 字符串拼接性能 — 为什么 join() 比 + 快几百倍?</h2>
<p class="subtitle">核心原因: 字符串是不可变对象, 每次+都创建新字符串 (O(n²) vs O(n))</p>
<div class="card">
  <table class="info-table">
    <tr><th>方式</th><th>时间复杂度</th><th>内存分配</th><th>n=100000耗时</th><th>原理</th></tr>
    <tr><td style="color:var(--pink);">s += str(i)</td><td>O(n²)</td><td>n 次</td><td>约 5000ms+</td><td>每次+都创建新字符串对象</td></tr>
    <tr><td style="color:var(--green);">"".join(...)</td><td>O(n)</td><td>1 次</td><td>约 5ms</td><td>一次计算总长度, 一次分配</td></tr>
  </table>
</div>
<button class="btn btn-run" onclick="runStringPerfDemo()" style="margin-bottom:16px;">▶ 运行性能测试 (约5-10秒)</button>
<div class="card" style="border-color:rgba(255,171,0,0.2);margin-top:16px;">
  <h3>C++ 对比: std::string 可变 vs str 不可变</h3>
  <div class="compare-panel">
    <div class="compare-col">
      <div class="compare-col-header cpp">C++ — std::string 可变 (in-place modify)</div>
      <div class="compare-col-body"><span class="cmt">// C++ std::string 是可变的 — 原地修改!</span>
std::string s = <span class="str">""</span>;
<span class="kw">for</span> (<span class="kw">int</span> i = <span class="num">0</span>; i < n; i++) {
    s += std::to_string(i);  <span class="cmt">// 追加到已有缓冲区</span>
}  <span class="cmt">// O(n) 总时间 (amortized)</span>

<span class="cmt">// 或者更高效: 先 reserve, 避免多次 realloc</span>
s.reserve(expected_size);

<span class="cmt">// C++ 也可用 ostringstream:</span>
std::ostringstream oss;
<span class="kw">for</span> (<span class="kw">int</span> i = <span class="num">0</span>; i < n; i++) oss &lt;&lt; i;
s = oss.str();  <span class="cmt">// O(n), 类似 join</span>

<span class="cmt">// 结论: C++ string 可变, += 本身是 O(1) amortized</span></div>
    </div>
    <div class="compare-col">
      <div class="compare-col-header py">Python — str 不可变 (每次+创建新对象)</div>
      <div class="compare-col-body"><span class="cmt"># Python 字符串是不可变对象!</span>
s = <span class="str">""</span>
<span class="kw">for</span> i <span class="kw">in</span> range(n):
    s += str(i)  <span class="cmt"># 每次创建全新 str 对象!</span>
<span class="cmt"># 旧 s 被丢弃 -> GC 回收 -> 大量内存分配</span>
<span class="cmt"># 总复杂度: O(n^2)  因为每次都要复制旧内容</span>

<span class="cmt"># 正确做法: join 一次性分配</span>
s = <span class="str">""</span>.join(str(i) <span class="kw">for</span> i <span class="kw">in</span> range(n))
<span class="cmt"># 总复杂度: O(n)  只分配一次内存</span>

<span class="cmt"># 性能差距: n=100000 时 +拼接~5000ms, join~5ms</span></div>
    </div>
  </div>
  <div class="compare-verdict"><strong>核心差异:</strong> C++ <code>std::string</code> 是<b>可变对象</b>, <code>+=</code> 可以在原有缓冲区后追加 (O(1) amortized); Python <code>str</code> 是<b>不可变对象</b>, 每次 <code>+=</code> 都创建全新字符串并复制所有内容 (O(n) per operation), 导致 O(n^2) 总复杂度。这是 Python 字符串拼接极慢的根本原因 — 必须用 <code>join()</code> 替代循环中的 <code>+=</code>。</div>
</div>

<div id="string-stepnav"></div>
<div class="step-content">
  <div class="chart-wrap" id="string-chartwrap"><canvas id="stringChart"></canvas></div>
  <div class="code-panel" id="string-code"></div>
</div>
<details class="full-code-wrap">
  <summary>📋 查看完整代码</summary>
  <div class="code-block"># 方式1: + 拼接 (慢 — O(n²))
s = ""
for i in range(100000):
    s += str(i)       # 每次循环创建新字符串!

# 方式2: join 拼接 (快 — O(n))
s = "".join(str(i) for i in range(100000))  # 一次分配

# 为什么? 字符串是不可变对象!
# s += x 每次都要: 分配新内存 + 复制旧内容 + 追加新内容 + 丢弃旧字符串
# join() 一次性计算总长度, 一次性分配内存, 一次性写入</div>
</details>
<div id="string-output" style="margin-top:10px;"></div>
</div>


</div><!-- /.app -->

<script>
// ===== 导航 =====
function switchSection(name) {
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.getElementById('sec-' + name).classList.add('active');
  document.querySelectorAll('.nav-tag').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  if (name === 'string' && !window._strChartInit) initStringSection();
}

// ===== 通用: 步骤导航渲染 =====
function renderStepNav(sectionId, steps, currentStep) {
  const nav = document.getElementById(sectionId + '-stepnav');
  if (!nav) return;
  nav.innerHTML = `
    <div class="step-nav">
      <button class="step-nav-btn" onclick="gotoStep('${sectionId}', ${currentStep - 1})"
        ${currentStep === 0 ? 'disabled' : ''}>◀ 上一步</button>
      <div class="step-dots">
        ${steps.map((s, i) => `<button class="step-dot${i === currentStep ? ' active' : ''}${i < currentStep ? ' done' : ''}"
          onclick="gotoStep('${sectionId}', ${i})" title="${s.label}"></button>`).join('')}
      </div>
      <button class="step-nav-btn" onclick="gotoStep('${sectionId}', ${currentStep + 1})"
        ${currentStep === steps.length - 1 ? 'disabled' : ''}>下一步 ▶</button>
      <span class="step-label">步骤 ${currentStep + 1}/${steps.length}: ${steps[currentStep].label}</span>
    </div>`;
}

function renderCodePanel(panelId, code, highlightLines) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const lines = code.split('\n');
  panel.innerHTML = `
    <div class="code-panel-header">当前步骤对应的代码 (高亮行)</div>
    <div class="code-panel-body">
      ${lines.map((l, i) => `<div class="code-line${highlightLines.includes(i+1) ? ' hl' : ''}">
        <span class="ln">${i+1}</span><span class="ct">${l || ' '}</span></div>`).join('')}
    </div>`;
}

function gotoStep(sectionId, stepIdx) {
  window._stepState = window._stepState || {};
  const state = window._stepState[sectionId];
  if (!state || stepIdx < 0 || stepIdx >= state.steps.length) return;
  state.current = stepIdx;
  const s = state.steps[stepIdx];
  renderStepNav(sectionId, state.steps, stepIdx);
  document.getElementById(sectionId + '-svg').innerHTML = s.svg();
  renderCodePanel(sectionId + '-code', s.code, s.highlight || []);
}

// ===== SVG helper =====
function boxEl(x, y, w, h, label, color, fs) { 
  fs = fs || 13;
  // Outer glow ring + inner filled rect + label
  return '<rect x="' + (x-1.5) + '" y="' + (y-1.5) + '" width="' + (w+3) + '" height="' + (h+3) + '" rx="7" fill="none" stroke="' + color + '" stroke-width="2.5" opacity="0.18"/>' +
    '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="6" fill="' + color + '10" stroke="' + color + '" stroke-width="1.3"/>' +
    '<text x="' + (x + w / 2) + '" y="' + (y + h / 2 + fs / 3) + '" text-anchor="middle" fill="' + color + '" font-size="' + fs + '" font-weight="600">' + label + '</text>';
}
function arrowEl(x1, y1, x2, y2, color) {
  var a = Math.atan2(y2 - y1, x2 - x1), L = 8;
  // Glow line behind
  return '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="' + color + '" stroke-width="3.5" opacity="0.18"/>' +
    '<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="' + color + '" stroke-width="1.5"/>' +
    '<polygon points="' + x2 + ',' + y2 + ' ' + (x2 - L * Math.cos(a - Math.PI / 6)) + ',' + (y2 - L * Math.sin(a - Math.PI / 6)) + ' ' + (x2 - L * Math.cos(a + Math.PI / 6)) + ',' + (y2 - L * Math.sin(a + Math.PI / 6)) + '" fill="' + color + '"/>';
}

// ===================================================================
// 步骤数据定义
// ===================================================================

// --- 1. 动态类型 ---
function initDynamicSteps() {
  const colors = ['#ff4081','#00e5ff','#00e676','#ffab00','#b388ff'];
  const types = ['int','float','str','list','dict'];
  const vals = ['42','3.14',"'Hello Python'",'[1, 2, 3]',"{'key': 'value'}"];
  return {
    steps: [
      {label:'int整数', highlight:[1],
        svg:()=>renderDynamicStepSVG(0),
        code:'x = 42\nx = 3.14\nx = "Hello Python"\nx = [1, 2, 3]\nx = {"key": "value"}'},
      {label:'float浮点数', highlight:[1,2],
        svg:()=>renderDynamicStepSVG(1),
        code:'x = 42\nx = 3.14\nx = "Hello Python"\nx = [1, 2, 3]\nx = {"key": "value"}'},
      {label:'str字符串', highlight:[1,2,3],
        svg:()=>renderDynamicStepSVG(2),
        code:'x = 42\nx = 3.14\nx = "Hello Python"\nx = [1, 2, 3]\nx = {"key": "value"}'},
      {label:'list列表', highlight:[1,2,3,4],
        svg:()=>renderDynamicStepSVG(3),
        code:'x = 42\nx = 3.14\nx = "Hello Python"\nx = [1, 2, 3]\nx = {"key": "value"}'},
      {label:'dict字典', highlight:[1,2,3,4,5],
        svg:()=>renderDynamicStepSVG(4),
        code:'x = 42                # int\nx = 3.14              # float\nx = "Hello Python"    # str\nx = [1, 2, 3]         # list\nx = {"key": "value"}  # dict'},
    ], current: 0,
  };

  function renderDynamicStepSVG(maxIdx) {
    const W=560, H=320;
    let s = `<svg width="${W}" height="${H}"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">变量名 "x" 指向 → 不同类型对象</text>`;
    s += boxEl(30, 48, 55, 26, 'x', '#00e5ff', 14);
    s += `<text x="57" y="95" text-anchor="middle" fill="#8b949e" font-size="10">变量名</text>`;
    s += `<line x1="57" y1="102" x2="57" y2="130" stroke="#94a3b8" stroke-dasharray="4,3" stroke-width="1"/>`;
    for (let i=0; i<=maxIdx; i++) {
      const y=138+i*34, cx=57, bx=120, bw=400;
      s += `<line x1="${cx}" y1="${y}" x2="${bx}" y2="${y+12}" stroke="#94a3b8" stroke-dasharray="4,3" stroke-width="1"/>`;
      s += `<polygon points="${bx-2},${y+8} ${bx+4},${y+12} ${bx-2},${y+16}" fill="#94a3b8"/>`;
      s += `<rect x="${bx}" y="${y}" width="${bw}" height="26" rx="6"
        fill="${colors[i]}15" stroke="${colors[i]}" stroke-width="1.5"/>
        <text x="${bx+12}" y="${y+18}" fill="${colors[i]}" font-size="11" font-weight="600">${types[i]}</text>
        <text x="${bx+80}" y="${y+18}" fill="#c9d1d9" font-size="11">${vals[i]}</text>`;
    }
    s += `<text x="280" y="310" text-anchor="middle" fill="#8b949e" font-size="11">同一个变量名 x, 先后指向不同对象 — 这就是"动态类型"</text>`;
    s += `</svg>`; return s;
  }
}

// --- 2. 列表内存 ---
function initListmemSteps() {
  return {
    steps: [
      {label:'创建列表', highlight:[1],
        svg:()=>renderListmemStep(0),
        code:'a = [10, 20, 30]\nb = a\nc = a.copy()\nb.append(999)'},
      {label:'b = a 赋值', highlight:[1,2],
        svg:()=>renderListmemStep(1),
        code:'a = [10, 20, 30]\nb = a\nc = a.copy()\nb.append(999)'},
      {label:'c = a.copy()', highlight:[1,2,3],
        svg:()=>renderListmemStep(2),
        code:'a = [10, 20, 30]\nb = a\nc = a.copy()\nb.append(999)'},
      {label:'b.append结果', highlight:[1,2,3,4],
        svg:()=>renderListmemStep(3),
        code:'a = [10, 20, 30]      # 原始列表\nb = a                  # 同一个对象!\nc = a.copy()           # 新列表\nappend(999)\n# a和b都变了, c不受影响'},
    ], current: 0,
  };

  function renderListmemStep(step) {
    const W=560, H=340, showB=(step>=1), showC=(step>=2), modified=(step>=3);
    let ids=['A','B','C'], s=`<svg width="${W}" height="${H}"><text x="280" y="20" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">列表内存模型: 变量→列表对象→元素</text>`;

    // a 变量
    s += boxEl(20, 42, 48, 26, 'a', '#00e5ff', 13);
    if (step >= 1) { s += boxEl(20, 125, 48, 26, 'b', '#ffab00', 13); }
    if (step >= 2) { s += boxEl(20, 208, 48, 26, 'c', '#00e676', 13); }

    // a的列表
    s += `<rect x="90" y="35" width="${modified?390:330}" height="52" rx="7" fill="#0d3320" stroke="#00e5ff" stroke-width="1.3"/>
      <text x="105" y="55" fill="#8b949e" font-size="9">列表对象 id=...</text>
      <rect x="105" y="62" width="50" height="18" rx="3" fill="#1e2d45"/><text x="130" y="75" text-anchor="middle" fill="#c9d1d9" font-size="11">10</text>
      <rect x="160" y="62" width="50" height="18" rx="3" fill="#1e2d45"/><text x="185" y="75" text-anchor="middle" fill="#c9d1d9" font-size="11">20</text>
      <rect x="215" y="62" width="50" height="18" rx="3" fill="#1e2d45"/><text x="240" y="75" text-anchor="middle" fill="#c9d1d9" font-size="11">30</text>`;
    if (modified) {
      s += `<rect x="270" y="62" width="50" height="18" rx="3" fill="#1e2d45"/><text x="295" y="75" text-anchor="middle" fill="#ffab00" font-size="11">999</text>
        <text x="380" y="75" fill="#ffab00" font-size="10">← b添加的</text>`;
    }

    // c的列表 (独立)
    if (step >= 2) {
      s += `<rect x="90" y="200" width="330" height="52" rx="7" fill="#0d3315" stroke="#00e676" stroke-width="1.3"/>
        <text x="105" y="220" fill="#8b949e" font-size="9">列表对象 id=... (独立)</text>
        <rect x="105" y="227" width="50" height="18" rx="3" fill="#1e2d45"/><text x="130" y="240" text-anchor="middle" fill="#c9d1d9" font-size="11">10</text>
        <rect x="160" y="227" width="50" height="18" rx="3" fill="#1e2d45"/><text x="185" y="240" text-anchor="middle" fill="#c9d1d9" font-size="11">20</text>
        <rect x="215" y="227" width="50" height="18" rx="3" fill="#1e2d45"/><text x="240" y="240" text-anchor="middle" fill="#c9d1d9" font-size="11">30</text>`;
      s += `<line x1="68" y1="221" x2="88" y2="226" stroke="#00e676" stroke-width="1.5"/>`;
    }

    // 箭头
    s += `<line x1="68" y1="55" x2="88" y2="61" stroke="#00e5ff" stroke-width="1.5"/>`;
    if (step >= 1) { s += `<line x1="68" y1="138" x2="88" y2="85" stroke="#ffab00" stroke-width="1.5"/>`; }

    s += `<text x="280" y="325" text-anchor="middle" fill="#8b949e" font-size="10">${step===0?'创建列表':step===1?'b=a → 同一个对象!':step===2?'c=copy → 独立对象':step===3?'修改b → a也变了! c不变':''}</text>`;
    s += `</svg>`; return s;
  }
}

// --- 2D. 二维列表 ---
function init2DListSteps() {
  return {
    steps: [
      {label:'创建二维列表', highlight:[1,2,3],
        svg:()=>render2DListStep(0),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]'},
      {label:'row0=matrix[0]', highlight:[1,2,3,5],
        svg:()=>render2DListStep(1),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]\n\nrow0 = matrix[0]'},
      {label:'浅拷贝', highlight:[1,2,3,5,6],
        svg:()=>render2DListStep(2),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]\nrow0 = matrix[0]\n\nshallow = matrix.copy()'},
      {label:'深拷贝', highlight:[1,2,3,5,6,7],
        svg:()=>render2DListStep(3),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]\nrow0 = matrix[0]\nshallow = matrix.copy()\n\ndeep = copy.deepcopy(matrix)'},
      {label:'修改row0', highlight:[1,2,3,5,6,7,9],
        svg:()=>render2DListStep(4),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]\nrow0 = matrix[0]\nshallow = matrix.copy()\ndeep = copy.deepcopy(matrix)\n\nrow0[0] = 999  # matrix[0][0]也变!'},
      {label:'修改shallow内层', highlight:[1,2,3,5,6,7,9,10],
        svg:()=>render2DListStep(5),
        code:'matrix = [[1, 2, 3],\n         [4, 5, 6],\n         [7, 8, 9]]\nrow0 = matrix[0]\nshallow = matrix.copy()\ndeep = copy.deepcopy(matrix)\n\nrow0[0] = 999\nshallow[1][1] = 888  # matrix也变!'},
    ], current: 0,
  };

  function render2DListStep(step) {
    const showRow0 = step >= 1, showShallow = step >= 2, showDeep = step >= 3;
    const modRow0 = step >= 4, modShallow = step >= 5;

    // ===== tree layout constants =====
    const vX = 10, vW = 72, vH = 26;          // variable label
    const tX = 100;                             // trunk vertical x
    const sX = 118, sW = 36, sH = 24;          // [*] slot
    const sR = sX + sW;                         // slot right edge
    const iX = 175, iW = 140;                  // inner list
    const ROW = 32;                             // row height
    const IC = ['#ff4081', '#ffab00', '#00e676'];

    // ===== helpers =====
    function box(x, y, w, h, c, t, fs, hl, dashed) {
      const sc = hl ? '#ff4060' : c;
      const sw = hl ? '2' : '0.9';
      const ds = dashed ? ' stroke-dasharray="4,3"' : '';
      return `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="${c}12" stroke="${sc}" stroke-width="${sw}"${ds}/>
        <text x="${x+w/2}" y="${y+h/2+4}" text-anchor="middle" fill="${hl?'#ff4060':c}" font-size="${fs||11}" font-weight="600">${t}</text>`;
    }
    function hLine(x1, x2, y, c, dashed) {
      const d = dashed ? ' stroke-dasharray="5,3"' : '';
      return `<line x1="${x1}" y1="${y}" x2="${x2}" y2="${y}" stroke="${c}" stroke-width="1.3"${d}/>`;
    }
    function vLine(x, y1, y2, c) {
      return `<line x1="${x}" y1="${y1}" x2="${x}" y2="${y2}" stroke="${c}" stroke-width="1.3"/>`;
    }
    function arrowHd(x, y, c) {
      return `<polygon points="${x},${y} ${x-5},${y-7} ${x+5},${y-7}" fill="${c}"/>`;
    }

    // Draw a complete tree: variable → trunk → slots → inner lists
    // Returns the y after the tree (bottom + gap)
    function drawTree(varName, varColor, topY, rowsData, shared) {
      const r0 = topY + 10, r1 = r0 + ROW, r2 = r0 + 2 * ROW;
      const mid = (r0 + 12) + (r2 + 12 - (r0 + 12)) / 2; // center of the 3-row block
      const bot = r2 + sH + 12;

      // Variable label
      s += box(vX, mid - vH / 2, vW, vH, varColor, varName, 12);

      // Horizontal connector from var to trunk
      s += hLine(vX + vW, tX, mid, varColor);
      s += arrowHd(tX, mid, varColor);

      // Vertical trunk spanning all 3 rows
      s += vLine(tX, r0 + sH / 2, r2 + sH / 2, varColor);

      for (let i = 0; i < 3; i++) {
        const ry = [r0, r1, r2][i];
        const rc = rowsData[i].color || IC[i];
        const rm = ry + sH / 2;
        const vals = rowsData[i].vals;
        const hlIdx = rowsData[i].hlIdx;

        // Horizontal branch from trunk to slot
        s += hLine(tX, sX, rm, rc);
        s += arrowHd(sX, rm, rc);

        // Slot [*]
        s += box(sX, ry, sW, sH, rc, '*', 10);

        // Slot → inner list connector
        s += hLine(sR, iX, rm, rc, shared);
        if (!shared) s += arrowHd(iX, rm, rc);

        // Inner list with 3 value cells
        const iy = rm - sH / 2;
        s += `<rect x="${iX}" y="${iy}" width="${iW}" height="${sH}" rx="4" fill="${rc}0c" stroke="${rc}" stroke-width="${shared?1:1}"${shared?' stroke-dasharray="4,3"':''}/>`;
        for (let j = 0; j < 3; j++) {
          const vx = iX + 10 + j * 41;
          const isHl = hlIdx === j;
          s += `<rect x="${vx}" y="${iy+3}" width="36" height="${sH-6}" rx="3" fill="#0d1117" stroke="${isHl?'#ff4060':rc}" stroke-width="${isHl?'1.6':'0.7'}"/>`;
          s += `<text x="${vx+18}" y="${iy+sH/2+4}" text-anchor="middle" fill="${isHl?'#ff4060':'#c9d1d9'}" font-size="10">${vals[j]}</text>`;
        }
      }
      return bot;
    }

    // ===== build SVG =====
    let s = '';

    // Prepare row data
    const matRows = [
      {vals: modRow0 ? [999, 2, 3] : [1, 2, 3], hlIdx: modRow0 ? 0 : -1, color: IC[0]},
      {vals: (modShallow && showShallow) ? [4, 888, 6] : [4, 5, 6], hlIdx: (modShallow && showShallow) ? 1 : -1, color: IC[1]},
      {vals: [7, 8, 9], hlIdx: -1, color: IC[2]},
    ];

    let y = 30;
    // --- matrix tree ---
    y = drawTree('matrix', '#00e5ff', y, matRows, false);
    y += 6;

    // --- row0 reference ---
    if (showRow0) {
      const ry = y;
      s += box(vX, ry, vW, vH, '#b388ff', 'row0', 12);
      s += hLine(vX + vW, tX, ry + vH / 2, '#b388ff', true);
      s += arrowHd(tX, ry + vH / 2, '#b388ff');
      // dashed connector up to matrix[0]
      s += hLine(tX, iX + 20, ry + vH / 2, '#b388ff', true);
      s += `<text x="${tX + 6}" y="${ry + vH/2 - 5}" fill="#b388ff" font-size="9">= matrix[0] 同一对象!</text>`;
      y = ry + vH + 14;
    }

    // --- shallow tree ---
    if (showShallow) {
      s += `<text x="${vX}" y="${y - 2}" fill="#ffab00" font-size="9">浅拷贝: 新外层, 内层全部共享</text>`;
      y = drawTree('shallow', '#ffab00', y, [
        {vals: modRow0 ? [999, 2, 3] : [1, 2, 3], hlIdx: modRow0 ? 0 : -1},
        {vals: (modShallow && showShallow) ? [4, 888, 6] : [4, 5, 6], hlIdx: (modShallow && showShallow) ? 1 : -1},
        {vals: [7, 8, 9], hlIdx: -1},
      ], true) + 6;
    }

    // --- deep tree ---
    if (showDeep) {
      s += `<text x="${vX}" y="${y - 2}" fill="#00e676" font-size="9">深拷贝: 递归复制, 完全独立</text>`;
      y = drawTree('deep', '#00e676', y, [
        {vals: [1, 2, 3], hlIdx: -1},
        {vals: [4, 5, 6], hlIdx: -1},
        {vals: [7, 8, 9], hlIdx: -1},
      ], false) + 6;
    }

    const H = Math.max(y + 18, 160);
    const msgs = [
      '外层是指针数组 → 三个内层列表对象, 两次跳转访问元素',
      'row0 = matrix[0] → 指向同一个内层列表!',
      'shallow = matrix.copy() → 新外层, 内层全部共享!',
      'deep = copy.deepcopy(matrix) → 递归复制, 完全独立!',
      'row0[0]=999 → matrix[0][0] 也变了! (同一对象)',
      'shallow[1][1]=888 → matrix[1][1] 也变了! (浅拷贝内层共享)',
    ];
    s += `<text x="${(vX + iX + iW) / 2}" y="${H - 6}" text-anchor="middle" fill="#8b949e" font-size="10">${msgs[step]}</text>`;

    const W = iX + iW + 10; // SVG width fits content
    return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${s}</svg>`;
  }
}

// --- 3. 函数参数 ---
function initParamsSteps() {
  return {
    steps: [
      {label:'不可变int', highlight:[1,2,3,4,5],
        svg:()=>`<svg width="560" height="340"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">不可变对象 — 函数内修改不影响外部</text>
          ${boxEl(30,50,90,32,'int:10','#ff4081',14)}<text x="125" y="72" fill="#8b949e" font-size="10">← x</text>
          <text x="75" y="110" text-anchor="middle" fill="#8b949e" font-size="10">↓ 传入函数 (拷贝引用)</text>
          ${boxEl(30,125,90,32,'int:10','#ffab00',14)}<text x="125" y="147" fill="#8b949e" font-size="10">← n</text>
          <text x="280" y="120" text-anchor="middle" fill="#ff4081" font-size="13">n += 100 操作:</text>
          <rect x="180" y="135" width="100" height="32" rx="5" fill="#1e2d45" stroke="#ff4081" stroke-width="1.5" stroke-dasharray="4,2"/>
          <text x="230" y="156" text-anchor="middle" fill="#ff4081" font-size="13">int:110</text>
          <text x="285" y="156" fill="#ff4081" font-size="10">← n (新对象!)</text>
          <text x="230" y="190" text-anchor="middle" fill="#8b949e" font-size="10">x 指向的还是旧的 int:10</text>
          <rect x="60" y="210" width="340" height="48" rx="6" fill="#0d3320" stroke="#00e676" stroke-width="1"/>
          <text x="230" y="230" text-anchor="middle" fill="#00e676" font-size="11">结论: 不可变对象 — n+=100 创建了新int, x 不变</text>
          <text x="230" y="248" text-anchor="middle" fill="#8b949e" font-size="10">类似C++的"传值" — 函数内操作不影响原变量</text></svg>`,
        code:'def modify_int(n):\n    n += 100        # n指向新对象\n    return n\nx = 10\nmodify_int(x)        # x仍是10'},
      {label:'可变list', highlight:[1,2,3,4,5],
        svg:()=>`<svg width="560" height="340"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">可变对象 — 函数内修改影响外部</text>
          ${boxEl(30,50,100,32,'[1,2,3]','#00e676',13)}<text x="135" y="72" fill="#8b949e" font-size="10">← my_list</text>
          <text x="80" y="110" text-anchor="middle" fill="#8b949e" font-size="10">↓ 传入 (同一个对象!)</text>
          ${boxEl(30,125,100,32,'[1,2,3]','#ffab00',13)}<text x="135" y="147" fill="#8b949e" font-size="10">← lst</text>
          <text x="280" y="120" text-anchor="middle" fill="#00e676" font-size="13">lst.append(999):</text>
          <rect x="210" y="135" width="120" height="32" rx="5" fill="#1e2d45" stroke="#00e676" stroke-width="1.5"/>
          <text x="270" y="156" text-anchor="middle" fill="#00e676" font-size="13">[1,2,3,999]</text>
          <text x="270" y="190" text-anchor="middle" fill="#8b949e" font-size="10">my_list 和 lst 指向同一对象 → 都看到变化!</text>
          <rect x="60" y="210" width="440" height="48" rx="6" fill="#0d3320" stroke="#00e676" stroke-width="1"/>
          <text x="280" y="230" text-anchor="middle" fill="#00e676" font-size="11">结论: 可变对象 — .append 原地修改, 外部可见</text>
          <text x="280" y="248" text-anchor="middle" fill="#8b949e" font-size="10">类似C++的"传指针" — 通过引用找到对象原地操作</text></svg>`,
        code:'def modify_list(lst):\n    lst.append(999)  # 原地修改\nmy_list = [1, 2, 3]\nmodify_list(my_list)\n# my_list→[1,2,3,999]'},
      {label:'赋值vs修改', highlight:[1,2,3,4,5],
        svg:()=>`<svg width="560" height="340"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">函数内 = 赋值 — 只改变局部变量</text>
          ${boxEl(20,50,100,32,'[1,2,3]','#ffab00',13)}<text x="125" y="72" fill="#8b949e" font-size="10">← my_list2</text>
          <text x="70" y="110" text-anchor="middle" fill="#8b949e" font-size="10">↓ 传入 (同一对象)</text>
          ${boxEl(20,125,100,32,'[1,2,3]','#ffab00',13)}<text x="125" y="147" fill="#8b949e" font-size="10">← lst (初始)</text>
          <text x="250" y="120" text-anchor="middle" fill="#ff4081" font-size="13">lst = [4,5,6] 操作:</text>
          <rect x="190" y="135" width="100" height="32" rx="5" fill="#1e2d45" stroke="#ff4081" stroke-width="1.5" stroke-dasharray="4,2"/>
          <text x="240" y="156" text-anchor="middle" fill="#ff4081" font-size="13">[4,5,6]</text>
          <text x="295" y="156" fill="#ff4081" font-size="10">← lst (新对象!)</text>
          <text x="240" y="190" text-anchor="middle" fill="#8b949e" font-size="10">my_list2 仍然指向旧的 [1,2,3]</text>
          <rect x="40" y="210" width="480" height="48" rx="6" fill="#332200" stroke="#ffab00" stroke-width="1"/>
          <text x="280" y="230" text-anchor="middle" fill="#ffab00" font-size="11">关键区别: = 赋值 → 局部变量指向新对象; .append() → 原地修改原对象</text>
          <text x="280" y="248" text-anchor="middle" fill="#8b949e" font-size="10">= 永远只改变局部变量名的指向, 不影响外部!</text></svg>`,
        code:'def reassign(lst):\n    lst = [4,5,6]    # 局部!\nmy_list2 = [1, 2, 3]\nreassign(my_list2)\n# my_list2还是[1,2,3]'},
    ], current: 0,
  };
}

// --- 4. 深/浅拷贝 ---
function initCopySteps() {
  return {
    steps: [
      {label:'原始列表', highlight:[1,2],
        svg:()=>renderCopyStep(0),
        code:'import copy\noriginal = [1,2,[10,20,30],3]\nshallow = original.copy()\ndeep = copy.deepcopy(original)\nshallow[2].append(999)'},
      {label:'浅拷贝', highlight:[1,2,3],
        svg:()=>renderCopyStep(1),
        code:'import copy\noriginal = [1,2,[10,20,30],3]\nshallow = original.copy()\ndeep = copy.deepcopy(original)\nshallow[2].append(999)'},
      {label:'深拷贝', highlight:[1,2,3,4],
        svg:()=>renderCopyStep(2),
        code:'import copy\noriginal = [1,2,[10,20,30],3]\nshallow = original.copy()\ndeep = copy.deepcopy(original)\nshallow[2].append(999)'},
      {label:'修改结果', highlight:[1,2,3,4,5],
        svg:()=>renderCopyStep(3),
        code:'import copy\noriginal = [1,2,[10,20,30],3]\nshallow = original.copy()\ndeep = copy.deepcopy(original)\nshallow[2].append(999)\n# original也变! deep不变'},
    ], current: 0,
  };

  function renderCopyStep(step) {
    const W=560, H=360, showShallow=(step>=1), showDeep=(step>=2), modified=(step>=3);
    let s=`<svg width="${W}" height="${H}"><text x="280" y="18" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">深拷贝 vs 浅拷贝 — 嵌套列表内存结构</text>`;

    // original
    s+=`<rect x="10" y="32" width="540" height="70" rx="7" fill="#0d1117" stroke="#00e5ff" stroke-width="1.3"/>
      <text x="25" y="52" fill="#00e5ff" font-size="12" font-weight="700">original</text>`;
    s+=boxEl(105,38,38,22,'1','#c9d1d9',11)+boxEl(148,38,38,22,'2','#c9d1d9',11);
    const nestedV = modified ? '[10,20,30,999]' : '[10,20,30]';
    s+=`<rect x="191" y="38" width="${modified?145:115}" height="22" rx="4" fill="#1e2d45" stroke="#ff4081"/>
      <text x="${191+(modified?72:57)}" y="54" text-anchor="middle" fill="#ff4081" font-size="10">${nestedV} ← 嵌套对象</text>`;
    s+=boxEl(modified?341:311,38,38,22,'3','#c9d1d9',11);

    if (showShallow) {
      s+=`<rect x="10" y="115" width="540" height="70" rx="7" fill="#331100" stroke="#ffab00" stroke-width="1.3"/>
        <text x="25" y="135" fill="#ffab00" font-size="12" font-weight="700">shallow (.copy)</text>`;
      s+=boxEl(145,121,38,22,'1','#c9d1d9',11)+boxEl(188,121,38,22,'2','#c9d1d9',11);
      s+=`<rect x="231" y="121" width="${modified?145:115}" height="22" rx="4" fill="#1e2d45" stroke="#ff4081"/>
        <text x="${231+(modified?72:57)}" y="137" text-anchor="middle" fill="#ff4081" font-size="10">${nestedV} ← 共享!</text>`;
      s+=boxEl(modified?381:351,121,38,22,'3','#c9d1d9',11);
      s+=`<line x1="${248}" y1="100" x2="${248}" y2="113" stroke="#ff4081" stroke-dasharray="4,2" stroke-width="1.5"/>
        <text x="320" y="110" fill="#ff4081" font-size="9">同一嵌套对象!</text>`;
    }

    if (showDeep) {
      const dy=showShallow?198:115;
      s+=`<rect x="10" y="${dy}" width="540" height="70" rx="7" fill="#0d3315" stroke="#00e676" stroke-width="1.3"/>
        <text x="25" y="${dy+20}" fill="#00e676" font-size="12" font-weight="700">deep (copy.deepcopy)</text>`;
      s+=boxEl(190,dy+6,38,22,'1','#c9d1d9',11)+boxEl(233,dy+6,38,22,'2','#c9d1d9',11);
      s+=`<rect x="276" y="${dy+6}" width="115" height="22" rx="4" fill="#1e2d45" stroke="#00e676"/>
        <text x="333" y="${dy+22}" text-anchor="middle" fill="#00e676" font-size="10">[10,20,30] ← 独立!</text>`;
      s+=boxEl(396,dy+6,38,22,'3','#c9d1d9',11);
    }

    s+=`<text x="280" y="${H-15}" text-anchor="middle" fill="#8b949e" font-size="10">${step===0?'原始列表 — 包含嵌套列表 [10,20,30]':step===1?'浅拷贝 — 嵌套对象共享! (同一id)':step===2?'深拷贝 — 嵌套对象独立! (新id)':step===3?'修改shallow → original也变了! deep不变':''}</text>`;
    s+=`</svg>`; return s;
  }
}

// --- 5. 字符串拼接 ---
function initStringSteps() {
  return {
    steps: [
      {label:'+拼接过程', highlight:[1,2,3],
        svg:()=>`<svg width="560" height="320"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">+ 拼接: 每次循环创建新字符串 — O(n²)</text>
          <rect x="30" y="55" width="500" height="56" rx="7" fill="#1e2d45" stroke="#ff4081" stroke-width="1.2"/>
          <text x="50" y="78" fill="#ff4081" font-size="12" font-weight="600">第1次: s = "" + "0" → 分配1字符空间, 复制0字符, 写入1字符</text>
          <text x="50" y="98" fill="#8b949e" font-size="10">第2次: s = "0" + "1" → 分配2字符空间, 复制1字符, 写入1字符</text>
          <rect x="30" y="125" width="500" height="40" rx="7" fill="#1e2d45" stroke="#ff4081" stroke-width="1.2"/>
          <text x="50" y="143" fill="#c9d1d9" font-size="11">第k次: 分配 k 字节, 复制 k-1 字节, 写入 1 字节</text>
          <text x="50" y="158" fill="#8b949e" font-size="10">总共: 1+2+3+...+n = n(n+1)/2 ≈ O(n²) 次内存操作!</text>
          <rect x="30" y="185" width="500" height="56" rx="7" fill="#0d3320" stroke="#00e676" stroke-width="1.2"/>
          <text x="50" y="208" fill="#00e676" font-size="12" font-weight="600">join 拼接: 一次计算总长度, 一次分配 — O(n)</text>
          <text x="50" y="228" fill="#c9d1d9" font-size="11">1. 遍历生成器, 累加总长度 → 2. malloc(总长度) → 3. 一次写入全部</text>
          <rect x="30" y="255" width="500" height="48" rx="7" fill="#0d1117" stroke="#ffab00" stroke-width="1"/>
          <text x="50" y="275" fill="#ffab00" font-size="11">关键: 字符串是不可变对象! 每次 s = s + x 都创建全新字符串对象</text>
          <text x="50" y="293" fill="#8b949e" font-size="10">join 避免了中间临时对象, 直接分配最终大小的缓冲区</text></svg>`,
        code:'s = ""\nfor i in range(n):\n    s += str(i)  # 每次创建新字符串'},
      {label:'join过程', highlight:[1,2],
        svg:()=>`<svg width="560" height="320"><text x="280" y="22" text-anchor="middle" fill="#94a3b8" font-size="12" font-weight="600">join 拼接: 内部一次性分配 — O(n)</text>
          <rect x="30" y="50" width="500" height="50" rx="7" fill="#0d3320" stroke="#00e676" stroke-width="1.2"/>
          <text x="50" y="70" fill="#00e676" font-size="12" font-weight="600">步骤1: 遍历生成器, 累加所有字符串的总长度</text>
          <text x="50" y="88" fill="#c9d1d9" font-size="11">总长度 = len("0")+len("1")+...+len(str(n-1))</text>
          <rect x="30" y="115" width="500" height="40" rx="7" fill="#0d3320" stroke="#00e676" stroke-width="1.2"/>
          <text x="50" y="133" fill="#00e676" font-size="12" font-weight="600">步骤2: 分配 总长度 的字符串缓冲区 (1次malloc)</text>
          <rect x="30" y="170" width="500" height="40" rx="7" fill="#0d3320" stroke="#00e676" stroke-width="1.2"/>
          <text x="50" y="188" fill="#00e676" font-size="12" font-weight="600">步骤3: 逐个拷贝各子串到缓冲区 (连续内存写入)</text>
          <rect x="30" y="230" width="500" height="72" rx="7" fill="#0d1117" stroke="#ffab00" stroke-width="1"/>
          <text x="50" y="252" fill="#ffab00" font-size="11">"".join(list) 性能优势:</text>
          <text x="50" y="272" fill="#c9d1d9" font-size="11">1. 只分配1次内存 2. 不创建临时对象 3. 无需GC回收中间结果</text>
          <text x="50" y="292" fill="#8b949e" font-size="10">n=100000时: + 拼接约5000ms, join约5ms — 快1000倍!</text></svg>`,
        code:'"".join(str(i) for i in range(n))\n# 一次计算总长, 一次分配'},
    ], current: 0,
  };
}




// ===== 初始化所有section的步骤 =====
const SECTIONS = {
  dynamic: { init: initDynamicSteps, svgId: 'dynamic-svg', codeId: 'dynamic-code', navId: 'dynamic-stepnav' },
  listmem: { init: initListmemSteps, svgId: 'listmem-svg', codeId: 'listmem-code', navId: 'listmem-stepnav' },
  '2dlist': { init: init2DListSteps, svgId: '2dlist-svg', codeId: '2dlist-code', navId: '2dlist-stepnav' },
  params: { init: initParamsSteps, svgId: 'params-svg', codeId: 'params-code', navId: 'params-stepnav' },
  copy: { init: initCopySteps, svgId: 'copy-svg', codeId: 'copy-code', navId: 'copy-stepnav' },
  string: { init: initStringSteps, svgId: 'string-chartwrap', codeId: 'string-code', navId: 'string-stepnav', isChart: true },
};

function initSection(name) {
  const cfg = SECTIONS[name];
  if (!cfg) return;
  const data = cfg.init();
  window._stepState = window._stepState || {};
  window._stepState[name] = data;
  if (!cfg.isChart) {
    document.getElementById(cfg.svgId).innerHTML = data.steps[0].svg();
  }
  renderCodePanel(cfg.codeId, data.steps[0].code, data.steps[0].highlight || []);
  renderStepNav(cfg.navId.replace('-stepnav',''), data.steps, 0);
}

function initStringSection() {
  if (window._strChartInit) return;
  window._strChartInit = true;
  initSection('string');
  const ctx = document.getElementById('stringChart').getContext('2d');
  if (stringChartInst) stringChartInst.destroy();
  stringChartInst = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['100', '500', '1k', '5k', '10k', '50k', '100k'],
      datasets: [
        { label: '+ 拼接 (ms)', data: [0,0,0,0,0,0,0], backgroundColor: 'rgba(255,64,129,0.6)', borderColor: '#ff4081', borderWidth: 1 },
        { label: 'join (ms)', data: [0,0,0,0,0,0,0], backgroundColor: 'rgba(0,230,118,0.6)', borderColor: '#00e676', borderWidth: 1 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#94a3b8', font: { size: 11 } } },
        subtitle: { display: true, text: '点击"▶ 运行性能测试"按钮查看实际数据', color: '#8b949e', font: { size: 12 }, padding: { bottom: 8 } }
      },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2d45' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2d45' }, title: { display: true, text: '耗时 (ms)', color: '#94a3b8' }, beginAtZero: true }
      }
    }
  });
}

// ===== 页面加载时初始化第一个 + 懒加载其他 =====
document.addEventListener('DOMContentLoaded', () => {
  initSection('dynamic');
});

// 增强 switchSection 以支持懒初始化
const _origSwitch = switchSection;
switchSection = function(name) {
  _origSwitch(name);
  const secNames = ['dynamic','listmem','2dlist','params','copy','string'];
  if (secNames.includes(name)) {
    setTimeout(() => {
      if (!window._stepState || !window._stepState[name]) initSection(name);
    }, 80);
  }
};

// ===== API 调用函数 =====
async function runDynamicDemo() {
  const out = document.getElementById('dynamic-output');
  out.innerHTML = '<div style="color:var(--text2);">执行中...</div>';
  try {
    const r = await fetch('/api/demo/dynamic_type');
    const data = await r.json();
    out.innerHTML = `<div class="demo-panel"><h3>▶ 实际运行结果 (含真实id值)</h3>
      ${data.steps.map((s,i) => `<div class="demo-step"><div class="demo-step-num">${i+1}</div>
        <div class="demo-step-body"><span class="step-code">${escHtml(s.code)}</span><br>
        <span style="font-size:12px;">→ 类型: <b style="color:var(--purple);">${s.type}</b> | 值: ${s.value} | id: ${s.id}</span><br>
        <span style="font-size:11px;color:var(--text2);">${s.desc}</span></div></div>`).join('')}</div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}

async function runListMemDemo() {
  const out = document.getElementById('listmem-output');
  out.innerHTML = '<div style="color:var(--text2);">执行中...</div>';
  try {
    const r = await fetch('/api/demo/list_memory');
    const d = await r.json();
    out.innerHTML = `<div class="demo-panel"><h3>▶ 实际运行结果</h3>
      <div class="demo-step"><div class="demo-step-num">1</div><div class="demo-step-body">
        <span style="font-size:12px;">a = ${d.a_val} (id:${String(d.a_id).slice(-6)})</span><br>
        <span style="font-size:12px;">b = ${d.b_val} (id:${String(d.b_id).slice(-6)}) <b style="color:var(--pink);">← 同一对象!</b></span><br>
        <span style="font-size:12px;">c = ${d.c_val} (id:${String(d.c_id).slice(-6)}) ← 新列表</span></div></div>
      <div class="demo-step"><div class="demo-step-num">2</div><div class="demo-step-body">
        <span>a is b → ${d.a_is_b} | a is c → ${d.a_is_c} | a == c → ${d.a_eq_c}</span></div></div>
      <div class="demo-step"><div class="demo-step-num">3</div><div class="demo-step-body">
        <b style="color:var(--pink);">b.append(999)后:</b><br>
        a→${d.after_b_append.a_val} <span style="color:var(--pink);">← 也变了!</span><br>
        c→${d.after_b_append.c_val} <span style="color:var(--green);">← 不受影响</span></div></div></div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}

async function run2DListDemo() {
  const out = document.getElementById('2dlist-output');
  out.innerHTML = '<div style="color:var(--text2);">执行中...</div>';
  try {
    const r = await fetch('/api/demo/2d_list');
    const d = await r.json();
    out.innerHTML = `<div class="demo-panel"><h3>▶ 实际运行结果 — 二维列表内存分析</h3>
      <div class="demo-step"><div class="demo-step-num">1</div><div class="demo-step-body">
        <span style="font-size:12px;">matrix = ${d.matrix_val}</span><br>
        <span style="font-size:11px;color:var(--text2);">外层id: ${String(d.matrix_id).slice(-6)}</span></div></div>
      <div class="demo-step"><div class="demo-step-num">2</div><div class="demo-step-body">
        <span>row0 = matrix[0]</span><br>
        <span style="font-size:12px;">row0 id(${String(d.row0_id).slice(-6)}) = matrix[0] id(${String(d.matrix_0_id).slice(-6)})</span><br>
        <span style="color:${d.row0_is_matrix0?'var(--pink)':'var(--green)'};">row0 is matrix[0] → ${d.row0_is_matrix0} (同一对象!)</span></div></div>
      <div class="demo-step"><div class="demo-step-num">3</div><div class="demo-step-body">
        <span>内层列表 id 对比:</span><br>
        <span style="font-size:11px;">matrix内层: [${d.inner_ids_matrix.map(id=>String(id).slice(-6)).join(', ')}]</span><br>
        <span style="font-size:11px;">shallow内层: [${d.inner_ids_shallow.map(id=>String(id).slice(-6)).join(', ')}]</span>
        <span style="color:var(--pink);">← 相同! 共享!</span><br>
        <span style="font-size:11px;">deep内层: [${d.inner_ids_deep.map(id=>String(id).slice(-6)).join(', ')}]</span>
        <span style="color:var(--green);">← 不同! 独立!</span></div></div>
      <div class="demo-step"><div class="demo-step-num">4</div><div class="demo-step-body">
        <b style="color:var(--pink);">row0[0] = 999 后:</b><br>
        <span>matrix → ${d.after_modify.matrix} <span style="color:var(--pink);">← matrix[0]也变了!</span></span><br>
        <span>deep → ${d.after_modify.deep} <span style="color:var(--green);">← 不受影响</span></span></div></div>
      <div class="demo-step"><div class="demo-step-num">5</div><div class="demo-step-body">
        <b style="color:var(--amber);">shallow[1][1] = 888 后:</b><br>
        <span>matrix → ${d.after_shallow_modify.matrix} <span style="color:var(--pink);">← matrix也变了! (浅拷贝内层共享)</span></span></div></div>
      <div style="margin-top:10px;padding:10px;background:#0d1117;border-radius:6px;border-left:3px solid var(--cyan);font-size:13px;line-height:1.7;">
        <b style="color:var(--cyan);">结论:</b> 二维列表 = 指针的数组的数组。matrix.copy() 只复制外层指针数组, 内层列表对象全部共享! 需要 copy.deepcopy() 才能完全独立。
      </div></div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}

async function runParamsDemo() {
  const out = document.getElementById('params-output');
  out.innerHTML = '<div style="color:var(--text2);">执行中...</div>';
  try {
    const r = await fetch('/api/demo/function_params');
    const data = await r.json();
    out.innerHTML = `<div class="demo-panel"><h3>▶ 实际运行结果</h3>
      ${data.results.map((rr,i) => `<div class="demo-step"><div class="demo-step-num">${i+1}</div>
        <div class="demo-step-body"><b style="color:var(--cyan);">${rr.title}</b><br>
        <span style="font-size:12px;">${rr.before} → ${rr.after_func}<br>
        <b style="color:${rr.changed || rr.changed_id ? 'var(--pink)' : 'var(--green)'};">${rr.after}</b></span></div></div>`).join('')}
      <div style="margin-top:10px;padding:10px;background:#0d1117;border-radius:6px;border-left:3px solid var(--cyan);font-size:13px;line-height:1.7;">
        <b style="color:var(--cyan);">结论:</b> Python的参数传递统一是"传对象引用"。不可变对象 → 类似传值; 可变对象 → 类似传指针; = 赋值 → 只改变局部变量。
      </div></div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}

async function runCopyDemo() {
  const out = document.getElementById('copy-output');
  out.innerHTML = '<div style="color:var(--text2);">执行中...</div>';
  try {
    const r = await fetch('/api/demo/copy_demo');
    const d = await r.json();
    out.innerHTML = `<div class="demo-panel"><h3>▶ 实际运行结果</h3>
      <div class="demo-step"><div class="demo-step-num">1</div><div class="demo-step-body">
        <span>original=${d.original} | shallow=${d.shallow} | deep=${d.deep}</span></div></div>
      <div class="demo-step"><div class="demo-step-num">!</div><div class="demo-step-body">
        <span style="color:var(--pink);">共享检测: 浅拷贝内层id(${String(d.shallow_nested_id).slice(-6)}) = 原对象内层id(${String(d.original_nested_id).slice(-6)})!</span></div></div>
      <div class="demo-step"><div class="demo-step-num">3</div><div class="demo-step-body">
        <b style="color:var(--amber);">shallow[2].append(999)后:</b><br>
        <span>original→${d.after_shallow_modify.original} <span style="color:var(--pink);">← 也变了!</span></span><br>
        <span>deep→${d.after_shallow_modify.deep} <span style="color:var(--green);">← 不受影响</span></span></div></div></div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}

let stringChartInst = null;
async function runStringPerfDemo() {
  const out = document.getElementById('string-output');
  out.innerHTML = '<div style="color:var(--text2);">性能测试中, 请稍候...</div>';
  try {
    const r = await fetch('/api/demo/string_perf');
    const data = await r.json();
    const ctx = document.getElementById('stringChart').getContext('2d');
    if (stringChartInst) stringChartInst.destroy();
    stringChartInst = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.sizes.map(s => s >= 1000 ? (s/1000)+'k' : s),
        datasets: [
          { label: '+ 拼接 (ms)', data: data.plus_times, backgroundColor: 'rgba(255,64,129,0.6)', borderColor: '#ff4081', borderWidth: 1 },
          { label: 'join (ms)', data: data.join_times, backgroundColor: 'rgba(0,230,118,0.6)', borderColor: '#00e676', borderWidth: 1 }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#94a3b8', font: { size: 11 } } },
          subtitle: { display: true, text: data.note, color: '#8b949e', font: { size: 11 }, padding: { top: 6 } }
        },
        scales: {
          x: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2d45' } },
          y: { ticks: { color: '#94a3b8' }, grid: { color: '#1e2d45' }, title: { display: true, text: '耗时 (ms)', color: '#94a3b8' }, beginAtZero: true }
        }
      }
    });
    const su = data.sizes.map((s,i) => data.plus_times[i] / Math.max(data.join_times[i], 0.001));
    out.innerHTML = `<div class="demo-panel"><h3>▶ 性能测试结果</h3>
      <table class="info-table">
        <tr><th>n</th>${data.sizes.map(s => `<th>${s>=1000?(s/1000)+'k':s}</th>`).join('')}</tr>
        <tr><td style="color:var(--pink);">+拼接(ms)</td>${data.plus_times.map(t => `<td style="color:var(--pink);">${t}</td>`).join('')}</tr>
        <tr><td style="color:var(--green);">join(ms)</td>${data.join_times.map(t => `<td style="color:var(--green);">${t}</td>`).join('')}</tr>
        <tr><td style="color:var(--amber);">倍数</td>${su.map(s => `<td style="color:var(--amber);">${s>=1000?Math.round(s)+'x':Math.round(s*10)/10+'x'}</td>`).join('')}</tr>
      </table><p style="margin-top:8px;font-size:12px;color:var(--text2);">${data.note}</p></div>`;
  } catch(e) { out.innerHTML = `<div style="color:var(--red);">错误: ${e.message}</div>`; }
}




function escHtml(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

// ===================================================================
// SCI-FI EFFECTS — Starfield Particle System + Cursor Glow
// ===================================================================

// --- Starfield: animated particles with constellation lines ---
(function(){
  const c = document.getElementById('starfield');
  const ctx = c.getContext('2d');
  var W, H, stars = [];
  var STAR_COUNT = 180;

  function resize() { W = c.width = window.innerWidth; H = c.height = window.innerHeight; }
  resize(); window.addEventListener('resize', resize);

  for (var i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: Math.random() * (W || window.innerWidth),
      y: Math.random() * (H || window.innerHeight),
      r: Math.random() * 1.5 + 0.25,
      speed: Math.random() * 0.1 + 0.012,
      opacity: Math.random() * 0.7 + 0.25,
      phase: Math.random() * Math.PI * 2,
      pulseRate: Math.random() * 0.014 + 0.004
    });
  }

  function draw() {
    if (!W || !H) resize();
    ctx.clearRect(0, 0, W, H);

    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      s.phase += s.pulseRate;
      var alpha = s.opacity + Math.sin(s.phase) * 0.22;

      // Star core
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(180,220,255,' + Math.max(0.08, alpha) + ')';
      ctx.fill();

      // Glow halo for larger stars
      if (s.r > 1.0) {
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r * 2.6, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0,240,255,' + Math.max(0.01, alpha * 0.1) + ')';
        ctx.fill();
      }

      // Drift upward
      s.y -= s.speed;
      if (s.y < -8) { s.y = H + 8; s.x = Math.random() * W; }
    }

    // Constellation lines between nearby stars
    for (var i = 0; i < stars.length; i++) {
      for (var j = i + 1; j < stars.length; j++) {
        var dx = stars[i].x - stars[j].x;
        var dy = stars[i].y - stars[j].y;
        var dist = Math.sqrt(dx * dx + dy * dy);
        var connectDist = 105;
        if (dist < connectDist && (stars[i].r > 0.85 || stars[j].r > 0.85)) {
          ctx.beginPath();
          ctx.moveTo(stars[i].x, stars[i].y);
          ctx.lineTo(stars[j].x, stars[j].y);
          ctx.strokeStyle = 'rgba(0,200,255,' + (0.033 * (1 - dist / connectDist)) + ')';
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }

  draw();
})();

// --- Cursor glow: smooth-follow light orb ---
(function(){
  var glow = document.getElementById('cursorGlow');
  var mouseX = -300, mouseY = -300;
  var curX = -300, curY = -300;

  document.addEventListener('mousemove', function(e) {
    mouseX = e.clientX;
    mouseY = e.clientY;
  });

  document.addEventListener('mouseleave', function() {
    glow.style.opacity = '0';
  });

  document.addEventListener('mouseenter', function() {
    glow.style.opacity = '1';
  });

  function animate() {
    curX += (mouseX - curX) * 0.065;
    curY += (mouseY - curY) * 0.065;
    glow.style.left = curX + 'px';
    glow.style.top = curY + 'px';
    requestAnimationFrame(animate);
  }

  animate();
})();

// --- Particle burst on interactive clicks ---
document.addEventListener('click', function(e) {
  var target = e.target.closest('.btn-run, .btn-demo, .nav-tag, .step-nav-btn, .step-dot');
  if (!target) return;
  createBurst(e.clientX, e.clientY);
});

function createBurst(x, y) {
  var container = document.body;
  var count = 14;
  for (var i = 0; i < count; i++) {
    var particle = document.createElement('div');
    var angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.4;
    var velocity = 35 + Math.random() * 45;
    var size = 2.5 + Math.random() * 5;
    var life = 0.5 + Math.random() * 0.4;
    var dx = Math.cos(angle) * velocity;
    var dy = Math.sin(angle) * velocity;

    // Set initial state explicitly
    particle.style.cssText = [
      'position:fixed;z-index:10001;pointer-events:none;',
      'left:' + x + 'px;top:' + y + 'px;',
      'width:' + size + 'px;height:' + size + 'px;',
      'border-radius:50%;',
      'background:hsl(190,100%,70%);',
      'box-shadow:0 0 ' + (size * 2.5) + 'px hsl(190,100%,60%);',
      'transition:all ' + life + 's cubic-bezier(0,0.55,0.45,1);',
      'opacity:1;',
      'transform:translate(0,0) scale(1);'
    ].join('');

    container.appendChild(particle);

    // Force reflow so the browser commits the initial styles above.
    // Without this, the transition has no start frame to interpolate from.
    particle.offsetHeight;

    // Fire the transition — particles explode outward and fade
    particle.style.transform = 'translate(' + dx + 'px,' + dy + 'px) scale(0)';
    particle.style.opacity = '0';

    setTimeout(function() { particle.remove(); }, (life + 0.15) * 1000);
  }
}
</script>
</body>
</html>"""

# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  Python 核心概念可视化教学平台")
    print("  启动地址: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=5000)
