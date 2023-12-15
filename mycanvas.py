from IPython.external.qt_for_kernel import QtCore
from PyQt5 import QtOpenGL
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton

from OpenGL.GL import *
from hetool.include.hetool import Hetool
from hetool.he.hemodel import HeModel
from hetool.he.hecontroller import HeController
from hetool.compgeom.tesselation import Tesselation
from hetool.geometry.point import Point
from hetool.geometry.segments.line import Line
import math
import sys
import json

class InputDialog(QDialog):
    def __init__(self, title="MeshDialog", labels=["Texto..."], dialogs=1):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowModality(Qt.ApplicationModal)

        self.lineEdits = [None] * dialogs
        self.layout = QVBoxLayout()
        for i in range(dialogs):
            self.lineEdits[i] = QLineEdit()  
            self.layout.addWidget(QLabel("{}:".format(labels[i])))
            self.layout.addWidget(self.lineEdits[i])

        self.pushButton = QPushButton("Confirmar")
        self.pushButton.clicked.connect(self.accept)
        self.layout.addWidget(self.pushButton)

        self.setLayout(self.layout)

class MyCanvas(QtOpenGL.QGLWidget):
    def __init__(self):
        # Initializing the canvas
        super(MyCanvas, self).__init__()
        self.malha = []
        self.m_w = 0
        self.m_h = 0
        self.m_L = -1000.0
        self.m_R = 1000.0
        self.m_B = -1000.0
        self.m_T = 1000.0
        self.list = None

        self.m_collector = AppCurveCollector()
        self.m_state = "View"
        self.m_mousePt = QtCore.QPointF(0.0, 0.0)
        self.m_heTol = 10.0
        

        self.m_pt0 = QtCore.QPointF(0.0, 0.0)
        self.m_pt1 = QtCore.QPointF(0.0, 0.0)
        self._last_mesh_spacing = 1.0
        self._temp = 100.0
        self._var = 1.2
        self._punch = -1000.0
        self._punch_particles = 10
        self._mass = 7850.0
        self._density = 210000000000.0
        self.m_hmodel = HeModel()
        self.m_controller = HeController(self.m_hmodel)



    def initializeGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glEnable(GL_LINE_SMOOTH)
        self.list = glGenLists(1)


    # Resizing uses the Hetool to check for an empty model
    def resizeGL(self, _w, _h):
        self.m_w = _w
        self.m_h = _h

        if Hetool.isEmpty():
            self.scaleWorldWindow(1.0)
        else:
            self.fitWorldToViewport()

        glViewport(0, 0, _w, _h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    # Paint GL needs to iterate over every entity in the model
    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        # Draw Patches
        glShadeModel(GL_SMOOTH)
        patches = Hetool.getPatches()
        for patch in patches:
            if patch.isDeleted:
                glColor3f(1.0, 1.0, 1.0)
            elif patch.isSelected():
                glColor3f(1.00, 0.75, 0.75)
            else:
                glColor3f(0.75, 0.75, 0.75)

            triangs = Hetool.tessellate(patch)
            for triangle in triangs:
                glBegin(GL_TRIANGLES)
                for pt in triangle:
                    glVertex2d(pt.getX(), pt.getY())
                glEnd()

        # Draw Segments
        segments = Hetool.getSegments()
        for segment in segments:
            pts = segment.getPointsToDraw()
            if segment.isSelected():
                glColor3f(00.0, 0.0, 1.0)
            else:
                glColor3f(0.0, 0.0, 1.0)
            glBegin(GL_LINE_STRIP)
            for pt in pts:
                glVertex2f(pt.getX(), pt.getY())
            glEnd()

        # Draw Points
        points = Hetool.getPoints()
        for point in points:
            if point.isSelected():
                glColor3f(0.0, 1.0, 0.0)
            else:
                glColor3f(0.0, 1.0, 0.0)
            glPointSize(3)
            glBegin(GL_POINTS)
            glVertex2f(point.getX(), point.getY())
            glEnd()

        # Draw curves that are being collected
        if self.m_collector.isActive():
            tempCurve = self.m_collector.getCurveToDraw()
            if len(tempCurve) > 0:
                glColor3f(1.0, 0.0, 0.0)
                glBegin(GL_LINE_STRIP)
                for pti in tempCurve:
                    glVertex2f(pti[0], pti[1])

                glEnd()

    # Needs to check for emptiness and access the bounding box
    def fitWorldToViewport(self):
        if Hetool.isEmpty():
            return

        self.m_L, self.m_R, self.m_B, self.m_T = Hetool.getBoundBox()
        self.scaleWorldWindow(1.1)

    def scaleWorldWindow(self, _scaleFactor):
        cx = 0.5 * (self.m_L + self.m_R)
        cy = 0.5 * (self.m_B + self.m_T)
        dx = (self.m_R - self.m_L) * _scaleFactor
        dy = (self.m_T - self.m_B) * _scaleFactor

        ratioVP = self.m_h / self.m_w
        if dy > dx * ratioVP:
            dx = dy / ratioVP
        else:
            dy = dx * ratioVP

        self.m_L = cx - 0.5 * dx
        self.m_R = cx + 0.5 * dx
        self.m_B = cy - 0.5 * dy
        self.m_T = cy + 0.5 * dy

        self.m_heTol = 0.005 * (dx + dy)

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.m_L, self.m_R, self.m_B, self.m_T, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def setState(self, _state, _varg="default"):
        self.m_collector.deactivateCollector()
        if _state == "Collect":
            self.m_state = "Collect"
            self.m_collector.activateCollector(_varg)


    def mouseMoveEvent(self, _event):
        pt = _event.pos()
        self.m_mousePt = pt
        if self.m_collector.isActive():
            pt = self.convertPtCoordsToUniverse(pt)
            self.m_collector.update(pt.x(), pt.y())
            self.update()


    # Uses the Hetool to:
    # - Snap coordinate to existing elements
    # - Add a finalized segment to the model
    # - Use click coord to select a patch
    def mouseReleaseEvent(self, _event):
        pt = _event.pos()
        if self.m_collector.isActive():
            pt_univ = self.convertPtCoordsToUniverse(pt)
            snaped, xs, ys = Hetool.snapToPoint(
                pt_univ.x(), pt_univ.y(), self.m_heTol)
            if snaped:
                isComplete = self.m_collector.collectPoint(xs, ys)
            else:
                snaped, xs, ys = Hetool.snapToSegment(
                    pt_univ.x(), pt_univ.y(), self.m_heTol)
                if snaped:
                    isComplete = self.m_collector.collectPoint(xs, ys)
                else:
                    isComplete = self.m_collector.collectPoint(
                        pt_univ.x(), pt_univ.y())


            if isComplete:
                self.setMouseTracking(False)
                curve = self.m_collector.getCurve()
                heSegment = []
                for pt in curve:
                    heSegment.append(pt[0])
                    heSegment.append(pt[1])
                Hetool.insertSegment(heSegment)
        
                self.update()
            else:
                self.setMouseTracking(True)

        if self.m_state == "Select":
            pt_univ = self.convertPtCoordsToUniverse(pt)
            Hetool.selectPick(pt_univ.x(), pt_univ.y(), self.m_heTol)
            self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.scaleWorldWindow(0.9)
        else:
            self.scaleWorldWindow(1.1)
        self.update()

    def convertPtCoordsToUniverse(self, _pt):
        dX = self.m_R - self.m_L
        dY = self.m_T - self.m_B
        mX = _pt.x() * 1 * dX / self.m_w
        mY = (self.m_h - _pt.y() * 1) * dY / self.m_h
        x = self.m_L + mX
        y = self.m_B + mY

        return QtCore.QPointF(x, y)
               
    def gerarMalha(self):
        if Hetool.isEmpty():
            print("Nao ha patches")
            return
        default = 1.0
        dialog = InputDialog(title="Definir grade", labels=["Quanto maior o valor, menor a grade"])
        dialog.exec()
        if dialog.result() == 1:
            try:
                default = float(dialog.lineEdits[0].text())
            except:
                default = 1.0
        self._last_mesh_spacing = default

        if not (Hetool.isEmpty()):
            patches = Hetool.getPatches()
            print("Gerando malha...")

            for pat in patches:
                pts = pat.getPoints()
                x_min = pts[0].getX()
                x_max = x_min
                y_min = pts[0].getY()
                y_max = y_min
                for i in range(1, len(pts)):
                    if pts[i].getX() < x_min:
                        x_min = pts[i].getX()
                    if pts[i].getX() > x_max:
                        x_max = pts[i].getX()
                    if pts[i].getY() < y_min:
                        y_min = pts[i].getY()
                    if pts[i].getY() > y_max:
                        y_max = pts[i].getY()
                x = []
                y = []
                x_min += default
                y_min += default
                while x_min < x_max:
                    x.append(x_min)
                    x_min += default
                while y_min < y_max:
                    y.append(y_min)
                    y_min += default
                for i in range(len(x)):
                    for j in range(len(y)):
                        point = Point(x[i], y[j])
                        if pat.isPointInside(point):
                            self.malha.append(point)
                            Hetool.insertPoint(point)
                      

        self.update()
        self.repaint()
  
    def temperatura(self):
            dialog = InputDialog(title="Defina o calor", labels=["Defina o calor ao redor do Objeto", "Defina a variação de calor"], dialogs=2)
            dialog.exec()
            if dialog.result() == 1:
                try:
                    self._temp = float(dialog.lineEdits[0].text())
                    self._var = float(dialog.lineEdits[1].text())
                except:
                    self._temp = 100.0
                    self._var = 1.2

    def movimento(self):
        dialog = InputDialog(
            title="Defina a força",
            labels=[
                "Define a força aplicada",
                "Quantidade de particulas afetadas de inicio",
                "Defina a massa do objeto",
                "Defina a densidade do objeto"
            ],
            dialogs=4
        )
        dialog.exec()
        if dialog.result() == 1:
            try:
                self._punch = float(dialog.lineEdits[0].text())
                self._punch_particles = int(dialog.lineEdits[2].text())
                self._mass = float(dialog.lineEdits[3].text())
                self._density = float(dialog.lineEdits[4].text())
            except:
                self._punch = -1000.0
                self._punch_particles = 10
                self._mass = 7850.0
                self._density = 210000000000.0
                
    def __get_point_index1(self, _coords, _x, _y):
        for i, coord in enumerate(_coords):
            if coord[0] == _x and coord[1] == _y:
                return i + 1
        return 0

    def exportar(self):
        lower_y = sys.maxsize
        upper_y = -sys.maxsize
        lower_x = sys.maxsize
        upper_x = -sys.maxsize

        _json = []
        for point in self.malha:
            if (point.getY() < lower_y):
                lower_y = point.getY()
            if (point.getY() > upper_y):
                upper_y = point.getY()
            if (point.getX() < lower_x):
                lower_x = point.getX()
            if (point.getX() > upper_x):
                upper_x = point.getX()
            _json.append({"x": point.getX(), "y": point.getY()})

        y_adjust = -1 * lower_y
        x_adjust = -1 * lower_x

        dem_output = {"coords": []}

        for point in _json:
            point["x"] = int(int(point["x"] + x_adjust) / self._last_mesh_spacing)
            point["y"] = int(int(point["y"] + y_adjust) / self._last_mesh_spacing)
            dem_output["coords"].append([point["x"], point["y"]])

        len_x = 1
        len_y = 1
        for point in _json:
            if point["x"] > len_x:
                len_x = point["x"]
            if point["y"] > len_y:
                len_y = point["y"]

        mdf_output =  [[-2.0 for x in range(len_x + 1)] for y in range(len_y + 1)]

        for point in _json:
            mdf_output[point["y"]][point["x"]] = -1.0

        self._temp -= self._var
        len_i = len(mdf_output)
        for i in range(len_i):
            self._temp += self._var
            self._temp = round(self._temp, 2)
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] == -1.0:
                    if i == 0 or j == 0 or (i + 1) == len_i or (j + 1) == len_j:
                        mdf_output[i][j] = self._temp
                    else:
                        if i > 0 and mdf_output[i - 1][j] == -2.0:
                            mdf_output[i][j] = self._temp
                        if i + 1 < len_i and mdf_output[i + 1][j] == -2.0:
                            mdf_output[i][j] = self._temp
                        if j > 0 and mdf_output[i][j - 1] == -2.0:
                            mdf_output[i][j] = self._temp
                        if j + 1 < len_j and mdf_output[i][j + 1] == -2.0:
                            mdf_output[i][j] = self._temp

        connective =  [[0 for _ in range(5)] for _ in range(len(dem_output["coords"]))]
        len_i = len(mdf_output)
        for i in range(len_i):
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] != -2.0:
                    actual_point = self.__get_point_index1(dem_output["coords"], j, i)
                    amount_of_connections = 0
                    if i > 0 and mdf_output[i - 1][j] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j, i - 1)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if i + 1 < len_i and mdf_output[i + 1][j] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j, i + 1)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if j > 0 and mdf_output[i][j - 1] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j - 1, i)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    if j + 1 < len_j and mdf_output[i][j + 1] != -2.0:
                        _conected_point = self.__get_point_index1(dem_output["coords"], j + 1, i)
                        amount_of_connections += 1
                        connective[actual_point - 1][amount_of_connections] = _conected_point
                    connective[actual_point - 1][0] = amount_of_connections

        force = [[0.0 for _ in range(2)] for _ in range(len(dem_output["coords"]))]
        amount_force = self._punch_particles
        len_i = len(mdf_output)
        for i in range(len_i - 1, 0, -1):
            len_j = len(mdf_output[i])
            for j in range(len_j - 1, 0, -1):
                if mdf_output[i][j] != -2.0:
                    if amount_force > 0:
                        force[self.__get_point_index1(dem_output["coords"], j, i) - 1][0] = self._punch
                        amount_force -= 1
                    else:
                        break
            if amount_force <= 0:
                break

        resistence = [[0 for _ in range(2)] for _ in range(len(dem_output["coords"]))]
        amount_resistence = self._punch_particles
        len_i = len(mdf_output)
        for i in range(len_i):
            len_j = len(mdf_output[i])
            for j in range(len_j):
                if mdf_output[i][j] != -2.0:
                    if amount_resistence > 0:
                        resistence[self.__get_point_index1(dem_output["coords"], j, i) - 1][0] = 1
                        resistence[self.__get_point_index1(dem_output["coords"], j, i) - 1][1] = 1
                        amount_resistence -= 1
                    else:
                        break
            if amount_resistence <= 0:
                break

        dem_output["connective"] = connective
        dem_output["force"] = force
        dem_output["resistence"] = resistence
        dem_output["mass"] = self._mass
        dem_output["density"] = self._density

        with open("dem_input.json", "w") as file:
            json.dump(dem_output, file)

        with open("mdf_input.json", "w") as file:
            json.dump(mdf_output, file)

   

class AppCurveCollector():
    def __init__(self):
        # Initialization
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    def isActive(self):
        return self.m_isActive

    # Activation w/ curve type
    def activateCollector(self, _curve):
        self.m_isActive = True
        self.m_curveType = _curve


    # Deactivation clearing the collector
    def deactivateCollector(self):
        self.m_isActive = False
        self.m_curveType = "None"
        self.m_ctrlPts = []
        self.m_tempCurve = []

    # Point Collection (depends on curve type and points collected)
    def collectPoint(self, _x, _y):
        isComplete = False
        if self.m_isActive:
            if self.m_curveType == "Line":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "Bezier2":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 2:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True
            elif self.m_curveType == "Rectangle":
                if len(self.m_ctrlPts) == 0:
                    self.m_ctrlPts.append([_x, _y])
                elif len(self.m_ctrlPts) == 1:
                    self.m_ctrlPts.append([_x, _y])
                    isComplete = True        

        return isComplete

    # Curve (temporary and finalized)
    def getCurveToDraw(self):
        return self.m_tempCurve

    def getCurve(self):
        if self.m_curveType == "Line":
            curve = self.m_ctrlPts
        else:
            curve = self.m_tempCurve
        
        self.m_ctrlPts = []
        self.m_tempCurve = []
        return curve

    # Update temporary curve (mouse tracking)
    def update(self, _x, _y):
        if self.m_curveType == "Line":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
        elif self.m_curveType == "Bezier2":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [self.m_ctrlPts[0], [_x, _y]]
            elif len(self.m_ctrlPts) == 2:
                nSampling = 20
                self.m_tempCurve = []
                for ii in range(nSampling+1):
                    t = ii/nSampling
                    ptx = (1-t)**2*self.m_ctrlPts[0][0] + \
                        2*(1-t)*t*_x + t**2*self.m_ctrlPts[1][0]
                    pty = (1-t)**2*self.m_ctrlPts[0][1] + \
                        2*(1-t)*t*_y + t**2*self.m_ctrlPts[1][1]
                    self.m_tempCurve.append([ptx, pty])
        elif self.m_curveType == "Rectangle":
            if len(self.m_ctrlPts) == 0:
                pass
            elif len(self.m_ctrlPts) == 1:
                self.m_tempCurve = [
                    self.m_ctrlPts[0], 
                    [self.m_ctrlPts[0][0], _y], 
                    [_x, _y],
                    [_x, self.m_ctrlPts[0][1]],
                    self.m_ctrlPts[0]
                ]
    