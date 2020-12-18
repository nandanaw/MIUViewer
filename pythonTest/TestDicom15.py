import sys

from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.util.misc import vtkGetDataRoot
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageMapToColors, vtkImageReslice
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkRenderer, \
    vtkRenderWindow, vtkRenderWindowInteractor, vtkCoordinate, vtkTextProperty, vtkTextMapper, vtkActor2D
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules import vtkRenderingVolumeOpenGL2, vtkRenderingFreeType

from math import floor, sqrt
from timeit import default_timer as timer

class MIUViewer:
    def __init__(self):
        VTK_DATA_ROOT = vtkGetDataRoot()
        self.reader = vtkDICOMImageReader()
        self.folder = "/Users/nandana/Downloads/image_ex"

        self.reader.SetDirectoryName(self.folder)
        self.reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter")
        self.reader.SetDataExtent(0, 63, 0, 63, 1, 93)
        self.reader.SetDataSpacing(3.2, 3.2, 1.5)
        self.reader.SetDataOrigin(0.0, 0.0, 0.0)
        self.reader.SetDataScalarTypeToUnsignedShort()
        self.reader.UpdateWholeExtent()
        self.reader.Update()

        self.center = self.calculate_center()

        self.axial = vtkMatrix4x4()
        self.axial.DeepCopy((1, 0, 0, self.center[0],
                        0, 1, 0, self.center[1],
                        0, 0, 1, self.center[2],
                        0, 0, 0, 1))

        self.coronal = vtkMatrix4x4()
        self.coronal.DeepCopy((1, 0, 0, self.center[0],
                          0, 0, 1, self.center[1],
                          0,-1, 0, self.center[2],
                          0, 0, 0, 1))

        self.sagittal = vtkMatrix4x4()
        self.sagittal.DeepCopy((0, 0,-1, self.center[0],
                           1, 0, 0, self.center[1],
                           0,-1, 0, self.center[2],
                           0, 0, 0, 1))

        self.oblique = vtkMatrix4x4()
        self.oblique.DeepCopy((1, 0, 0, self.center[0],
                          0, 0.866025, -0.5, self.center[1],
                          0, 0.5, 0.866025, self.center[2],
                          0, 0, 0, 1))

        self.img_reslice = vtkImageReslice()
        self.roi_reslice = vtkImageReslice()

        self.img_reslice.SetInputConnection(0, self.reader.GetOutputPort())
        self.img_reslice.SetOutputDimensionality(2)
        self.img_reslice.SetInterpolationModeToLinear()

        self.roi_reslice.SetInputConnection(0, self.reader.GetOutputPort())
        self.roi_reslice.SetOutputDimensionality(2)
        self.roi_reslice.SetInterpolationModeToLinear()

        self.set_orientation(self.axial)

        self.img_table = vtkLookupTable()
        self.roi_table = vtkLookupTable()
        self.window_level = vtkImageMapToWindowLevelColors()
        self.img_color = vtkImageMapToColors()
        self.roi_color = vtkImageMapToColors()

        self.img = self.map_img()
        self.roi = self.map_roi()

        self.px_coord_text_prop = vtkTextProperty()
        self.px_coord_text_mapper = vtkTextMapper()
        self.px_coord_text_actor = vtkActor2D()
        self.world_coord_text_prop = vtkTextProperty()
        self.world_coord_text_mapper = vtkTextMapper()
        self.world_coord_text_actor = vtkActor2D()
        self.usage_text_prop = vtkTextProperty()
        self.usage_text_mapper = vtkTextMapper()
        self.usage_text_actor = vtkActor2D()

        self.renderer = vtkRenderer()
        self.add_text()
        self.renderer.AddActor(self.img)
        self.renderer.AddActor(self.roi)

        self.renderer.SetBackground(0.2, 0.3, 0.4)

        self.window = vtkRenderWindow()
        self.window.AddRenderer(self.renderer)

        self.window.SetSize(1000, 1000)

        self.interactor_style = vtkInteractorStyleImage()
        self.interactor_style.SetInteractionModeToImageSlicing()

        self.interactor = vtkRenderWindowInteractor()
        self.interactor.SetInteractorStyle(self.interactor_style)
        self.window.SetInteractor(self.interactor)

        self.window_level.SetWindow(1000)
        self.window_level.SetLevel(200)
        self.window_level.Update()

        self.window.Render()

        self.interactor_style.AddObserver("MouseWheelForwardEvent", self.scroll_forward_callback)
        self.interactor_style.AddObserver("MouseWheelBackwardEvent", self.scroll_backward_callback)
        self.interactor_style.AddObserver("MouseMoveEvent", self.mouse_move_callback)
        self.interactor_style.AddObserver("KeyPressEvent", self.key_press_callback)
        self.interactor_style.AddObserver("LeftButtonPressEvent", self.left_press_callback)
        self.window.AddObserver("ModifiedEvent", self.window_mod_callback)

        self.actions = {"Slicing": 0, "Cursor": 0, "CurrentPos": -1, "LastPos": -1, "DoubleClick": 0}

    def get_extent(self): # get extent in format (xMin, xMax, yMin, yMax, zMin, zMax)
        return self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))

    def get_extent_max(self): # get maximum extent values in format (xMax, yMax, zMax)
        return self.get_extent()[1], self.get_extent()[3], self.get_extent()[5]

    def get_spacing(self): # get spacing in form (xSpacing, ySpacing, zSpacing)
        return self.reader.GetOutput().GetSpacing()

    def get_origin(self): # get origin in form (x0, y0, z0)
        return self.reader.GetOutput().GetOrigin()

    def calculate_center(self):
        (xMin, xMax, yMin, yMax, zMin, zMax) = self.get_extent()
        (xSpacing, ySpacing, zSpacing) = self.get_spacing()
        (x0, y0, z0) = self.get_origin()

        return [x0 + xSpacing * 0.5 * (xMin + xMax),
                y0 + ySpacing * 0.5 * (yMin + yMax),
                z0 + zSpacing * 0.5 * (zMin + zMax)]

    def set_orientation(self, orientation):
        self.img_reslice.SetResliceAxes(orientation)
        self.roi_reslice.SetResliceAxes(orientation)

    def get_orientation(self):
        return self.img_reslice.GetResliceAxes()

    def map_img(self): # greyscale lookup table
        self.img_table.SetRange(0, 2000) # image intensity range
        self.img_table.SetValueRange(0.0, 1.0) # from black to white
        self.img_table.SetSaturationRange(0.0, 0.0) # no color saturation
        self.img_table.SetRampToSQRT()
        self.img_table.Build()

        self.window_level.SetInputConnection(self.img_reslice.GetOutputPort())
        self.img_color.SetLookupTable(self.img_table)
        self.img_color.SetInputConnection(self.window_level.GetOutputPort())

        img_actor = vtkImageActor()
        img_actor.GetMapper().SetInputConnection(self.img_color.GetOutputPort())
        return img_actor

    def map_roi(self): # colored lookup table
        self.roi_table.SetNumberOfTableValues(2)
        self.roi_table.SetRange(0.0,1.0)
        self.roi_table.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
        self.roi_table.SetTableValue(1, 0.0, 1.0, 0.0, 1.0) # value, r, g, b, a
        self.roi_table.Build()

        self.roi_color.SetLookupTable(self.roi_table)
        self.roi_color.SetInputConnection(self.roi_reslice.GetOutputPort())

        roi_actor = vtkImageActor()
        roi_actor.GetMapper().SetInputConnection(self.roi_color.GetOutputPort())

        return roi_actor

    def add_text(self):
        self.px_coord_text_prop.SetFontFamilyToCourier()
        self.px_coord_text_prop.SetFontSize(20)
        self.px_coord_text_prop.SetVerticalJustificationToBottom()
        self.px_coord_text_prop.SetJustificationToLeft()

        self.px_coord_text_mapper.SetInput("Pixel Coordinates: (--, --)")
        self.px_coord_text_mapper.SetTextProperty(self.px_coord_text_prop)

        self.px_coord_text_actor.SetMapper(self.px_coord_text_mapper)
        self.px_coord_text_actor.SetPosition(500, 10)

        self.world_coord_text_prop.SetFontFamilyToCourier()
        self.world_coord_text_prop.SetFontSize(20)
        self.world_coord_text_prop.SetVerticalJustificationToBottom()
        self.world_coord_text_prop.SetJustificationToLeft()

        self.world_coord_text_mapper.SetInput("World Coordinates: (--, --)")
        self.world_coord_text_mapper.SetTextProperty(self.world_coord_text_prop)

        self.world_coord_text_actor.SetMapper(self.world_coord_text_mapper)
        self.world_coord_text_actor.SetPosition(500, 30)

        self.usage_text_prop.SetFontFamilyToCourier()
        self.usage_text_prop.SetFontSize(14)
        self.usage_text_prop.SetVerticalJustificationToTop()
        self.usage_text_prop.SetJustificationToLeft()

        self.usage_text_mapper.SetInput("- Slice with mouse wheel\n"
                                        "- Zoom with pressed right\n"
                                        "  mouse button while dragging\n"
                                        "- Press i to toggle cursor line on/off")
        self.usage_text_mapper.SetTextProperty(self.usage_text_prop)

        self.usage_text_actor.SetMapper(self.usage_text_mapper)
        self.usage_text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
        self.usage_text_actor.GetPositionCoordinate().SetValue(0.05, 0.95)

        self.renderer.AddActor2D(self.px_coord_text_actor)
        self.renderer.AddActor2D(self.world_coord_text_actor)
        self.renderer.AddActor2D(self.usage_text_actor)

    def increment_slice(self, inc, reslice_axes):
        x_inc = y_inc = z_inc = 0
        upperBound = lowerBound = 0
        center = self.center
        (x_spacing, y_spacing, z_spacing) = self.get_spacing()
        (x_max, y_max, z_max) = self.get_extent_max()

        i = -1

        if reslice_axes == self.sagittal:
            x_inc = inc*x_spacing
            upperBound = floor(x_max*x_spacing)
            i = 0
        elif reslice_axes == self.coronal:
            y_inc = inc*y_spacing
            upperBound = floor(y_max*y_spacing)
            i = 1
        elif reslice_axes == self.axial:
            z_inc = inc*z_spacing
            upperBound = floor(z_max*z_spacing)
            i = 2

        elif reslice_axes == self.oblique:
            pass
        else:
            sys.stderr.write("ERROR: Invalid view orientation")
            exit(1)

        # slice through image by changing center
        if (inc < 0 and center[i] > lowerBound) or (inc > 0 and center[i] < upperBound):
            self.center = (center[0]+x_inc, center[1]+y_inc, center[2]+z_inc)

    def load(self, img, roi, alpha, window_size, window_val, level_val, n_center):
        if self.img != img:
            self.renderer.RemoveViewProp(self.img)
            self.renderer.AddActor(img)
        if self.roi != roi:
            self.renderer.RemoveViewProp(self.roi)
            self.renderer.AddActor(roi)

        self.window.SetSize(window_size)
        roi.SetOpacity(alpha)
        self.window_level.SetWindow(window_val)
        self.window_level.SetLevel(level_val)
        self.center[0] = n_center[0]
        self.center[1] = n_center[1]
        self.center[2] = n_center[2]
        self.get_orientation().SetElement(0, 3, self.center[0])
        self.get_orientation().SetElement(1, 3, self.center[1])
        self.get_orientation().SetElement(2, 3, self.center[2])
        self.window.Render()

    def scroll_forward_callback(self, obj, event):
        matrix = self.get_orientation()
        self.increment_slice(1, matrix)

        matrix.SetElement(0, 3, self.center[0])
        matrix.SetElement(1, 3, self.center[1])
        matrix.SetElement(2, 3, self.center[2])

        #print("scrolling forward....")
        #print(center)
        self.mouse_move_callback(obj, event)
        self.window.Render()

    def scroll_backward_callback(self, obj, event):
        matrix = self.get_orientation()
        self.increment_slice(-1, matrix)

        matrix.SetElement(0, 3, self.center[0])
        matrix.SetElement(1, 3, self.center[1])
        matrix.SetElement(2, 3, self.center[2])

        #print("scrolling backward....")
        #print(center)

        self.mouse_move_callback(obj, event)
        self.window.Render()

    def mouse_move_callback(self, obj, event):
        (mouseX, mouseY) = self.interactor.GetEventPosition()
        Z_OFFSET = 0
        bounds = self.img.GetMapper().GetInput().GetBounds()

        testCoord = vtkCoordinate()
        testCoord.SetCoordinateSystemToDisplay()
        testCoord.SetValue(mouseX, mouseY, 0) # TODO: set 3rd val to slice num
        (posX, posY, _) = testCoord.GetComputedWorldValue(self.renderer)
        posZ = self.center[2]

        inBounds = True;
        if posX < bounds[0] or posX > bounds[1] or posY < bounds[2] or posY > bounds[3]:
            inBounds = False

        if inBounds:
            (xSpacing, ySpacing, zSpacing) = self.get_spacing()
            wMousePos = "Pixel Coordinates: (" + "{:d}".format(int((posX+self.center[0])/xSpacing)) + ", " + "{:d}".format(int((posY+self.center[1])/ySpacing)) + ", " + "{:d}".format(int(posZ-Z_OFFSET)) + ")"
            pMousePos = "??? Coordinates: (" + "{:.2f}".format(mouseX) + ", " + "{:.2f}".format(mouseY) + ")"
            self.world_coord_text_mapper.SetInput(wMousePos)
            self.px_coord_text_mapper.SetInput(pMousePos)

            self.window.Render()

        self.interactor_style.OnMouseMove()

    def key_press_callback(self, obj, event):
        key = self.interactor.GetKeySym()
        if(key == "t"):
            if(self.actions["Cursor"] == 0):
                self.window.HideCursor()
                self.actions["Cursor"] = 1
            elif(self.actions["Cursor"] == 1):
                self.window.ShowCursor()
                self.actions["Cursor"] = 0
        if(key == "n"):
            self.load(viewer.img, viewer.roi, 0.8, (500, 500), 1000, 200, [169.66796875, 169.66796875, 107.0])
            self.start_interaction()


    def left_press_callback(self, obj, event):
        diff = None
        self.actions["CurrentPos"] = timer()

        if self.actions["LastPos"] != -1:
            diff = self.actions["CurrentPos"] - self.actions["LastPos"]

        if diff is not None and diff < 0.5: # valid double click
            print("double clicked")
            print(self.center)

        self.actions["LastPos"] = self.actions["CurrentPos"]
        self.interactor_style.OnLeftButtonDown()

    def window_mod_callback(self, obj, event):
        width = self.window.GetSize()[0]
        self.px_coord_text_actor.SetPosition(width-550, 10)
        self.world_coord_text_actor.SetPosition(width-550, 30)

        self.window.Render()

    def start_interaction(self):
        self.interactor.Start()



if __name__ == '__main__':
    viewer = MIUViewer()
    viewer.start_interaction()
