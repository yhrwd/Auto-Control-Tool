import sys
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton
from PyQt5.QtCore import QSize  # 添加这一行

class SmoothResizeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 200, 200)
        
        resize_button = QPushButton("Resize", self)
        resize_button.clicked.connect(self.animate_resize)
        resize_button.move(50, 50)

    def animate_resize(self):
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(1000)
        self.animation.setStartValue(QRect(self.pos(), self.size()))
        self.animation.setEndValue(QRect(self.pos(), QSize(self.width() + 100, self.height() + 100)))
        self.animation.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmoothResizeWindow()
    window.show()
    sys.exit(app.exec_())
