# PDF 论文翻译工具

这是一个用于将英文 PDF 论文翻译成中文的工具。它使用 OpenAI 的 API 进行翻译，并保留原始 PDF 的格式和布局。

## 功能

- 自动识别和翻译 PDF 中的文本内容
- 保留原始 PDF 的格式、图表和页面布局
- 多线程翻译以提高效率
- 智能判断是否需要翻译特定内容（如表格数据、公式等）

## 安装

1. 确保你的 Python 版本大于 3.10。
   
2. 克隆此仓库：
```bash
git clone https://github.com/lln556/pdf-translation-tool.git
cd pdf-translation-tool
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 在项目根目录创建 `.env` 文件，并添加你的 OpenAI API 密钥：
```bash
OPENAI_APIKEY=your_openai_api_key
```

## 使用方法

1. 将要翻译的 PDF 文件放在项目目录中。

2. 修改 `main.py` 文件中的 `source_file_path` 变量，指向你的 PDF 文件。

3. 指定字体路径 `font_path`, 默认为宋体。

4. 运行 `main.py` 文件：
```bash
python main.py
```

5. 翻译后的 PDF 将保存在原文件同目录下，文件名为原文件名加上 "_zh" 后缀。

## 许可证

本项目基于 AGPL-3.0 许可证发布。详细信息请参见 LICENSE 文件。

## 致谢

感谢 [PyMuPDF](https://github.com/pymupdf/PyMuPDF) 团队提供的强大库，使得 PDF 文件的处理和操作变得更加简单和高效。

