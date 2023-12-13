from PyQt5.QtGui import QIcon
from mycanvas import *

class MyWindow(QMainWindow):
    def __init__(self):
        # Window initialization
        super(MyWindow, self).__init__()
        self.setGeometry(150, 100, 600, 400)
        self.setWindowTitle("MyGLDrawer")
        self.m_canvas = MyCanvas()
        self.setCentralWidget(self.m_canvas)

        # ToolBar Actions
        tb = self.addToolBar("ToolBar")

        addLine = QAction("Adicionar reta", self)
        tb.addAction(addLine)
        addBezier2 = QAction("Adicionar bezier", self)
        tb.addAction(addBezier2)
        addRectangle = QAction("Adicionar retangulo", self)
        tb.addAction(addRectangle)
        tb.actionTriggered[QAction].connect(self.tbpressed)


    # ToolBar Pressed Function
    def tbpressed(self, _action):
        if _action.text() == "Adicionar reta":
            self.m_canvas.setState("Collect", "Line")
        elif _action.text() == "Adicionar bezier":
            self.m_canvas.setState("Collect", "Bezier2")
        elif _action.text() == "Adicionar retangulo":
            self.m_canvas.setState("Collect", "Rectangle")
