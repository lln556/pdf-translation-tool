# -*- coding:utf-8 -*-
import pymupdf
from translate import translate_multi, whether_to_trans_multi
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import backoff

def process_block(block):
    if block['type'] == 0:  # 文本类型
        text = ""
        font_size = []
        for line in block['lines']:
            for span in line['spans']:
                text += span['text']
                font_size.append(span['size'])

        # 添加更多的检查
        if text is None or text.strip() == '' or len(text) < 2:
            return None

        x1, y1, x2, y2 = block['bbox']
        rect = pymupdf.Rect(x1, y1, x2, y2)

        # 检查矩形的有效性
        if rect.is_empty or rect.is_infinite:
            return None

        return {
            "text": text,
            "font_size": font_size,
            "rect": rect,
        }
    return None

@backoff.on_exception(backoff.expo,
                      Exception,
                      max_tries=5,
                      max_time=300)
def translate_text(text):
    trans_flag = whether_to_trans_multi([text], "openai")[0]
    if trans_flag is not None:
        trans_flag = trans_flag.strip().lower()
        if trans_flag in ['true', '1', 'yes']:
            zh = translate_multi([text], "openai")[0]
            if zh is not None:
                print(f"翻译结果: {zh}")  # 打印前翻译结果
                return zh
    return None

def main(pdf_path, output_path,font_path="C:\\Windows\\Fonts\\simsun.ttc"):
    doc = pymupdf.open(pdf_path)
    font = pymupdf.Font(fontfile=font_path)
    
    total_pages = len(doc)
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        for page_num in range(total_pages):
            page = doc[page_num]
            print(f"处理第 {page_num + 1}/{total_pages} 页")
            tw = pymupdf.TextWriter(page.rect)
            dct = page.get_text("dict")
            
            blocks_to_translate = []
            for block in dct['blocks']:
                block_info = process_block(block)
                if block_info:
                    blocks_to_translate.append(block_info)
            
            print(f"第 {page_num + 1} 页有 {len(blocks_to_translate)} 个文本块需要处理")
            
            # 并行翻译所有块
            futures = {executor.submit(translate_text, block["text"]): i for i, block in enumerate(blocks_to_translate)}
            translations = [None] * len(blocks_to_translate)
            for future in as_completed(futures):
                try:
                    result = future.result()
                    index = futures[future]
                    translations[index] = result
                except Exception as e:
                    print(f"翻译过程中发生错误: {e}")
            
            print(f"第 {page_num + 1} 页实际翻译了 {sum(1 for t in translations if t is not None)} 个文本块")
            
            # 在主线程中处理每个块的覆写
            for block, translation in zip(blocks_to_translate, translations):
                if translation:
                    formatted_zh = '\n'.join([' '.join(line.split()) for line in translation.splitlines()])
                    # formatted_zh = formatted_zh.replace('\t', '')
                    
                    rect = block["rect"]
                    fontsize = sum(block["font_size"]) / len(block["font_size"])
                    
                    # 尝试填充文本，如果失败则逐步缩小字体大小
                    success = False
                    while fontsize > 1 and not success:  # 设置最小字体大小为1
                        try:
                            tw.fill_textbox(rect, formatted_zh, pos=None, font=font, 
                                            fontsize=fontsize, align=0, 
                                            right_to_left=False, warn=None, small_caps=0)
                            success = True
                        except ValueError:
                            fontsize *= 0.9  # 每次减少10%的字体大小
                    
                    if not success:
                        print(f"无法适应文本框，跳过此块: {block['text']}")
                        continue

                    page.add_redact_annot(rect)
                else:
                    print(f"跳过未翻译的块: {block['text']}")
            
            # 在处理完所有块后，一次性应用所有修改
            page.apply_redactions()
            tw.write_text(page)
            

    # 保存处理后的PDF
    doc.save(output_path)
    doc.close()
    print("处理完成！")

if __name__ == "__main__":
    source_file_path = r"C:\Users\94375\Zotero\storage\3EUGGQI6\Hu 等 - 2024 - AUITestAgent Automatic Requirements Oriented GUI Function Testing.pdf"
    font_path = "C:\\Windows\\Fonts\\simsun.ttc"
    out_put_path = ''.join(source_file_path.split(".")[0:-1]) + "_zh." + source_file_path.split(".")[-1]
    main(source_file_path, out_put_path, font_path)
