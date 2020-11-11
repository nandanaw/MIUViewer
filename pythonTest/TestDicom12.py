#!/usr/bin/env python

# This example shows how to load a 3D image into VTK and then reformat
# that image into a different orientation for viewing.  It uses
# vtkImageReslice for reformatting the image, and uses vtkImageActor
# and vtkInteractorStyleImage to display the image.  This InteractorStyle
# forces the camera to stay perpendicular to the XY plane.

import sys, os
import vtk
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.util.misc import vtkGetDataRoot
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkImagingCore import vtkImageMapToColors, vtkImageReslice
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkRenderer, \
    vtkRenderWindow, vtkRenderWindowInteractor, vtkCoordinate, vtkTextProperty, vtkTextMapper, vtkActor2D
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules.vtkCommonDataModel import vtkImageData
from math import floor

class MIUViewer:
    def __init__(self):
        self.window_level = vtkImageMapToWindowLevelColors()
        self.renderer = vtkRenderer()
        self.window = vtkRenderWindow()
        #self.center =

# window size should be a "constant"
def load(img, roi, alpha, window_size, window, level, center, self_renderer,
         self_window, self_window_level, self_center, self_matrix):
    self_renderer.RemoveAllViewProps()
    self_renderer.AddActor(img)
    self_renderer.AddActor(roi)
    self_window.SetSize(window_size)
    roi.SetOpacity(alpha)
    self_window_level.SetWindow(window)
    self_window_level.SetLevel(level)
    self_center[0] = center[0]
    self_center[1] = center[1]
    self_center[2] = center[2]
    self_matrix.SetElement(0, 3, self_center[0])
    self_matrix.SetElement(1, 3, self_center[1])
    self_matrix.SetElement(2, 3, self_center[2])
    self_window.Render()

"""
Load 
   > param1 - imageA, roi1, alpha, window size, window/level, initial center

"""

VTK_DATA_ROOT = vtkGetDataRoot()
folder = "/Users/nandana/Downloads/image_ex"

# Start by loading some data.
reader = vtkDICOMImageReader()
reader.SetDirectoryName(folder)
reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter")
reader.SetDataExtent(0, 63, 0, 63, 1, 93)
reader.SetDataSpacing(3.2, 3.2, 1.5)
reader.SetDataOrigin(0.0, 0.0, 0.0)
reader.SetDataScalarTypeToUnsignedShort()
reader.UpdateWholeExtent()

# Calculate the center of the volume
reader.Update()
(xMin, xMax, yMin, yMax, zMin, zMax) = reader.GetExecutive().GetWholeExtent(reader.GetOutputInformation(0))
(xSpacing, ySpacing, zSpacing) = reader.GetOutput().GetSpacing()
(x0, y0, z0) = reader.GetOutput().GetOrigin()

print((xMin, xMax, yMin, yMax, zMin, zMax))
print((xSpacing, ySpacing, zSpacing))
print((x0, y0, z0))

center = [x0 + xSpacing * 0.5 * (xMin + xMax),
          y0 + ySpacing * 0.5 * (yMin + yMax),
          z0 + zSpacing * 0.5 * (zMin + zMax)]
print(center)

# Matrices for axial, coronal, sagittal, oblique view orientations
axial = vtkMatrix4x4()
axial.DeepCopy((1, 0, 0, center[0],
                0, 1, 0, center[1],
                0, 0, 1, center[2],
                0, 0, 0, 1))

coronal = vtkMatrix4x4()
coronal.DeepCopy((1, 0, 0, center[0],
                  0, 0, 1, center[1],
                  0,-1, 0, center[2],
                  0, 0, 0, 1))

sagittal = vtkMatrix4x4()
sagittal.DeepCopy((0, 0,-1, center[0],
                   1, 0, 0, center[1],
                   0,-1, 0, center[2],
                   0, 0, 0, 1))

oblique = vtkMatrix4x4()
oblique.DeepCopy((1, 0, 0, center[0],
                  0, 0.866025, -0.5, center[1],
                  0, 0.5, 0.866025, center[2],
                  0, 0, 0, 1))

# Extract a slice in the desired orientation
reslice = vtkImageReslice()
reslice.SetInputConnection(0, reader.GetOutputPort())
reslice.SetOutputDimensionality(2)
#reslice.SetMagnificationFactors(2, 0, 0)
reslice.SetResliceAxes(axial)

reslice2 = vtkImageReslice()
reslice2.SetInputConnection(0, reader.GetOutputPort())
reslice2.SetOutputDimensionality(2)
reslice2.SetResliceAxes(reslice.GetResliceAxes())


reslice.SetInterpolationModeToLinear()
reslice2.SetInterpolationModeToLinear()

image = reader.GetOutput()
roiData = vtkImageData()
roiData.DeepCopy(image)
extent = roiData.GetExtent()

print("generating ROI...")

"""
for i in range(extent[0], extent[1]):
    for j in range(extent[2], extent[3]):
        for k in range(extent[4], extent[5]):
            if image.GetScalarComponentAsDouble(i, j, k, 0) > -100:
                roiData.SetScalarComponentFromDouble(i, j, k, 0, 1.0)
                #roiData.SetScalarComponentFromDouble(0, i, j, k, 1)
                
            else:   #just in case
                roiData.SetScalarComponentFromDouble(i, j, k, 0, 0.0)
                #roiData.SetScalarComponentFromDouble(0, i, j, k, 0.0)
"""

print("creating LookupTable...")

table = vtkLookupTable()
table.SetNumberOfTableValues(2)
table.SetRange(0.0,1.0)

table.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
table.SetTableValue(1, 0.0, 1.0, 0.0, 1.0) # value, r, g, b, a

table.Build()

# Create a greyscale lookup table
table2 = vtkLookupTable()
table2.SetRange(0, 2000) # image intensity range
table2.SetValueRange(0.0, 1.0) # from black to white
table2.SetSaturationRange(0.0, 0.0) # no color saturation
table2.SetRampToSQRT()
table2.Build()

# Map the image through the lookup table
print("mapping colors...")

windowLevel = vtkImageMapToWindowLevelColors()
windowLevel.SetInputConnection(reslice2.GetOutputPort())

color = vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(reslice.GetOutputPort())

color2 = vtkImageMapToColors()
color2.SetLookupTable(table2)
color2.SetInputConnection(windowLevel.GetOutputPort())

# Display the image
actor = vtkImageActor()
actor.GetMapper().SetInputConnection(color.GetOutputPort())

original = vtkImageActor()
original.GetMapper().SetInputConnection(color2.GetOutputPort())

print(actor.GetInput().GetExtent())

# ADD TEXT PROPS
coordTextProp = vtkTextProperty()
coordTextProp.SetFontFamilyToCourier()
coordTextProp.SetFontSize(20)
coordTextProp.SetVerticalJustificationToBottom()
coordTextProp.SetJustificationToLeft()

coordTextMapper = vtkTextMapper()
coordTextMapper.SetInput("Pixel Coordinates: (--, --)")
coordTextMapper.SetTextProperty(coordTextProp)

coordTextActor = vtkActor2D()
coordTextActor.SetMapper(coordTextMapper)
coordTextActor.SetPosition(500, 10)

worldCoordTextProp = vtkTextProperty()
worldCoordTextProp.SetFontFamilyToCourier()
worldCoordTextProp.SetFontSize(20)
worldCoordTextProp.SetVerticalJustificationToBottom()
worldCoordTextProp.SetJustificationToLeft()

worldCoordTextMapper = vtkTextMapper()
worldCoordTextMapper.SetInput("World Coordinates: (--, --)")
worldCoordTextMapper.SetTextProperty(worldCoordTextProp)

worldCoordTextActor = vtkActor2D()
worldCoordTextActor.SetMapper(worldCoordTextMapper)
worldCoordTextActor.SetPosition(500, 30)

usageTextProp = vtkTextProperty()
usageTextProp.SetFontFamilyToCourier()
usageTextProp.SetFontSize(14)
usageTextProp.SetVerticalJustificationToTop()
usageTextProp.SetJustificationToLeft()

usageTextMapper = vtkTextMapper()
usageTextMapper.SetInput("- Slice with mouse wheel\n- Zoom with pressed right\n  mouse button while dragging\n- Press i to toggle cursor line on/off")
usageTextMapper.SetTextProperty(usageTextProp)

usageTextActor = vtkActor2D()
usageTextActor.SetMapper(usageTextMapper)
usageTextActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
usageTextActor.GetPositionCoordinate().SetValue(0.05, 0.95)

renderer = vtkRenderer()
renderer.AddActor(original)
renderer.AddActor(actor)
renderer.AddActor2D(coordTextActor)
renderer.AddActor2D(usageTextActor)
renderer.AddActor2D(worldCoordTextActor)

renderer.SetBackground(0.2, 0.3, 0.4)

window = vtkRenderWindow()
window.AddRenderer(renderer)
window.SetSize(1000, 1000)

renderer.SetBackground(0.2, 0.3, 0.4)

# Set up the interaction
interactorStyle = vtkInteractorStyleImage()
interactorStyle.SetInteractionModeToImageSlicing()

interactor = vtkRenderWindowInteractor()
interactor.SetInteractorStyle(interactorStyle)
window.SetInteractor(interactor)

windowLevel.SetWindow(1000)
windowLevel.SetLevel(200)
windowLevel.Update()

window.Render()


input()
print("Loading params 1")
load(original, actor, 0.0, (500, 500), 1000, -1000, (169.66796875, 169.66796875, 107.0),
     renderer, window, windowLevel, center, reslice.GetResliceAxes())

input()
print("Loading params 2")
load(original, actor, 0.5, (700, 1000), 1000, 200, (169.66796875, 169.66796875, 0.0),
     renderer, window, windowLevel, center, reslice.GetResliceAxes())


# Create callbacks for slicing the image
actions = {}
actions["Slicing"] = 0
actions["Cursor"] = 0

def IncrementSlice(inc, resliceAxes):
    global center
    xInc = yInc = zInc = 0
    upperBound = lowerBound = 0
    i = -1

    if resliceAxes == sagittal:
        xInc = inc*xSpacing
        upperBound = floor(xMax*xSpacing)
        i = 0
    elif resliceAxes == coronal:
        yInc = inc*ySpacing
        upperBound = floor(yMax*ySpacing)
        i = 1
    elif resliceAxes == axial:
        zInc = inc*zSpacing
        upperBound = floor(zMax*zSpacing)
        i = 2
    elif resliceAxes == oblique:
        pass
    else:
        sys.stderr.write("ERROR: Invalid view orientation")
        exit(1)

    # slice through image by changing center
    if (inc < 0 and center[i] > lowerBound) or (inc > 0 and center[i] < upperBound):
        center = (center[0]+xInc, center[1]+yInc, center[2]+zInc)


def ButtonCallback(obj, event):
    if event == "MiddleButtonPressEvent":
        actions["Slicing"] = 1
    else:
        actions["Slicing"] = 0

def ButtonCallback2(obj, event):
    if event == "MouseWheelForwardEvent":
        actions["Slicing"] = 2
    else:
        actions["Slicing"] = 0

def ButtonCallback3(obj, event):
    if event == "MouseWheelBackwardEvent":
        actions["Slicing"] = 3
    else:
        actions["Slicing"] = 0

def MouseMoveCallback(obj, event):
    (mouseX, mouseY) = interactor.GetEventPosition()
    bounds = actor.GetMapper().GetInput().GetBounds()

    testCoord = vtkCoordinate()
    testCoord.SetCoordinateSystemToDisplay()
    testCoord.SetValue(mouseX, mouseY, 0);

    (posX, posY, posZ) = testCoord.GetComputedWorldValue(renderer)

    inBounds = True;
    if posX < bounds[0] or posX > bounds[1] or posY < bounds[2] or posY > bounds[3]:
        inBounds = False

    if inBounds:
        wMousePos = "World Coordinates: (" + "{:.2f}".format(posX) + ", " + "{:.2f}".format(posY) + ", " + "{:.2f}".format(posZ) + ")"
        pMousePos = "Pixel Coordinates: (" + "{:.2f}".format(mouseX) + ", " + "{:.2f}".format(mouseY) + ")"
        worldCoordTextMapper.SetInput(wMousePos)
        coordTextMapper.SetInput(pMousePos)

        window.Render()

    interactorStyle.OnMouseMove()

def ScrollForwardCallback(obj, event):
    matrix = reslice.GetResliceAxes()
    IncrementSlice(1, matrix)

    matrix.SetElement(0, 3, center[0])
    matrix.SetElement(1, 3, center[1])
    matrix.SetElement(2, 3, center[2])

    #print("scrolling forward....")
    #print(center)
    window.Render()

def ScrollBackwardCallback(obj, event):
    matrix = reslice.GetResliceAxes()
    IncrementSlice(-1, matrix)

    matrix.SetElement(0, 3, center[0])
    matrix.SetElement(1, 3, center[1])
    matrix.SetElement(2, 3, center[2])

    #print("scrolling backward....")
    #print(center)
    window.Render()

def WindowModifiedCallback(obj, event):
    # track render window width so coordinate text aligns itself
    # to the right side of the screen

    width = window.GetSize()[0]
    coordTextActor.SetPosition(width-550, 10)
    worldCoordTextActor.SetPosition(width-550, 30)

    window.Render()

def KeyPressCallback(obj, event):
    # toggle cursor on/off when t key is pressed
    key = interactor.GetKeySym()
    if(key == "t"):
        if(actions["Cursor"] == 0):
            window.HideCursor()
            actions["Cursor"] = 1
        elif(actions["Cursor"] == 1):
            window.ShowCursor()
            actions["Cursor"] = 0


interactorStyle.AddObserver("MouseWheelForwardEvent", ScrollForwardCallback)
interactorStyle.AddObserver("MouseWheelBackwardEvent", ScrollBackwardCallback)
interactorStyle.AddObserver("MiddleButtonPressEvent", ButtonCallback)
interactorStyle.AddObserver("MiddleButtonReleaseEvent", ButtonCallback)
interactorStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)
interactorStyle.AddObserver("KeyPressEvent", KeyPressCallback)
window.AddObserver("ModifiedEvent", WindowModifiedCallback)

#interactorStyle.AddObserver("MouseWheelForwardEvent", ButtonCallback2)
#interactorStyle.AddObserver("MouseWheelBackwardEvent", ButtonCallback3)

# Start interaction
interactor.Start()
