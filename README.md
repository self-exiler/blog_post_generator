# 博文生成工具

一个基于PySide6的GUI工具，用于生成和编辑符合chirpy-starter模板格式的Jekyll博文文件。

## 功能特点

- 📝 自动生成符合chirpy-starter模板格式的markdown文件
- 📂 打开并编辑已生成的博文文件，保留正文内容
- 🗂️ 支持设置博文分类（主分类和子分类）
- 🏷️ 支持多个标签，使用空格分隔（自动转换为英文逗号）
- 👤 自动从 `_data/authors.yml`加载作者列表
- 💾 记住上次使用的博客工程路径
- 🚀 一键在VSCode中打开博客工程和生成的文件
- 📋 提供操作状态日志
- 🤖 **AI关键词提炼**：使用OpenAI API从正文内容中自动提取5个关键词
- 📄 **纯文本粘贴**：描述字段支持纯文本粘贴，避免格式混乱

## 系统要求

- Python 3.8+
- PySide6
- VSCode（可选，用于"用VSCode打开"功能）

## 安装步骤

1. 克隆或下载此项目到本地
2. 安装依赖：
   ```
   pip install -r requirements.txt
   ```
3. 运行程序：
   ```
   python main.py
   ```

## 使用方法

1. **设置博客工程路径**：

   - 点击"浏览"按钮选择您的Jekyll博客工程根目录
   - 路径会自动保存，下次打开程序时会自动加载

2. **配置OpenAI API（可选）**：

   - 编辑 `config.ini`文件，在 `[OpenAI]` 部分添加以下配置：
     ```
     [OpenAI]
     api_key = your_openai_api_key
     api_base = https://api.openai.com/v1
     model = gpt-3.5-turbo
     ```
   - `api_key`：您的OpenAI API密钥（必需）
   - `api_base`：API基础地址（可选，默认为OpenAI官方地址）
   - `model`：使用的模型（可选，默认为gpt-3.5-turbo）

3. **创建新博文**：

   - 日期和时间：默认为当前时间，可手动调整
   - 标题：必填，将用于生成文件名
   - 分类：可选，可设置主分类和子分类
   - 标签：可选，多个标签使用空格分隔
   - 作者：可选，从 `_data/authors.yml`自动加载
   - 描述：可选，可填写博文描述（支持纯文本粘贴）
   - **AI关键词提炼**：
     - 点击"浏览"按钮选择包含正文内容的文本文件
     - 点击"AI提炼关键词"按钮，程序将调用OpenAI API分析正文内容
     - 自动提取5个最相关的关键词并显示在标签字段中
     - 您可以在此基础上修改或添加更多标签
   - 点击"生成博文"按钮创建新博文

4. **编辑已有博文**：

   - 点击"打开已有博文"按钮
   - 从`_posts`目录中选择要编辑的markdown文件
   - 程序会自动解析文件并将元数据填充到表单中
   - 修改需要更新的信息（标题、日期、分类等）
   - 点击"生成博文"按钮保存更改（正文内容将保持不变）

5. **文件管理**：

   - 博文将保存在 `工程路径/_posts/`目录下
   - 文件名格式为：`年-月-日-标题.md`
   - 生成或编辑博文后，可点击"用VSCode打开"按钮
   - 将在VSCode中打开博客工程文件夹和当前处理的博文文件

## 配置文件

程序使用 `config.ini`文件保存配置，主要包括：

- 博客工程路径
- OpenAI API配置（可选）

## 文件结构

```
github博文生成工具/
├── blog_post_generator.ui      # UI界面定义文件
├── blog_post_generator_ui.py   # 编译后的UI文件
├── main.py                     # 主程序文件
├── config.ini                  # 配置文件
├── requirements.txt            # 依赖列表
└── README.md                   # 说明文档
```

## 注意事项

1. 如果修改了 `blog_post_generator.ui`文件，需要重新编译为Python文件：

   ```bash
   pyside6-uic blog_post_generator.ui -o blog_post_generator_ui.py
   ```
   
   或者在Windows PowerShell中运行：
   ```powershell
   cd "项目路径"; pyside6-uic blog_post_generator.ui -o blog_post_generator_ui.py
   ```

2. 作者列表从博客工程的 `_data/authors.yml`文件自动加载，请确保该文件存在且格式正确。
3. 生成的博文文件符合Jekyll的chirpy-starter模板格式，包含必要的YAML头部信息。
4. **编辑已有博文时**：
   - 程序会保留原文的正文内容不变
   - 只有front matter中的元数据会被更新
   - 如果文件没有front matter，整个文件将被视为正文内容
5. 文件名格式遵循Jekyll标准：`YYYY-MM-DD-title.md`，其中标题部分会自动移除特殊字符并替换为连字符。
6. **AI关键词提炼功能**：
   - 需要配置有效的OpenAI API密钥才能使用
   - 建议使用UTF-8编码的文本文件作为正文来源
   - 提取的关键词会显示在标签字段中，您可以在此基础上进一步编辑
   - 该功能为可选功能，不配置OpenAI API时仍可使用其他所有功能

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。