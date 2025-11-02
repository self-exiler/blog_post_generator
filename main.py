import sys
import re
import subprocess
import configparser
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
import yaml
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import QDate, QTime, Slot
from blog_post_generator_ui import Ui_BlogPostGenerator

# 常量
CONFIG_FILE_NAME = "config.ini"
AUTHORS_FILE_PATH = "_data/authors.yml"
POSTS_DIR_PATH = "_posts"

# 优化 3：使用正则表达式精简解析
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
        # 优化 1：确保按钮文本在启动时是“生成”
        self.ui.generateButton.setText("生成博文")

    def connect_signals(self) -> None:
        """连接所有信号和槽"""
        self.ui.browseButton.clicked.connect(self.browse_project_path)
        self.ui.openPostButton.clicked.connect(self.open_existing_post)
        self.ui.generateButton.clicked.connect(self.generate_blog_post)
        self.ui.clearButton.clicked.connect(self.clear_form)
        self.ui.openVSCodeButton.clicked.connect(self.open_in_vscode)
    
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
        """辅助函数：获取并读取配置文件解析器"""
        config = configparser.ConfigParser()
        if self.config_file.exists():
            config.read(self.config_file, encoding='utf-8')
        return config

    def load_config(self) -> None:
        """加载配置文件"""
        try:
            config = self._get_config_parser()
            blog_project_path = config.get('Settings', 'blog_project_path', fallback='')
            if blog_project_path:
                self.ui.projectPathEdit.setText(blog_project_path)
                self.log(f"已加载配置中的博客工程路径: {blog_project_path}")
        except configparser.Error as e:
            self.log(f"加载配置文件失败: {str(e)}")
    
    def save_config(self) -> None:
        """保存配置文件"""
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
    def browse_project_path(self) -> None:
        """浏览并选择博文工程路径"""
        directory = QFileDialog.getExistingDirectory(self, "选择博文工程路径")
        if directory:
            self.ui.projectPathEdit.setText(directory)
            self.log(f"已选择博文工程路径: {directory}")
            self.save_config()
            self.load_authors()
    
    @Slot()
    def load_authors(self) -> None:
        """加载作者列表 (使用 PyYAML)"""
        project_path = self.ui.projectPathEdit.text().strip()
        self.ui.authorComboBox.clear()
        self.ui.authorComboBox.addItem("")  # 添加空选项
        
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

    def _build_front_matter(self, data: Dict[str, Any]) -> str:
        """精简：构建 YAML front matter 字符串"""
        content = "---\n"
        for key, value in data.items():
            if not value:  # 跳过空值
                continue
            
            if key == "description" and '\n' in str(value):
                # 对多行描述特殊处理
                content += "description: |-\n"
                for line in str(value).splitlines():
                    content += f"  {line}\n"
            else:
                content += f"{key}: {value}\n"
        
        content += "---\n"
        return content

    def _parse_front_matter(self, content: str) -> tuple[Dict[str, Any], str]:
        """(优化 3) 精简：使用re.split解析markdown文件的front matter"""
        front_matter = {}
        body_content = ""
        
        # 使用正则表达式分割
        parts = FRONT_MATTER_DELIMITER.split(content, maxsplit=2)
        
        # parts[0] 应该是空字符串
        # parts[1] 是 front matter
        # parts[2] 是正文
        if len(parts) == 3 and parts[0].strip() == '':
            try:
                front_matter = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError as e:
                self.log(f"解析front matter失败: {str(e)}")
                return {}, content # 解析失败，返回原始内容
            
            body_content = parts[2]
        else:
            # 没有front matter，整个内容作为正文
            body_content = content
        
        return front_matter, body_content

    @Slot()
    def open_existing_post(self) -> None:
        """打开已有的博文文件进行编辑"""
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
            
            # 保存原始内容和文件路径
            self.original_content = content
            self.current_opened_file = Path(file_path)
            
            # 优化 2 (Bug修复): 同时设置 last_generated_file
            self.last_generated_file = self.current_opened_file
            
            # 填充表单
            self._populate_form_from_front_matter(front_matter)
            
            # 启用VSCode按钮
            self.ui.openVSCodeButton.setEnabled(True)
            
            # 优化 1 (UI): 更改按钮文本为“更新”
            self.ui.generateButton.setText("更新博文")
            
            self.log(f"已打开博文: {file_path}")
            
        except IOError as e:
            QMessageBox.critical(self, "错误", f"读取文件失败: {str(e)}")
            self.log(f"读取文件失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开文件失败: {str(e)}")
            self.log(f"打开文件失败: {str(e)}")
    
    def _populate_form_from_front_matter(self, front_matter: Dict[str, Any]) -> None:
        """根据front matter填充表单"""
        # 清空当前表单（防止旧数据残留）
        self.clear_form()
        # 备注: clear_form会重置按钮文本，我们在这里重新设置它
        self.ui.generateButton.setText("更新博文")

        # 标题
        self.ui.titleEdit.setText(front_matter.get('title', ''))
        
        # 日期和时间
        date_str = front_matter.get('date', '')
        if isinstance(date_str, datetime): # PyYAML 可能会将其解析为 datetime 对象
             self.ui.dateEdit.setDate(QDate(date_str.year, date_str.month, date_str.day))
             self.ui.timeEdit.setTime(QTime(date_str.hour, date_str.minute, date_str.second))
        elif isinstance(date_str, str): # 否则，作为字符串解析
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
        
        # 分类
        categories_list = front_matter.get('categories', [])
        if isinstance(categories_list, list):
            if len(categories_list) >= 1:
                self.ui.mainCategoryEdit.setText(categories_list[0])
            if len(categories_list) >= 2:
                self.ui.subCategoryEdit.setText(categories_list[1])
        elif isinstance(categories_list, str): # 兼容旧的 "[a,b]" 格式
            try:
                clean_categories = categories_list.strip('[]')
                category_parts = clean_categories.split(',')
                if len(category_parts) >= 1: self.ui.mainCategoryEdit.setText(category_parts[0].strip())
                if len(category_parts) >= 2: self.ui.subCategoryEdit.setText(category_parts[1].strip())
            except Exception as e:
                self.log(f"解析分类(str)失败: {str(e)}")

        # 标签
        tags_list = front_matter.get('tags', [])
        if isinstance(tags_list, list):
            self.ui.tagsEdit.setText(' '.join(tags_list))
        elif isinstance(tags_list, str): # 兼容旧的 "[a,b]" 格式
            try:
                clean_tags = tags_list.strip('[]')
                tag_parts = clean_tags.split(',')
                self.ui.tagsEdit.setText(' '.join(tag.strip() for tag in tag_parts))
            except Exception as e:
                self.log(f"解析标签(str)失败: {str(e)}")
        
        # 作者
        author = front_matter.get('author', '')
        index = self.ui.authorComboBox.findText(author)
        if index >= 0:
            self.ui.authorComboBox.setCurrentIndex(index)
        else:
            self.ui.authorComboBox.setCurrentText(author)
        
        # 描述
        self.ui.descriptionEdit.setPlainText(front_matter.get('description', ''))

    @Slot()
    def generate_blog_post(self) -> None:
        """生成博文文件或更新已有文件"""
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
        
        # 优化：YAML 应该使用列表
        categories_list = []
        if main_category: categories_list.append(main_category)
        if sub_category: categories_list.append(sub_category)

        tags_list = [tag.strip() for tag in tags_raw.split(' ') if tag.strip()]
        
        # 2. 构建文件名 (仅在新建时使用)
        safe_title = re.sub(r'[^\w\u4e00-\u9fa5\s-]', '', title)
        safe_title = re.sub(r'\s+', '-', safe_title)
        
        # 3. 精简：使用字典构建 front matter
        front_matter_data = {
            "title": title,
            "date": f"{date} {time} +0800",
            # 优化：使用标准YAML列表
            "categories": categories_list if categories_list else None,
            "tags": tags_list if tags_list else None,
            "author": self.ui.authorComboBox.currentText().strip(),
            "description": self.ui.descriptionEdit.toPlainText().strip()
        }
        # 使用 PyYAML 来转储 front matter，更健壮
        front_matter_content = "---\n"
        front_matter_content += yaml.dump(front_matter_data, allow_unicode=True, sort_keys=False)
        front_matter_content += "---\n"
        
        # 4. 确定文件路径和内容
        is_editing = self.current_opened_file is not None
        
        if is_editing:
            file_path = self.current_opened_file
            _, body_content = self._parse_front_matter(self.original_content)
            content = front_matter_content + body_content
            action = "更新"
        else:
            filename = f"{date}-{safe_title}.md"
            posts_dir = Path(project_path) / POSTS_DIR_PATH
            file_path = posts_dir / filename
            content = front_matter_content
            action = "生成"
        
        # 5. 写入文件
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.last_generated_file = file_path
            self.ui.openVSCodeButton.setEnabled(True) # 启用按钮
            
            # 如果是新建，清空表单进入“编辑”状态
            if not is_editing:
                self.current_opened_file = file_path
                self.original_content = content
                self.ui.generateButton.setText("更新博文") # 优化 1
            
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
        """清空表单"""
        self.ui.titleEdit.clear()
        self.ui.mainCategoryEdit.clear()
        self.ui.subCategoryEdit.clear()
        self.ui.tagsEdit.clear()
        self.ui.authorComboBox.setCurrentIndex(0)
        self.ui.descriptionEdit.clear()
        
        self.ui.dateEdit.setDate(QDate.currentDate())
        self.ui.timeEdit.setTime(QTime.currentTime())
        
        # 清空时禁用 VSCode 按钮并重置编辑状态
        self.ui.openVSCodeButton.setEnabled(False)
        self.last_generated_file = None
        self.current_opened_file = None
        self.original_content = None
        
        # 优化 1：重置按钮文本
        self.ui.generateButton.setText("生成博文")
        
        self.log("表单已清空")
    
    @Slot()
    def open_in_vscode(self) -> None:
        """在VSCode中打开博客工程文件夹和最后生成的markdown文件"""
        project_path = self.ui.projectPathEdit.text().strip()
        
        # 优化 2：现在 self.last_generated_file 会被正确设置
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BlogPostGenerator()
    window.show()
    sys.exit(app.exec())