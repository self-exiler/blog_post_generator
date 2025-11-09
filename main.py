import sys,os
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
        """记录日志，增强错误处理"""
        if not isinstance(message, str):
            message = str(message)
            
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.ui.logTextEdit.append(f"[{timestamp}] {message}")
            self.ui.logTextEdit.ensureCursorVisible()
        except Exception as e:
            # 如果日志记录失败，至少输出到控制台
            print(f"日志记录失败: {str(e)}")
            print(f"原始消息: {message}")
    
    def _get_config_parser(self) -> configparser.ConfigParser:
        """获取配置解析器，增强错误处理"""
        config = configparser.ConfigParser()
        
        try:
            if self.config_file.exists():
                config.read(self.config_file, encoding='utf-8')
                self.log(f"已加载配置文件: {self.config_file}")
            else:
                self.log(f"配置文件不存在: {self.config_file}")
        except UnicodeDecodeError:
            self.log(f"配置文件编码错误，请使用UTF-8编码: {self.config_file}")
        except Exception as e:
            self.log(f"加载配置文件失败: {str(e)}")
        
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
    
    def _save_project_path_to_config(self, path: str) -> None:
        """保存项目路径到配置文件，增强错误处理"""
        try:
            config = self._get_config_parser()
            
            if not config.has_section('Settings'):
                config.add_section('Settings')
                
            config.set('Settings', 'blog_project_path', path)
            
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入配置文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
                
            self.log(f"已保存项目路径到配置文件: {path}")
            
        except PermissionError:
            self._show_error("没有权限写入配置文件，请检查文件权限")
        except configparser.Error as e:
            self._show_error(f"配置文件格式错误: {str(e)}")
        except Exception as e:
            self._show_error(f"保存项目路径到配置文件失败: {str(e)}")
    
    def save_config(self) -> None:
        """保存配置文件"""
        blog_project_path = self.ui.projectPathEdit.text().strip()
        if blog_project_path:
            self._save_project_path_to_config(blog_project_path)
    
    @Slot()
    def browse_content_file(self) -> None:
        """浏览并选择正文来源文件，增强错误处理"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择正文文件", "", "Markdown文件 (*.md);;所有文件 (*)"
            )
            
            if file_path:
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    self._show_error(f"选择的文件不存在: {file_path}")
                    return
                    
                # 检查是否是文件
                if not os.path.isfile(file_path):
                    self._show_error(f"选择的路径不是文件: {file_path}")
                    return
                
                # 检查文件是否可读
                if not os.access(file_path, os.R_OK):
                    self._show_error(f"无法读取文件: {file_path}")
                    return
                
                self.ui.contentFilePathEdit.setText(file_path)
                self.log(f"已选择正文来源文件: {file_path}")
                
        except Exception as e:
            self._show_error(f"选择正文来源文件时发生错误: {str(e)}")
    
    @Slot()
    def open_content_file(self) -> None:
        """打开正文来源文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择正文文件", "", "Markdown文件 (*.md);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        # 读取文件内容并填充到正文编辑框
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.ui.contentEdit.setPlainText(content)
            self.ui.contentFilePathEdit.setText(file_path)
            self.log(f"已加载正文文件: {file_path}")
        except Exception as e:
            self._show_error(f"读取正文文件失败: {str(e)}")
    
    def read_content_file(self, file_path: str) -> str:
        """读取MD文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self._show_error(f"读取正文文件失败: {str(e)}")
            return ""
    
    @Slot()
    def browse_project_path(self) -> None:
        """浏览并选择博客项目路径，增强错误处理"""
        try:
            directory = QFileDialog.getExistingDirectory(self, "选择博文工程路径")
            
            if directory:
                # 检查目录是否存在
                if not os.path.exists(directory):
                    self._show_error(f"选择的目录不存在: {directory}")
                    return
                    
                # 检查是否是目录
                if not os.path.isdir(directory):
                    self._show_error(f"选择的路径不是目录: {directory}")
                    return
                
                # 检查目录是否可读
                if not os.access(directory, os.R_OK):
                    self._show_error(f"无法读取目录: {directory}")
                    return
                
                self.ui.projectPathEdit.setText(directory)
                self.log(f"已选择博文工程路径: {directory}")
                
                # 保存到配置文件
                self.save_config()
                
                # 加载作者列表
                self.load_authors()
                
        except Exception as e:
            self._show_error(f"选择博文工程路径时发生错误: {str(e)}")
    
    @Slot()
    def load_authors(self) -> None:
        """从YAML文件加载作者列表，增强错误处理"""
        project_path = self.ui.projectPathEdit.text().strip()
        self.ui.authorComboBox.clear()
        self.ui.authorComboBox.addItem("")
        
        if not project_path:
            self.log("警告: 博客工程路径为空，无法加载作者列表")
            return
            
        authors_file = Path(project_path) / AUTHORS_FILE_PATH
        
        # 检查文件是否存在
        if not authors_file.exists():
            self.log(f"警告: 未找到作者文件: {authors_file}")
            return
            
        # 检查文件是否可读
        if not authors_file.is_file():
            self.log(f"错误: 作者路径不是文件: {authors_file}")
            return

        try:
            # 尝试读取文件
            with open(authors_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查文件是否为空
            if not content.strip():
                self.log(f"警告: 作者文件为空: {authors_file}")
                return
                
            # 解析YAML内容
            authors_data = yaml.safe_load(content)
                
            # 验证数据格式
            if authors_data is None:
                self.log(f"警告: 作者文件内容为空或无效: {authors_file}")
                return
                
            if not isinstance(authors_data, dict):
                self.log(f"错误: 作者文件格式不正确，期望是一个字典，但得到了 {type(authors_data)}")
                return
            
            # 提取作者名称
            author_names = list(authors_data.keys())
            
            # 验证作者名称
            valid_authors = []
            for name in author_names:
                if isinstance(name, str) and name.strip():
                    valid_authors.append(name.strip())
                else:
                    self.log(f"警告: 跳过无效的作者名称: {name}")
            
            # 添加到下拉框
            if valid_authors:
                self.ui.authorComboBox.addItems(valid_authors)
                self.log(f"成功加载 {len(valid_authors)} 个作者")
            else:
                self.log("警告: 未找到有效的作者名称")
                    
        except yaml.YAMLError as e:
            self.log(f"错误: 加载作者列表失败 (YAML 解析错误): {str(e)}")
        except UnicodeDecodeError as e:
            self.log(f"错误: 作者文件编码错误，请使用UTF-8编码: {str(e)}")
        except PermissionError as e:
            self.log(f"错误: 没有权限读取作者文件: {str(e)}")
        except IOError as e:
            self.log(f"错误: 读取作者文件时发生IO错误: {str(e)}")
        except Exception as e:
            self.log(f"错误: 加载作者列表失败 (未知错误): {str(e)}")

    def _parse_front_matter(self, content: str) -> Tuple[Dict[str, Any], str]:
        """(保留) 使用re.split解析markdown文件的front matter"""
        front_matter = {}
        body_content = ""
        
        if not content or not isinstance(content, str):
            self.log("警告: 内容为空或不是字符串类型")
            return {}, content
        
        parts = FRONT_MATTER_DELIMITER.split(content, maxsplit=2)
        
        if len(parts) == 3 and parts[0].strip() == '':
            try:
                front_matter = yaml.safe_load(parts[1]) or {}
                if not isinstance(front_matter, dict):
                    self.log("警告: front matter不是字典类型，将重置为空字典")
                    front_matter = {}
            except yaml.YAMLError as e:
                self.log(f"解析front matter失败: {str(e)}")
                return {}, content
            except Exception as e:
                self.log(f"解析front matter时发生未知错误: {str(e)}")
                return {}, content
            
            body_content = parts[2].lstrip('\n') # 移除YAML和正文之间的多余换行
        else:
            self.log("提示: 未找到front matter格式，将整个内容作为正文处理")
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
            
        except FileNotFoundError:
            self._show_error(f"文件不存在: {file_path}")
        except PermissionError:
            self._show_error(f"没有权限读取文件: {file_path}")
        except UnicodeDecodeError:
            self._show_error(f"文件编码错误，请确保文件使用UTF-8编码: {file_path}")
        except yaml.YAMLError as e:
            self._show_error(f"解析front matter失败: {str(e)}")
        except Exception as e:
            self._show_error(f"打开博文文件失败: {str(e)}")
    
    def _clear_ui_fields_only(self) -> None:
        """仅清空UI输入字段，不涉及状态重置，增强错误处理"""
        try:
            self.ui.titleEdit.clear()
            self.ui.mainCategoryEdit.clear()
            self.ui.subCategoryEdit.clear()
            self.ui.tagsEdit.clear()
            self.ui.authorComboBox.setCurrentIndex(0)
            self.ui.descriptionEdit.clear()
            self.ui.contentFilePathEdit.clear()
            
            # 重置日期时间为当前时间
            self.ui.dateEdit.setDate(QDate.currentDate())
            self.ui.timeEdit.setTime(QTime.currentTime())
            
        except Exception as e:
            self.log(f"清空UI字段时发生错误: {str(e)}")
            # 即使清空失败，也要尝试继续执行，避免UI处于不一致状态
            try:
                self.ui.titleEdit.clear()
                self.ui.mainCategoryEdit.clear()
                self.ui.subCategoryEdit.clear()
                self.ui.tagsEdit.clear()
                self.ui.authorComboBox.setCurrentIndex(0)
                self.ui.descriptionEdit.clear()
                self.ui.contentFilePathEdit.clear()
            except:
                pass  # 最后的尝试，即使失败也不抛出异常

    def _populate_form_from_front_matter(self, front_matter: Dict[str, Any]) -> None:
        """(保留) 根据front matter填充表单"""
        # (修复) 不再调用 clear_form()，而是调用 _clear_ui_fields_only()
        self._clear_ui_fields_only() 
        
        # 重置按钮文本
        self.ui.generateButton.setText("更新博文")

        # 设置标题 - 添加类型检查
        title = front_matter.get('title', '')
        if title:
            self.ui.titleEdit.setText(str(title))
        
        # 处理日期时间 - 增强错误处理
        date_str = front_matter.get('date', '')
        if isinstance(date_str, datetime):
             try:
                 self.ui.dateEdit.setDate(QDate(date_str.year, date_str.month, date_str.day))
                 self.ui.timeEdit.setTime(QTime(date_str.hour, date_str.minute, date_str.second))
             except Exception as e:
                 self.log(f"警告: 设置日期时间失败: {str(e)}")
        elif isinstance(date_str, str):
            try:
                parts = date_str.split(' ')
                if len(parts) >= 2:
                    date_part = parts[0]
                    time_part = parts[1].split('+')[0]
                    
                    date_obj = QDate.fromString(date_part, "yyyy-M-d")
                    if date_obj.isValid(): 
                        self.ui.dateEdit.setDate(date_obj)
                    else:
                        self.log(f"警告: 无效的日期格式: {date_part}")
                    
                    time_obj = QTime.fromString(time_part, "HH:mm:ss")
                    if time_obj.isValid(): 
                        self.ui.timeEdit.setTime(time_obj)
                    else:
                        self.log(f"警告: 无效的时间格式: {time_part}")
                else:
                    self.log(f"警告: 日期时间格式不正确: {date_str}")
            except Exception as e:
                self.log(f"解析日期时间字符串失败: {str(e)}")
        elif date_str:
            self.log(f"警告: 日期时间类型不支持: {type(date_str)}")
        
        # 处理分类 - 增强错误处理
        categories_list = front_matter.get('categories', [])
        if isinstance(categories_list, list):
            try:
                if len(categories_list) >= 1:
                    self.ui.mainCategoryEdit.setText(str(categories_list[0]))
                if len(categories_list) >= 2:
                    self.ui.subCategoryEdit.setText(str(categories_list[1]))
            except Exception as e:
                self.log(f"警告: 处理分类时出错: {str(e)}")
        elif categories_list:
            self.log(f"警告: 分类不是列表类型: {type(categories_list)}")

        # 处理标签 - 增强错误处理
        tags_list = front_matter.get('tags', [])
        if isinstance(tags_list, list):
            try:
                # 将列表转换为空格分隔的字符串
                tags_str = ' '.join(str(tag) for tag in tags_list if tag)
                self.ui.tagsEdit.setText(tags_str)
            except Exception as e:
                self.log(f"警告: 处理标签时出错: {str(e)}")
        elif tags_list:
            self.log(f"警告: 标签不是列表类型: {type(tags_list)}")
        
        # 处理作者 - 增强错误处理
        author = front_matter.get('author', '')
        if author:
            try:
                author_str = str(author)
                index = self.ui.authorComboBox.findText(author_str)
                if index >= 0:
                    self.ui.authorComboBox.setCurrentIndex(index)
                else:
                    self.ui.authorComboBox.setCurrentText(author_str)
            except Exception as e:
                self.log(f"警告: 处理作者时出错: {str(e)}")
        
        # 处理描述 - 增强错误处理
        description = front_matter.get('description', '')
        if description:
            try:
                self.ui.descriptionEdit.setPlainText(str(description))
            except Exception as e:
                self.log(f"警告: 处理描述时出错: {str(e)}")

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
            self._show_error(f"写入文件失败: {str(e)}")
        except Exception as e:
            self._show_error(f"{action}博文失败 (未知错误): {str(e)}")
    
    @Slot()
    def clear_form(self) -> None:
        """清空表单，增强错误处理"""
        try:
            self._clear_ui_fields_only() # 调用辅助函数清空UI字段
            
            # 清空时禁用 VSCode 按钮并重置编辑状态
            self.ui.openVSCodeButton.setEnabled(False)
            self.last_generated_file = None
            self.current_opened_file = None
            self.original_content = None
            
            self.ui.generateButton.setText("生成博文")
            
            self.log("表单已清空")
            
        except Exception as e:
            self._show_error(f"清空表单时发生错误: {str(e)}")
    
    @Slot()
    def open_in_vscode(self) -> None:
        """(保留) 在VSCode中打开，增强错误处理"""
        project_path = self.ui.projectPathEdit.text().strip()
        file_to_open = self.last_generated_file
        
        # 验证项目路径
        if not project_path:
            self._show_error("项目路径为空，请先指定博文工程路径")
            return
            
        if not os.path.exists(project_path):
            self._show_error(f"项目路径不存在: {project_path}")
            return
            
        if not os.path.isdir(project_path):
            self._show_error(f"项目路径不是目录: {project_path}")
            return
        
        # 验证文件路径
        if not file_to_open:
            self._show_error("没有可打开的文件，请先生成或打开博文")
            return
            
        if not file_to_open.exists():
            self._show_error(f"文件不存在: {file_to_open}")
            return
            
        if not file_to_open.is_file():
            self._show_error(f"路径不是文件: {file_to_open}")
            return
        
        try:
            cmd = ["code", project_path, str(file_to_open)]
            subprocess.Popen(cmd) # 移除 shell=True
            self.log(f"已在VSCode中打开: {file_to_open.name}")
        except FileNotFoundError:
            self._show_error("打开VSCode失败: 'code' 命令未找到。\n请确保 VSCode 已经安装并添加到了系统的 PATH 环境变量中。")
        except PermissionError:
            self._show_error("没有权限执行VSCode命令，请检查系统权限")
        except subprocess.SubprocessError as e:
            self._show_error(f"启动VSCode进程失败: {str(e)}")
        except Exception as e:
            self._show_error(f"打开VSCode失败: {str(e)}")

    @Slot()
    def extract_keywords(self) -> None:
        """使用OpenAI API从正文中提取关键词"""
        content_file_path = self.ui.contentFilePathEdit.text().strip()
        
        # 验证输入
        if not content_file_path:
            self._show_error("请先选择正文来源文件")
            return
        
        # 读取正文内容
        content = self.read_content_file(content_file_path)
        if not content:
            return
        
        # 加载OpenAI配置
        config = self._get_config_parser()
        if not config.has_section('OpenAI'):
            self._show_error("未在config.ini中找到OpenAI配置")
            return
            
        api_key = config.get('OpenAI', 'api_key', fallback='')
        api_base = config.get('OpenAI', 'api_base', fallback='https://api.openai.com/v1')
        model = config.get('OpenAI', 'model', fallback='gpt-3.5-turbo')
        
        if not api_key:
            self._show_error("未在config.ini中设置OpenAI API密钥")
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
        
        # 执行API请求
        self._execute_api_request(api_base, headers, data)
    
    def _show_error(self, message: str) -> None:
        """显示错误消息并记录日志"""
        self.log(message)
        QMessageBox.critical(self, "错误", message)
    
    def _execute_api_request(self, api_base: str, headers: dict, data: dict) -> None:
        """执行API请求并处理响应"""
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
                self._show_error(f"API请求失败: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            self._show_error(f"网络请求错误: {str(e)}")
        except Exception as e:
            self._show_error(f"提取关键词时发生错误: {str(e)}")
        finally:
            self.ui.extractKeywordsButton.setEnabled(True)
            self.ui.extractKeywordsButton.setText("提炼关键词")

def main():
    """主函数，增强错误处理"""
    try:
        app = QApplication(sys.argv)
        
        # 设置应用程序信息
        app.setApplicationName("博文生成器")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("BlogPostGenerator")
        
        # 创建并显示主窗口
        window = BlogPostGenerator()
        window.show()
        
        # 运行应用程序
        exit_code = app.exec()
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"应用程序启动失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()