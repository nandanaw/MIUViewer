#!/usr/bin/env python

# This example shows how to load a 3D image into VTK and then reformat
# that image into a different orientation for viewing.  It uses
# vtkImageReslice for reformatting the image, and uses vtkImageActor
# and vtkInteractorStyleImage to display the image.  This InteractorStyle
# forces the camera to stay perpendicular to the XY plane.

import vtk
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.util.misc import vtkGetDataRoot
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonCore import vtkLookupTable
from vtkmodules.vtkImagingCore import vtkImageMapToColors
from vtkmodules.vtkRenderingCore import vtkImageActor, vtkRenderer,\
    vtkRenderWindow, vtkRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
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

center = [x0 + xSpacing * 0.5 * (xMin + xMax),
          y0 + ySpacing * 0.5 * (yMin + yMax),
          z0 + zSpacing * 0.5 * (zMin + zMax)]

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
reslice = vtkMatrix4x4()
reslice.SetInputConnection(reader.GetOutputPort())
reslice.SetOutputDimensionality(2)
#reslice.SetMagnificationFactors(2, 0, 0)
reslice.SetResliceAxes(sagittal)
reslice.SetInterpolationModeToLinear()

# Create a greyscale lookup table
table = vtkLookupTable()

table.SetRange(0, 2000) # image intensity range
table.SetValueRange(0.0, 1.0) # from black to white
table.SetSaturationRange(0.0, 0.0) # no color saturation
table.SetRampToSQRT()
table.Build()


# Map the image through the lookup table
color = vtkImageMapToColors()
color.SetLookupTable(table)
color.SetInputConnection(reslice.GetOutputPort())

# Display the image
actor = vtkImageActor()
actor.GetMapper().SetInputConnection(color.GetOutputPort())

print(actor.GetInput().GetExtent)

renderer = vtkRenderer()
renderer.AddActor(actor)

window = vtkRenderWindow()
window.AddRenderer(renderer)

# Set up the interaction
interactorStyle = vtkInteractorStyleImage()

interactorStyle.SetInteractionModeToImageSlicing()

interactor = vtkRenderWindowInteractor()
interactor.SetInteractorStyle(interactorStyle)
window.SetInteractor(interactor)
window.Render()

# Create callbacks for slicing the image
actions = {}
actions["Slicing"] = 0

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
    (lastX, lastY) = interactor.GetLastEventPosition()
    (mouseX, mouseY) = interactor.GetEventPosition()
    if actions["Slicing"] == 1:
        deltaY = mouseY - lastY
        reslice.Update()
        sliceSpacing = reslice.GetOutput().GetSpacing()[2]
        matrix = reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaY, 1))
        matrix.SetElement(0, 3, center[0])
        matrix.SetElement(1, 3, center[1])
        matrix.SetElement(2, 3, center[2])
        window.Render()

    elif actions["Slicing"] == 2:
        deltaScroll = 0.25
        reslice.Update()
        sliceSpacing = reslice.GetOutput().GetSpacing()[2]
        matrix = reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaScroll, 1))
        matrix.SetElement(0, 3, center[0])
        matrix.SetElement(1, 3, center[1])
        matrix.SetElement(2, 3, center[2])
        window.Render()

    elif actions["Slicing"] == 3:
        deltaScroll = -0.25
        reslice.Update()
        sliceSpacing = reslice.GetOutput().GetSpacing()[2]
        matrix = reslice.GetResliceAxes()
        # move the center point that we are slicing through
        center = matrix.MultiplyPoint((0, 0, sliceSpacing*deltaScroll, 1))
        matrix.SetElement(0, 3, center[0])
        matrix.SetElement(1, 3, center[1])
        matrix.SetElement(2, 3, center[2])
        window.Render()
        
    else:
        interactorStyle.OnMouseMove()


interactorStyle.AddObserver("MouseMoveEvent", MouseMoveCallback)
interactorStyle.AddObserver("MiddleButtonPressEvent", ButtonCallback)
interactorStyle.AddObserver("MiddleButtonReleaseEvent", ButtonCallback)


interactorStyle.AddObserver("MouseWheelForwardEvent", ButtonCallback2)
interactorStyle.AddObserver("MouseWheelBackwardEvent", ButtonCallback3)

# Start interaction
interactor.Start()
