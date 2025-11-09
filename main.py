import sys
import re
import subprocess
import configparser
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, Tuple
import yaml
import requests
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import QDate, QTime, Slot
from blog_post_generator_ui import Ui_BlogPostGenerator

# 常量
CONFIG_FILE_NAME = "config.ini"
AUTHORS_FILE_PATH = "_data/authors.yml"
POSTS_DIR_PATH = "_posts"

# 匹配 --- 分隔符 (在行首)
FRONT_MATTER_DELIMITER = re.compile(r'^---\s*$', re.MULTILINE)

class BlogPostGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.ui = Ui_BlogPostGenerator()
        self.ui.setupUi(self)
        
        self.last_generated_file: Optional[Path] = None
        self.current_opened_file: Optional[Path] = None  # 当前打开的文件
        self.original_content: Optional[str] = None  # 原始文件内容
        self.config_file = Path(__file__).parent / CONFIG_FILE_NAME
        
        self.init_ui_state()
        self.connect_signals()
        
        self.load_config()
        self.load_authors()
        
        self.log("博文生成工具已启动")
    
    def init_ui_state(self) -> None:
        """初始化UI默认状态"""
        self.ui.dateEdit.setDate(QDate.currentDate())
        self.ui.timeEdit.setTime(QTime.currentTime())
        self.ui.openVSCodeButton.setEnabled(False) # 默认禁用
        self.ui.generateButton.setText("生成博文")

    def connect_signals(self) -> None:
        """连接所有信号和槽"""
        self.ui.browseButton.clicked.connect(self.browse_project_path)
        self.ui.openPostButton.clicked.connect(self.open_existing_post)
        self.ui.generateButton.clicked.connect(self.generate_blog_post)
        self.ui.clearButton.clicked.connect(self.clear_form)
        self.ui.openVSCodeButton.clicked.connect(self.open_in_vscode)
        self.ui.browseContentButton.clicked.connect(self.browse_content_file)
        self.ui.extractKeywordsButton.clicked.connect(self.extract_keywords)
    
    def closeEvent(self, event) -> None:
        """窗口关闭事件，保存配置"""
        self.save_config()
        event.accept()
    
    @Slot(str)
    def log(self, message: str) -> None:
        """在日志窗口记录信息"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.ui.logTextEdit.append(f"[{timestamp}] {message}")
    
    def _get_config_parser(self) -> configparser.ConfigParser:
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file, encoding='utf-8')
        return config

    def load_config(self) -> None:
        try:
            config = self._get_config_parser()
            blog_project_path = config.get('Settings', 'blog_project_path', fallback='')
            if blog_project_path:
                self.ui.projectPathEdit.setText(blog_project_path)
                self.log(f"已加载配置中的博客工程路径: {blog_project_path}")
        except configparser.Error as e:
            self.log(f"加载配置文件失败: {str(e)}")
    
    def save_config(self) -> None:
        try:
            config = self._get_config_parser()
            if not config.has_section('Settings'):
                config.add_section('Settings')
            
            blog_project_path = self.ui.projectPathEdit.text().strip()
            if blog_project_path:
                config.set('Settings', 'blog_project_path', blog_project_path)
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    config.write(f)
                self.log("配置已保存")
        except configparser.Error as e:
            self.log(f"保存配置文件失败: {str(e)}")
    
    @Slot()
    def browse_content_file(self) -> None:
        """浏览并选择MD文件作为正文来源"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择MD文件作为正文来源", "", "Markdown文件 (*.md);;所有文件 (*.*)"
        )
        
        if file_path:
            self.ui.contentFilePathEdit.setText(file_path)
            self.log(f"已选择正文来源文件: {file_path}")
    
    def read_content_file(self, file_path: str) -> str:
        """读取MD文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except IOError as e:
            self.log(f"读取正文文件失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"读取正文文件失败: {str(e)}")
            return ""
        except Exception as e:
            self.log(f"读取正文文件时发生未知错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"读取正文文件时发生未知错误: {str(e)}")
            return ""
    
    @Slot()
    def browse_project_path(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "选择博文工程路径")
        if directory:
            self.ui.projectPathEdit.setText(directory)
            self.log(f"已选择博文工程路径: {directory}")
            self.save_config()
            self.load_authors()
    
    @Slot()
    def load_authors(self) -> None:
        project_path = self.ui.projectPathEdit.text().strip()
        self.ui.authorComboBox.clear()
        self.ui.authorComboBox.addItem("")
        
        if not project_path:
            return
            
        authors_file = Path(project_path) / AUTHORS_FILE_PATH
        if not authors_file.exists():
            self.log(f"未找到作者文件: {authors_file}")
            return

        try:
            with open(authors_file, 'r', encoding='utf-8') as f:
                authors_data = yaml.safe_load(f)
                
            if isinstance(authors_data, dict):
                author_names = list(authors_data.keys())
                self.ui.authorComboBox.addItems(author_names)
                self.log(f"已加载 {len(author_names)} 个作者")
            else:
                self.log(f"作者文件格式不正确，期望是一个字典，但得到了 {type(authors_data)}")
                    
        except yaml.YAMLError as e:
            self.log(f"加载作者列表失败 (YAML 解析错误): {str(e)}")
        except Exception as e:
            self.log(f"加载作者列表失败 (未知错误): {str(e)}")

    def _parse_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """(保留) 使用re.split解析markdown文件的front matter"""
        front_matter = {}
        body_content = ""
        
        parts = FRONT_MATTER_DELIMITER.split(content, maxsplit=2)
        
        if len(parts) == 3 and parts[0].strip() == '':
            try:
                front_matter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError as e:
                self.log(f"解析front matter失败: {str(e)}")
                return {}, content
            
            body_content = parts[2].lstrip('\n') # 移除YAML和正文之间的多余换行
        else:
            body_content = content
        
        return front_matter, body_content

    @Slot()
    def open_existing_post(self) -> None:
        """(保留) 打开已有的博文文件进行编辑"""
        project_path = self.ui.projectPathEdit.text().strip()
        
        if not project_path:
            QMessageBox.warning(self, "警告", "请先指定博文工程路径")
            return
            
        posts_dir = Path(project_path) / POSTS_DIR_PATH
        if not posts_dir.exists():
            QMessageBox.warning(self, "警告", f"博文目录不存在: {posts_dir}")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要编辑的博文文件", str(posts_dir), "Markdown文件 (*.md)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            front_matter, body_content = self._parse_front_matter(content)
            
            self.original_content = content
            self.current_opened_file = Path(file_path)
            self.last_generated_file = self.current_opened_file
            
            self._populate_form_from_front_matter(front_matter)
            
            self.ui.openVSCodeButton.setEnabled(True)
            self.ui.generateButton.setText("更新博文")
            
            self.log(f"已打开博文: {file_path}")
            
        except IOError as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            self.log(f"读取文件失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")
            self.log(f"打开文件失败: {str(e)}")
    
    def _clear_ui_fields_only(self) -> None:
        """(新) 仅清空UI表单字段，不重置状态"""
        self.ui.titleEdit.clear()
        self.ui.mainCategoryEdit.clear()
        self.ui.subCategoryEdit.clear()
        self.ui.tagsEdit.clear()
        self.ui.authorComboBox.setCurrentIndex(0)
        self.ui.descriptionEdit.clear()
        self.ui.contentFilePathEdit.clear()
        
        self.ui.dateEdit.setDate(QDate.currentDate())
        self.ui.timeEdit.setTime(QTime.currentTime())

    def _populate_form_from_front_matter(self, front_matter: Dict[str, Any]) -> None:
        """(保留) 根据front matter填充表单"""
        # (修复) 不再调用 clear_form()，而是调用 _clear_ui_fields_only()
        self._clear_ui_fields_only() 
        
        # 重置按钮文本
        self.ui.generateButton.setText("更新博文")

        self.ui.titleEdit.setText(front_matter.get('title', ''))
        
        date_str = front_matter.get('date', '')
        if isinstance(date_str, datetime):
             self.ui.dateEdit.setDate(QDate(date_str.year, date_str.month, date_str.day))
             self.ui.timeEdit.setTime(QTime(date_str.hour, date_str.minute, date_str.second))
        elif isinstance(date_str, str):
            try:
                parts = date_str.split(' ')
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1].split('+')[0]
                    
                    date_obj = QDate.fromString(date_part, "yyyy-M-d")
                    if date_obj.isValid(): self.ui.dateEdit.setDate(date_obj)
                    
                    time_obj = QTime.fromString(time_part, "HH:mm:ss")
                    if time_obj.isValid(): self.ui.timeEdit.setTime(time_obj)
            except Exception as e:
                self.log(f"解析日期时间字符串失败: {str(e)}")
        
        categories_list = front_matter.get('categories', [])
        if isinstance(categories_list, list):
            if len(categories_list) >= 1:
                self.ui.mainCategoryEdit.setText(categories_list[0])
            if len(categories_list) >= 2:
                self.ui.subCategoryEdit.setText(categories_list[1])

        tags_list = front_matter.get('tags', [])
        if isinstance(tags_list, list):
            # 将列表转换为空格分隔的字符串
            self.ui.tagsEdit.setText(' '.join(tags_list))
        
        author = front_matter.get('author', '')
        index = self.ui.authorComboBox.findText(author)
        if index >= 0:
            self.ui.authorComboBox.setCurrentIndex(index)
        else:
            self.ui.authorComboBox.setCurrentText(author)
        
        self.ui.descriptionEdit.setPlainText(front_matter.get('description', ''))

    @Slot()
    def generate_blog_post(self) -> None:
        """(已修复) 生成博文文件或更新已有文件"""
        project_path = self.ui.projectPathEdit.text().strip()
        title = self.ui.titleEdit.text().strip()
        
        if not project_path:
            QMessageBox.warning(self, "警告", "请指定博文工程路径")
            return
        if not title:
            QMessageBox.warning(self, "警告", "请输入博文标题")
            return
        
        # 1. 准备数据
        date = self.ui.dateEdit.date().toString("yyyy-M-d")
        time = self.ui.timeEdit.time().toString("HH:mm:ss")
        main_category = self.ui.mainCategoryEdit.text().strip()
        sub_category = self.ui.subCategoryEdit.text().strip()
        tags_raw = self.ui.tagsEdit.text().strip()
        author = self.ui.authorComboBox.currentText().strip()
        description = self.ui.descriptionEdit.toPlainText().strip()
        content_file_path = self.ui.contentFilePathEdit.text().strip()
        
        # 读取正文内容（如果指定了文件）
        body_content = ""
        if content_file_path:
            body_content = self.read_content_file(content_file_path)
            if not body_content:  # 如果读取失败，继续使用空内容
                body_content = ""
        
        # 2. (已修复) 严格按照 prompt.md 格式构建 front_matter 字符串
        
        front_matter_content = "---\n"
        
        # 标题 (必需)
        front_matter_content += f"title: {title}\n\n"
        
        # 日期 (必需)
        front_matter_content += f"date: {date} {time} +0800\n\n"
        
        # 分类 (可选)
        categories_str = ""
        if main_category:
            categories_str = main_category
            if sub_category:
                categories_str += f",{sub_category}" # 格式: [A,B]
        if categories_str:
            front_matter_content += f"categories: [{categories_str}]\n\n"
            
        # 标签 (可选)
        # UI中用空格分隔，输出为 [A,B,C] 格式
        tags_list = [tag.strip() for tag in tags_raw.split(' ') if tag.strip()]
        if tags_list:
            tags_str = ",".join(tags_list) # 格式: [A,B,C]
            front_matter_content += f"tags: [{tags_str}]\n\n"

        # 作者 (可选)
        if author:
            front_matter_content += f"author: {author}\n\n"
        
        # 描述 (可选)
        if description:
            # prompt.md 中的示例是多行
            # 我们使用 | (literal block) 来保留换行符
            if '\n' in description:
                front_matter_content += "description: |-\n" # |- 保留换行但去除末尾换行
                for line in description.splitlines():
                    front_matter_content += f"  {line}\n"
            else:
                front_matter_content += f"description: {description}\n"
            front_matter_content += "\n" # 额外加一个换行
        
        front_matter_content += "---\n"
        
        # --- 修复结束 ---

        
        # 3. 确定文件路径和内容
        is_editing = self.current_opened_file is not None
        
        if is_editing:
            # 编辑模式
            file_path = self.current_opened_file
            _, existing_body_content = self._parse_front_matter(self.original_content)
            
            # 如果有指定正文文件，使用文件内容；否则保留原有正文
            if body_content:
                final_body_content = body_content
            else:
                final_body_content = existing_body_content
                
            content = front_matter_content + "\n" + final_body_content # 确保front matter和正文间有换行
            action = "更新"
        else:
            # 新建模式
            safe_title = re.sub(r'[^\w\u4e00-\u9fa5\s-]', '', title)
            safe_title = re.sub(r'\s+', '-', safe_title)
            filename = f"{date}-{safe_title}.md"
            
            posts_dir = Path(project_path) / POSTS_DIR_PATH
            file_path = posts_dir / filename
            
            # 如果有指定正文文件，使用文件内容；否则为空
            content = front_matter_content
            if body_content:
                content += "\n" + body_content
                
            action = "生成"
        
        # 4. 写入文件
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.last_generated_file = file_path
            self.ui.openVSCodeButton.setEnabled(True)
            
            # 如果是新建，清空表单进入“编辑”状态
            if not is_editing:
                self.current_opened_file = file_path
                self.original_content = content
                self.ui.generateButton.setText("更新博文")
            
            self.log(f"博文已{action}: {file_path}")
            QMessageBox.information(self, "成功", f"博文已{action}:\n{file_path}")
        
        except IOError as e:
            QMessageBox.critical(self, "错误", f"写入文件失败: {str(e)}")
            self.log(f"写入文件失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"{action}博文失败 (未知错误): {str(e)}")
            self.log(f"{action}博文失败: {str(e)}")
    
    @Slot()
    def clear_form(self) -> None:
        """(保留) 清空表单"""
        self._clear_ui_fields_only() # (修改) 调用新的辅助函数
        
        # 清空时禁用 VSCode 按钮并重置编辑状态
        self.ui.openVSCodeButton.setEnabled(False)
        self.last_generated_file = None
        self.current_opened_file = None
        self.original_content = None
        
        self.ui.generateButton.setText("生成博文")
        
        self.log("表单已清空")
    
    @Slot()
    def open_in_vscode(self) -> None:
        """(保留) 在VSCode中打开"""
        project_path = self.ui.projectPathEdit.text().strip()
        file_to_open = self.last_generated_file
        
        if not project_path or not file_to_open:
            QMessageBox.warning(self, "警告", "路径或文件无效。")
            return
        
        try:
            cmd = ["code", project_path, str(file_to_open)]
            subprocess.Popen(cmd) # 移除 shell=True
            self.log(f"已在VSCode中打开: {file_to_open.name}")
        except FileNotFoundError:
            QMessageBox.critical(self, "错误", "打开VSCode失败: 'code' 命令未找到。\n请确保 VSCode 已经安装并添加到了系统的 PATH 环境变量中。")
            self.log("打开VSCode失败: 'code' 命令未找到")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开VSCode失败: {str(e)}")
            self.log(f"打开VSCode失败: {str(e)}")

    @Slot()
    def extract_keywords(self) -> None:
        """使用OpenAI API从正文中提取关键词"""
        content_file_path = self.ui.contentFilePathEdit.text().strip()
        
        if not content_file_path:
            QMessageBox.warning(self, "警告", "请先选择正文来源文件")
            return
        
        # 读取正文内容
        content = self.read_content_file(content_file_path)
        if not content:
            return
        
        # 加载OpenAI配置
        config = self._get_config_parser()
        if not config.has_section('OpenAI'):
            QMessageBox.warning(self, "警告", "未在config.ini中找到OpenAI配置")
            return
            
        api_key = config.get('OpenAI', 'api_key', fallback='')
        api_base = config.get('OpenAI', 'api_base', fallback='https://api.openai.com/v1')
        model = config.get('OpenAI', 'model', fallback='gpt-3.5-turbo')
        
        if not api_key:
            QMessageBox.warning(self, "警告", "未在config.ini中设置OpenAI API密钥")
            return
        
        # 准备API请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        prompt = f"""请从以下文本中提取五个最重要的关键词，只返回关键词，用逗号分隔，不要添加任何其他文字：

{content[:2000]}"""
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个专业的关键词提取助手，擅长从文本中提取最重要的关键词。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }
        
        try:
            self.log("正在调用OpenAI API提取关键词...")
            self.ui.extractKeywordsButton.setEnabled(False)
            self.ui.extractKeywordsButton.setText("提取中...")
            
            response = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                keywords = result["choices"][0]["message"]["content"].strip()
                
                # 将关键词填入标签输入框
                self.ui.tagsEdit.setText(keywords)
                self.log(f"已提取关键词: {keywords}")
                QMessageBox.information(self, "成功", f"已提取关键词: {keywords}")
            else:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                self.log(error_msg)
                QMessageBox.critical(self, "错误", error_msg)
                
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求错误: {str(e)}"
            self.log(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        except Exception as e:
            error_msg = f"提取关键词时发生错误: {str(e)}"
            self.log(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        finally:
            self.ui.extractKeywordsButton.setEnabled(True)
            self.ui.extractKeywordsButton.setText("提炼关键词")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlogPostGenerator()
    window.show()
    sys.exit(app.exec())