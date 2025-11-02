# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'blog_post_generator.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QTextEdit,
    QTimeEdit, QVBoxLayout, QWidget)

class Ui_BlogPostGenerator(object):
    def setupUi(self, BlogPostGenerator):
        if not BlogPostGenerator.objectName():
            BlogPostGenerator.setObjectName(u"BlogPostGenerator")
        BlogPostGenerator.resize(800, 700)
        self.centralwidget = QWidget(BlogPostGenerator)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.formLayout = QFormLayout(self.groupBox)
        self.formLayout.setObjectName(u"formLayout")
        self.label = QLabel(self.groupBox)
        self.label.setObjectName(u"label")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.projectPathEdit = QLineEdit(self.groupBox)
        self.projectPathEdit.setObjectName(u"projectPathEdit")

        self.horizontalLayout.addWidget(self.projectPathEdit)

        self.browseButton = QPushButton(self.groupBox)
        self.browseButton.setObjectName(u"browseButton")

        self.horizontalLayout.addWidget(self.browseButton)


        self.formLayout.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)


        self.verticalLayout.addWidget(self.groupBox)

        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.formLayout_2 = QFormLayout(self.groupBox_2)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.label_2)

        self.dateEdit = QDateEdit(self.groupBox_2)
        self.dateEdit.setObjectName(u"dateEdit")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.dateEdit)

        self.label_3 = QLabel(self.groupBox_2)
        self.label_3.setObjectName(u"label_3")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.label_3)

        self.timeEdit = QTimeEdit(self.groupBox_2)
        self.timeEdit.setObjectName(u"timeEdit")

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.timeEdit)

        self.label_4 = QLabel(self.groupBox_2)
        self.label_4.setObjectName(u"label_4")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.label_4)

        self.titleEdit = QLineEdit(self.groupBox_2)
        self.titleEdit.setObjectName(u"titleEdit")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.titleEdit)

        self.label_5 = QLabel(self.groupBox_2)
        self.label_5.setObjectName(u"label_5")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.label_5)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.mainCategoryEdit = QLineEdit(self.groupBox_2)
        self.mainCategoryEdit.setObjectName(u"mainCategoryEdit")

        self.horizontalLayout_2.addWidget(self.mainCategoryEdit)

        self.subCategoryEdit = QLineEdit(self.groupBox_2)
        self.subCategoryEdit.setObjectName(u"subCategoryEdit")

        self.horizontalLayout_2.addWidget(self.subCategoryEdit)


        self.formLayout_2.setLayout(3, QFormLayout.ItemRole.FieldRole, self.horizontalLayout_2)

        self.label_6 = QLabel(self.groupBox_2)
        self.label_6.setObjectName(u"label_6")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.LabelRole, self.label_6)

        self.tagsEdit = QLineEdit(self.groupBox_2)
        self.tagsEdit.setObjectName(u"tagsEdit")

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.tagsEdit)

        self.label_7 = QLabel(self.groupBox_2)
        self.label_7.setObjectName(u"label_7")

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.LabelRole, self.label_7)

        self.authorComboBox = QComboBox(self.groupBox_2)
        self.authorComboBox.addItem("")
        self.authorComboBox.setObjectName(u"authorComboBox")
        self.authorComboBox.setEditable(True)

        self.formLayout_2.setWidget(5, QFormLayout.ItemRole.FieldRole, self.authorComboBox)

        self.label_8 = QLabel(self.groupBox_2)
        self.label_8.setObjectName(u"label_8")

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.LabelRole, self.label_8)

        self.descriptionEdit = QTextEdit(self.groupBox_2)
        self.descriptionEdit.setObjectName(u"descriptionEdit")
        self.descriptionEdit.setMaximumHeight(100)

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.FieldRole, self.descriptionEdit)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.openPostButton = QPushButton(self.centralwidget)
        self.openPostButton.setObjectName(u"openPostButton")

        self.horizontalLayout_3.addWidget(self.openPostButton)
        self.generateButton = QPushButton(self.centralwidget)
        self.generateButton.setObjectName(u"generateButton")

        self.horizontalLayout_3.addWidget(self.generateButton)

        self.clearButton = QPushButton(self.centralwidget)
        self.clearButton.setObjectName(u"clearButton")

        self.horizontalLayout_3.addWidget(self.clearButton)

        self.openVSCodeButton = QPushButton(self.centralwidget)
        self.openVSCodeButton.setObjectName(u"openVSCodeButton")

        self.horizontalLayout_3.addWidget(self.openVSCodeButton)


        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.groupBox_3 = QGroupBox(self.centralwidget)
        self.groupBox_3.setObjectName(u"groupBox_3")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox_3)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.logTextEdit = QTextEdit(self.groupBox_3)
        self.logTextEdit.setObjectName(u"logTextEdit")
        self.logTextEdit.setMaximumHeight(150)
        self.logTextEdit.setReadOnly(True)

        self.verticalLayout_2.addWidget(self.logTextEdit)


        self.verticalLayout.addWidget(self.groupBox_3)

        BlogPostGenerator.setCentralWidget(self.centralwidget)

        self.retranslateUi(BlogPostGenerator)

        QMetaObject.connectSlotsByName(BlogPostGenerator)
    # setupUi

    def retranslateUi(self, BlogPostGenerator):
        BlogPostGenerator.setWindowTitle(QCoreApplication.translate("BlogPostGenerator", u"\u535a\u6587\u751f\u6210\u5de5\u5177", None))
        self.groupBox.setTitle(QCoreApplication.translate("BlogPostGenerator", u"\u535a\u6587\u5de5\u7a0b\u8bbe\u7f6e", None))
        self.label.setText(QCoreApplication.translate("BlogPostGenerator", u"\u535a\u6587\u5de5\u7a0b\u8def\u5f84:", None))
        self.browseButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6d4f\u89c8", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("BlogPostGenerator", u"\u535a\u6587\u4fe1\u606f", None))
        self.label_2.setText(QCoreApplication.translate("BlogPostGenerator", u"\u65e5\u671f:", None))
        self.dateEdit.setDisplayFormat(QCoreApplication.translate("BlogPostGenerator", u"yyyy-M-d", None))
        self.label_3.setText(QCoreApplication.translate("BlogPostGenerator", u"\u65f6\u95f4:", None))
        self.timeEdit.setDisplayFormat(QCoreApplication.translate("BlogPostGenerator", u"HH:mm:ss", None))
        self.label_4.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6807\u9898:", None))
        self.label_5.setText(QCoreApplication.translate("BlogPostGenerator", u"\u5206\u7c7b:", None))
        self.mainCategoryEdit.setPlaceholderText(QCoreApplication.translate("BlogPostGenerator", u"\u4e3b\u5206\u7c7b", None))
        self.subCategoryEdit.setPlaceholderText(QCoreApplication.translate("BlogPostGenerator", u"\u5b50\u5206\u7c7b", None))
        self.label_6.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6807\u7b7e:", None))
        self.tagsEdit.setPlaceholderText(QCoreApplication.translate("BlogPostGenerator", u"\u591a\u4e2a\u6807\u7b7e\u7528\u7a7a\u683c\u5206\u9694", None))
        self.label_7.setText(QCoreApplication.translate("BlogPostGenerator", u"\u4f5c\u8005:", None))
        self.authorComboBox.setItemText(0, "")

        self.label_8.setText(QCoreApplication.translate("BlogPostGenerator", u"\u63cf\u8ff0:", None))
        self.openPostButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6253\u5f00\u5df2\u6709\u535a\u6587", None))
        self.openPostButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6253\u5f00\u5df2\u6709\u535a\u6587", None))
        self.generateButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u751f\u6210\u535a\u6587", None))
        self.clearButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u6e05\u7a7a", None))
        self.openVSCodeButton.setText(QCoreApplication.translate("BlogPostGenerator", u"\u7528VSCode\u6253\u5f00", None))
        self.groupBox_3.setTitle(QCoreApplication.translate("BlogPostGenerator", u"\u72b6\u6001\u65e5\u5fd7", None))
    # retranslateUi