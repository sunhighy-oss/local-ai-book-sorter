#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, re, shutil, json, logging, requests, time
from pathlib import Path
from pypdf import PdfReader
from ebooklib import epub
from bs4 import BeautifulSoup

# ================= 配置区域 =================
SOURCE_FOLDER = "./input_pdfs"
TARGET_ROOT = "./sorted_library_clc"
LLAMA_SERVER_URL = "http://localhost:8080"
DRY_RUN = False
AI_TIMEOUT = 60

# ================= 中图法定义 =================
CLASS_NAMES = {"A": "A_马克思主义", "B": "B_哲学宗教", "C": "C_社会科学总论", "D": "D_政治法律", "E": "E_军事", "F": "F_经济", "G": "G_文化教育", "H": "H_语言文字", "I": "I_文学", "J": "J_艺术", "K": "K_历史地理", "N": "N_自然科学总论", "O": "O_数理科学", "P": "P_天文地球", "Q": "Q_生物科学", "R": "R_医药卫生", "S": "S_农业科学", "T": "T_工业技术", "U": "U_交通运输", "V": "V_航空航天", "X": "X_环境安全", "Z": "Z_综合性图书"}
SUB_CLASS_NAMES = {"R1": "R1_预防医学", "R2": "R2_中医", "R3": "R3_基础医学", "R4": "R4_临床医学", "R5": "R5_内科学", "R6": "R6_外科学", "R7": "R7_专科医学", "R9": "R9_药学", "D9": "D9_法律", "D0": "D0_政治理论", "F0": "F0_经济理论", "F1": "F1_世界经济", "F2": "F2_经济管理", "F8": "F8_财政金融", "B0": "B0_哲学理论", "B2": "B2_中国哲学", "B5": "B5_西方哲学", "B84": "B84_心理学", "B9": "B9_宗教", "K2": "K2_中国史", "K3": "K3_亚洲史", "K5": "K5_欧洲史", "K7": "K7_美洲史", "K8": "K8_传记", "K9": "K9_地理", "O1": "O1_数学", "O3": "O3_力学", "O4": "O4_物理学", "O6": "O6_化学", "TP": "TP_计算机技术", "TN": "TN_电子技术", "TM": "TM_电工技术", "TU": "TU_建筑科学", "G4": "G4_教育", "G8": "G8_体育", "H1": "H1_汉语", "H3": "H3_外语", "I2": "I2_中国文学", "I3": "I3_亚洲文学", "I5": "I5_欧洲文学", "I7": "I7_美洲文学", "I24": "I24_小说", "I26": "I26_散文", "I27": "I27_诗歌", "J0": "J0_艺术理论", "J2": "J2_绘画", "J6": "J6_音乐", "J9": "J9_影视", "C9": "C9_社会学", "N": "N_自然科学", "Q": "Q_生物科学", "X": "X_环境科学", "Z": "Z_综合图书"}

KEYWORD_RULES = {
    "K": {"K8": ["传记", "回忆录", "自传"], "K2": ["中国史", "清代", "明代"], "K": ["历史", "战争", "古代"]},
    "I": {"I24": ["小说", "故事"], "I26": ["散文", "随笔"], "I": ["文学", "名著"]},
    "R": {"R": ["医学", "临床", "疾病", "健康"]},
    "F": {"F": ["经济", "金融", "银行", "投资"]},
    "B": {"B84": ["心理", "思维", "意识"], "B": ["哲学", "宗教", "思想"]},
    "T": {"TP": ["计算机", "软件", "编程", "AI", "Python"], "T": ["技术", "工程"]},
    "Z": {"Z": ["综合", "丛书", "套装"]}
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[logging.FileHandler("clc_classify.log", encoding='utf-8'), logging.StreamHandler()])

def extract_pdf_text(file_path, max_chars=1500):
    try:
        reader = PdfReader(str(file_path))
        if reader.is_encrypted: return "", 'encrypted', ""
        text = ""
        for i in range(min(3, len(reader.pages))):
            text += reader.pages[i].extract_text() or ""
        if len(text.strip()) < 100: return "", 'scanned', ""
        valid_ratio = sum(1 for c in text[:500] if '\u4e00' <= c <= '\u9fff' or c.isalnum()) / 500
        if valid_ratio < 0.5: return "", 'garbled', ""
        return text[:max_chars], 'ok', text[:100]
    except Exception: return "", 'error', ""

def extract_epub_text(file_path, max_chars=1500):
    try:
        book = epub.read_epub(str(file_path), {'ignore_ncx': True})
        text = ""
        for item in book.get_items():
            if hasattr(item, 'get_type') and item.get_type() == epub.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8', errors='ignore')
                text += BeautifulSoup(content, 'lxml').get_text(separator=' ', strip=True) + "\n"
            if len(text) >= max_chars: break
        if len(text.strip()) < 100: return "", 'scanned', ""
        return text[:max_chars], 'ok', text[:100]
    except Exception: return "", 'error', ""

def keyword_classify(text_info):
    text_lower = text_info.lower()
    for main_class, subs in KEYWORD_RULES.items():
        for sub_code, keywords in subs.items():
            if any(kw.lower() in text_lower for kw in keywords):
                return sub_code
    return None

def classify_with_llama(content, title):
    prompt = f"你是图书分类专家。根据书名和内容，返回中图法分类号(2-3位字母数字，如TP311, K248, I247)。只返回JSON: {{\"code\": \"分类号\", \"reason\": \"理由\"}}\n书名:{title}\n内容:{content[:500]}"
    try:
        payload = {"prompt": prompt, "n_predict": 100, "temperature": 0.1, "stop": ["user"], "stream": False}
        response = requests.post(f"{LLAMA_SERVER_URL}/completion", json=payload, timeout=AI_TIMEOUT)
        output = response.json().get("content", "").strip().replace('```json', '').replace('```', '')
        start, end = output.find('{'), output.rfind('}')
        if start >= 0 and end > start:
            res = json.loads(output[start:end+1])
            code = ''.join(c for c in res.get("code", "").upper() if c.isalnum())
            if code and code[0].isalpha(): return code
    except Exception: pass
    return None

def get_folder_path(code):
    main_class = code[0]
    main_name = CLASS_NAMES.get(main_class, f"{main_class}_未分类")
    if len(code) >= 2 and code[:2] in SUB_CLASS_NAMES:
        return f"{main_name}/{SUB_CLASS_NAMES[code[:2]]}"
    return f"{main_name}/{main_name}"

def organize_pdfs():
    source_path = Path(SOURCE_FOLDER).resolve()
    target_root = Path(TARGET_ROOT).resolve()
    if not source_path.exists():
        logging.error(f"❌ 源文件夹不存在：{source_path}")
        return

    # 创建目录
    target_root.mkdir(parents=True, exist_ok=True)
    for name in CLASS_NAMES.values(): (target_root / name).mkdir(parents=True, exist_ok=True)
    for sub_code, sub_name in SUB_CLASS_NAMES.items():
        main_name = CLASS_NAMES.get(sub_code[0], f"{sub_code[0]}_未分类")
        (target_root / main_name / sub_name).mkdir(parents=True, exist_ok=True)
    (target_root / "Z_综合性图书/未分类").mkdir(parents=True, exist_ok=True)

    all_files = [f for f in source_path.rglob("*") if f.suffix.lower() in ['.pdf', '.epub']]
    logging.info(f"📚 发现 {len(all_files)} 个文件待处理")

    for i, file_path in enumerate(all_files):
        logging.info(f"[{i+1}/{len(all_files)}] {file_path.name}")
        ext = file_path.suffix.lower()
        content, status, preview = extract_pdf_text(file_path) if ext == '.pdf' else extract_epub_text(file_path)
        
        if status != 'ok':
            target_dir = target_root / f"Z_综合性图书/未分类/{status}"
            target_dir.mkdir(parents=True, exist_ok=True)
            if not DRY_RUN: shutil.move(str(file_path), str(target_dir / file_path.name))
            logging.info(f"  → 移动到未分类/{status}")
            continue

        title = file_path.stem
        code = classify_with_llama(content, title)
        if not code:
            code = keyword_classify(content + " " + title)
        if not code: code = "Z"

        folder_path = get_folder_path(code)
        target_dir = target_root / folder_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        if not DRY_RUN: shutil.move(str(file_path), str(target_dir / file_path.name))
        logging.info(f"  → 已移动到：{folder_path}")

if __name__ == "__main__":
    organize_pdfs()
