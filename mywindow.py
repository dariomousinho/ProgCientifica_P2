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
        generateMesh = QAction("Gerar malha", self)
        tb.addAction(generateMesh)
        temperatura = QAction("Temperatura", self)
        tb.addAction(temperatura)
        forca = QAction("Movimento", self)
        tb.addAction(forca)
        export = QAction("Exportar", self)
        tb.addAction(export)

        tb.actionTriggered[QAction].connect(self.tbpressed)


    # ToolBar Pressed Function
    def tbpressed(self, _action):
        if _action.text() == "Adicionar reta":
            self.m_canvas.setState("Collect", "Line")
        elif _action.text() == "Adicionar bezier":
            self.m_canvas.setState("Collect", "Bezier2")
        elif _action.text() == "Adicionar retangulo":
            self.m_canvas.setState("Collect", "Rectangle")
        elif _action.text() == "Gerar malha":
            self.m_canvas.gerarMalha()
        elif _action.text() == "Temperatura":
            self.m_canvas.temperatura()
        elif _action.text() == "Forca":
            self.m_canvas.movimento()
        elif _action.text() == "Exportar":
            self.m_canvas.exportar()