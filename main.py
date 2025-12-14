#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
剪映字幕提取工具
從剪映導出的 draft_content.json 提取字幕並保存為 txt 文件
"""

import json
import sys
import os


def extract_subtitles(filename):
    """從剪映 JSON 檔案中提取字幕"""
    
    # 讀取檔案
    with open(filename, "r", encoding="utf-8") as f:
        raw = f.read()

    data = json.loads(raw)

    # 1. 先把字幕文字按 material.id 收集起來
    #    通常在 data["materials"]["texts"]（有些版本叫 "subtitles"）
    texts_by_id = {}

    materials = data.get("materials", {})
    for key in ["texts", "subtitles"]:  # 兩種常見名稱都試
        for item in materials.get(key, []):
            mid = item.get("id")
            content_str = item.get("content")
            if not mid or not content_str:
                continue
            try:
                inner = json.loads(content_str)
                txt = inner.get("text", "")
                texts_by_id[mid] = txt
            except Exception:
                pass

    # 2. 再從 tracks 裡找出 type 是文字/字幕的軌，拿時間＋對應的 material_id
    entries = []  # (start, end, text)

    for track in data.get("tracks", []):
        # 這裡常見的 type 可能是 "text" / "subtitle" / "sticker"
        ttype = track.get("type", "")
        if ttype not in ["text", "subtitle", "sticker"]:
            continue

        for seg in track.get("segments", []):
            mid = seg.get("material_id")
            if not mid or mid not in texts_by_id:
                continue

            # CapCut 常見時間欄位：target_timerange = {"start":..., "duration":...}
            tr = seg.get("target_timerange", {}) or seg.get("timerange", {})
            start = tr.get("start")
            duration = tr.get("duration")

            if start is None or duration is None:
                continue

            end = start + duration
            text = texts_by_id[mid]
            entries.append((start, end, text))

    # 3. 依時間排序
    entries.sort(key=lambda x: x[0])

    return entries


def us_to_time(t_us):
    """將微秒轉換為時間格式 HH:MM:SS"""
    t = t_us / 1_000_000.0  # 如果出來時間怪異，改成 / 1000 試試（表示是毫秒）
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_output(entries, include_time=True):
    """格式化字幕輸出"""
    lines = []
    
    for idx, (st, ed, txt) in enumerate(entries, start=1):
        if include_time:
            lines.append(f"[{us_to_time(st)} --> {us_to_time(ed)}]")
        lines.append(txt)
        lines.append("")  # 空行
    
    return "\n".join(lines)


def main():
    """主程序"""
    print("=" * 50)
    print("剪映字幕提取工具")
    print("=" * 50)
    
    # 獲取檔案名稱
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = input("\n請輸入剪映 JSON 檔案路徑: ").strip()
    
    # 檢查檔案是否存在
    if not os.path.exists(filename):
        print(f"❌ 錯誤：找不到檔案 '{filename}'")
        return
    
    print(f"\n📁 已讀取檔案: {filename}")
    
    try:
        # 提取字幕
        entries = extract_subtitles(filename)
        
        if not entries:
            print("\n⚠️ 未找到任何字幕內容")
            return
        
        print(f"✅ 成功提取 {len(entries)} 條字幕\n")
        
        # 打印字幕內容
        print("=" * 50)
        print("字幕內容：")
        print("=" * 50)
        
        output_text = format_output(entries, include_time=True)
        print(output_text)
        
        # 保存為 txt 檔案
        output_filename = "output.txt"
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output_text)
        
        print("=" * 50)
        print(f"✅ 字幕已保存到: {output_filename}")
        print("=" * 50)
        
    except json.JSONDecodeError:
        print("\n❌ 錯誤：檔案格式不正確，請確認是剪映導出的 JSON 檔案")
    except Exception as e:
        print(f"\n❌ 錯誤：{str(e)}")


if __name__ == "__main__":
    main()
