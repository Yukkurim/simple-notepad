import sys
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                               QFileDialog, QPlainTextEdit, QLabel, QFrame, 
                               QTextEdit, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QColor, QPainter, QTextFormat, QKeySequence, QFont, QAction, QIcon

# Fluent Widgets
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF,
    CommandBar, Action, TransparentToolButton, InfoBar, InfoBarPosition,
    setTheme, Theme, LineEdit, RoundMenu, PushButton
)
from qfluentwidgets import qconfig

# --- 安全にアイコンを取得するヘルパー ---
def get_icon(name, fallback_name="EDIT"):
    if hasattr(FIF, name):
        return getattr(FIF, name)
    if hasattr(FIF, fallback_name):
        return getattr(FIF, fallback_name)
    return FIF.EDIT

# --- 行番号付きエディタ ---
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)
        
        # デザイン調整: 枠線を消してフラットに
        self.setFrameShape(QFrame.NoFrame)
        
        # エディタ用フォント設定 (Consolas)
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        self.setFont(font)
        
        # シグナル接続
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        space = 24 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        
        # 修正箇所: 引数を正しく設定
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        
        # 背景色をエディタと馴染ませる
        is_dark = qconfig.theme == Theme.DARK
        bg_color = QColor(32, 32, 32) if is_dark else QColor(248, 248, 248) 
        text_color = QColor(100, 100, 100) if is_dark else QColor(160, 160, 160)
        
        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        painter.setPen(text_color)
        painter.setFont(QFont("Consolas", 10))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.drawText(0, int(top), self.lineNumberArea.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            is_dark = qconfig.theme == Theme.DARK
            # ハイライト色
            line_color = QColor(255, 255, 255, 10) if is_dark else QColor(0, 0, 0, 8)
            
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def contextMenuEvent(self, event):
        menu = RoundMenu(parent=self)
        menu.addAction(Action(get_icon("CUT"), '切り取り', triggered=self.cut))
        menu.addAction(Action(get_icon("COPY"), 'コピー', triggered=self.copy))
        menu.addAction(Action(get_icon("PASTE"), '貼り付け', triggered=self.paste))
        menu.addSeparator()
        menu.addAction(Action(get_icon("SELECT_ALL", "ACCEPT"), 'すべて選択', triggered=self.selectAll))
        menu.exec(event.globalPos())

# --- メインエディタ画面 ---
class EditorInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EditorInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(0)

        # 1. ツールバー (CommandBar)
        self.commandBar = CommandBar(self)
        self.commandBar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        # 修正箇所: setBackgroundColor を setStyleSheet に変更
        self.commandBar.setStyleSheet("background: transparent;") 
        self.vBoxLayout.addWidget(self.commandBar)
        
        # 区切り線
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setFixedHeight(1)
        # テーマに応じたボーダー色
        border_col = "#3e3e3e" if qconfig.theme == Theme.DARK else "#e5e5e5"
        line.setStyleSheet(f"background-color: transparent; border-top: 1px solid {border_col};")
        self.vBoxLayout.addWidget(line)

        # 2. 検索バー
        self.searchBarContainer = QWidget()
        bg_col = "#202020" if qconfig.theme == Theme.DARK else "#f9f9f9"
        self.searchBarContainer.setStyleSheet(f"background-color: {bg_col};")
        
        self.searchLayout = QHBoxLayout(self.searchBarContainer)
        self.searchLayout.setContentsMargins(20, 8, 20, 8)
        self.searchLayout.setSpacing(10)
        
        self.searchEdit = LineEdit()
        self.searchEdit.setPlaceholderText("検索...")
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setMaximumWidth(300)
        self.searchEdit.returnPressed.connect(self.searchNext)
        
        self.btnNext = TransparentToolButton(get_icon("DOWN", "ChevronDown"), self)
        self.btnNext.clicked.connect(self.searchNext)
        self.btnNext.setToolTip("次を検索")
        
        self.btnPrev = TransparentToolButton(get_icon("UP", "ChevronUp"), self)
        self.btnPrev.clicked.connect(self.searchPrev)
        self.btnPrev.setToolTip("前を検索")
        
        self.btnCloseSearch = TransparentToolButton(get_icon("CLOSE", "Cancel"), self)
        self.btnCloseSearch.clicked.connect(lambda: self.searchBarContainer.hide())

        self.searchLayout.addWidget(self.searchEdit)
        self.searchLayout.addWidget(self.btnNext)
        self.searchLayout.addWidget(self.btnPrev)
        self.searchLayout.addStretch(1)
        self.searchLayout.addWidget(self.btnCloseSearch)
        
        self.vBoxLayout.addWidget(self.searchBarContainer)
        self.searchBarContainer.hide()

        # 3. エディタエリア
        self.editor = CodeEditor(self)
        self.vBoxLayout.addWidget(self.editor)

        # 4. ステータスバー
        self.statusBar = QWidget()
        self.statusBar.setFixedHeight(32)
        self.statusLayout = QHBoxLayout(self.statusBar)
        self.statusLayout.setContentsMargins(15, 0, 15, 0)
        self.statusLayout.setSpacing(20)
        
        status_font = QFont("Segoe UI", 9)
        
        self.lblCursor = QLabel("Ln 1, Col 1")
        self.lblLength = QLabel("0文字")
        self.lblZoom = QLabel("100%")
        
        for lbl in [self.lblCursor, self.lblLength, self.lblZoom]:
            lbl.setFont(status_font)
            lbl.setStyleSheet("color: #888888;")
            self.statusLayout.addWidget(lbl)
            
        self.statusLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.statusBar)

        self.currentFile = None
        self.zoomLevel = 100
        self._initActions()
        self._initCommandBar()
        self._connectSignals()

    def _connectSignals(self):
        self.editor.cursorPositionChanged.connect(self.updateStatus)
        self.editor.textChanged.connect(self.updateStatus)

    def _initActions(self):
        # ファイル操作
        self.newAction = Action(get_icon("ADD"), "新規", self)
        self.newAction.setShortcut(QKeySequence.New)
        self.newAction.triggered.connect(self.newFile)

        self.openAction = Action(get_icon("FOLDER"), "開く", self)
        self.openAction.setShortcut(QKeySequence.Open)
        self.openAction.triggered.connect(self.openFile)

        self.saveAction = Action(get_icon("SAVE"), "保存", self)
        self.saveAction.setShortcut(QKeySequence.Save)
        self.saveAction.triggered.connect(self.saveFile)

        # 編集
        self.undoAction = Action(get_icon("RETURN", "UNDO"), "元に戻す", self) 
        self.undoAction.setShortcut(QKeySequence.Undo)
        self.undoAction.triggered.connect(self.editor.undo)

        self.redoAction = Action(get_icon("REDO", "Sync"), "やり直し", self)
        self.redoAction.setShortcut(QKeySequence.Redo)
        self.redoAction.triggered.connect(self.editor.redo)

        # 検索
        self.findAction = Action(get_icon("SEARCH"), "検索", self)
        self.findAction.setShortcut(QKeySequence.Find)
        self.findAction.triggered.connect(self.showSearchBar)

        # 表示オプション
        self.wrapAction = Action(get_icon("ALIGNMENT"), "折り返し", self, checkable=True)
        self.wrapAction.setChecked(True)
        self.wrapAction.toggled.connect(self.toggleWrap)

        # ズーム
        self.zoomInAction = Action(get_icon("ZOOM_IN"), "拡大", self)
        self.zoomInAction.triggered.connect(self.zoomIn)
        self.zoomOutAction = Action(get_icon("ZOOM_OUT"), "縮小", self)
        self.zoomOutAction.triggered.connect(self.zoomOut)

    def _initCommandBar(self):
        self.commandBar.addAction(self.newAction)
        self.commandBar.addAction(self.openAction)
        self.commandBar.addAction(self.saveAction)
        self.commandBar.addSeparator()
        self.commandBar.addAction(self.undoAction)
        self.commandBar.addAction(self.redoAction)
        self.commandBar.addSeparator()
        self.commandBar.addAction(self.findAction)
        
        self.commandBar.addSeparator()
        self.commandBar.addAction(self.wrapAction)
        self.commandBar.addAction(self.zoomInAction)
        self.commandBar.addAction(self.zoomOutAction)

    def updateStatus(self):
        cursor = self.editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        length = len(self.editor.toPlainText())
        self.lblCursor.setText(f"Ln {line}, Col {col}")
        self.lblLength.setText(f"{length}文字")

    def toggleWrap(self, checked):
        if checked:
            self.editor.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        else:
            self.editor.setLineWrapMode(QPlainTextEdit.NoWrap)

    def zoomIn(self):
        self.editor.zoomIn(1)
        self.zoomLevel += 10
        self.lblZoom.setText(f"{self.zoomLevel}%")

    def zoomOut(self):
        self.editor.zoomOut(1)
        self.zoomLevel = max(10, self.zoomLevel - 10)
        self.lblZoom.setText(f"{self.zoomLevel}%")

    def showSearchBar(self):
        self.searchBarContainer.show()
        self.searchEdit.setFocus()
        self.searchEdit.selectAll()

    def searchNext(self):
        text = self.searchEdit.text()
        if not text: return
        found = self.editor.find(text)
        if not found:
            self.editor.moveCursor(self.editor.textCursor().Start)
            found = self.editor.find(text)
            if not found:
                InfoBar.warning("検索", f"'{text}' は見つかりませんでした。", parent=self)

    def searchPrev(self):
        text = self.searchEdit.text()
        if not text: return
        found = self.editor.find(text, QTextEdit.FindBackward)
        if not found:
            self.editor.moveCursor(self.editor.textCursor().End)
            found = self.editor.find(text, QTextEdit.FindBackward)

    def newFile(self):
        self.editor.clear()
        self.currentFile = None
        self.showSuccess("新規ファイルを作成しました")

    def openFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "Text Files (*.txt);;Python Files (*.py);;All Files (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self.editor.setPlainText(f.read())
                self.currentFile = path
                self.showSuccess(f"開きました: {path}")
            except Exception as e:
                self.showError(str(e))

    def saveFile(self):
        if not self.currentFile:
            path, _ = QFileDialog.getSaveFileName(self, "保存", "", "Text Files (*.txt);;All Files (*)")
            if not path: return
            self.currentFile = path
        
        try:
            with open(self.currentFile, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.showSuccess(f"保存しました: {self.currentFile}")
        except Exception as e:
            self.showError(str(e))

    def showSuccess(self, msg):
        InfoBar.success(title='成功', content=msg, orient=Qt.Horizontal, 
                        isClosable=True, position=InfoBarPosition.TOP, parent=self)

    def showError(self, msg):
        InfoBar.error(title='エラー', content=msg, orient=Qt.Horizontal, 
                      isClosable=True, position=InfoBarPosition.TOP, parent=self)


class SettingInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SettingInterface")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        title = QLabel("設定")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        desc = QLabel("外観設定")
        desc.setFont(QFont("Segoe UI", 12))
        desc.setStyleSheet("color: gray;")
        layout.addWidget(desc)
        
        layout.addSpacing(10)

        btn_theme = PushButton("テーマを切り替える (ライト / ダーク)", self)
        btn_theme.clicked.connect(self.toggleTheme)
        btn_theme.setFixedWidth(250)
        layout.addWidget(btn_theme)
        
        layout.addStretch(1)

    def toggleTheme(self):
        if qconfig.theme == Theme.DARK:
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.DARK)

class MainWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Fluent Notepad")
        self.resize(900, 650)
        
        icon_edit = get_icon("EDIT")
        icon_setting = get_icon("SETTING", "SETTINGS")

        self.editorInterface = EditorInterface(self)
        self.settingInterface = SettingInterface(self)

        self.addSubInterface(self.editorInterface, icon_edit, "編集", NavigationItemPosition.TOP)
        self.addSubInterface(self.settingInterface, icon_setting, "設定", NavigationItemPosition.BOTTOM)

if __name__ == "__main__":
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
