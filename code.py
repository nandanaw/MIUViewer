#
# This example demonstrates how to read a series of dicom images
# and how to scroll with the mousewheel or the up/down keys
# through all slices
#
# some standard vtk headers


import vtk
import sys
from vtk.util.misc import vtkGetDataRoot

class myResliceCommand(vtk.vtkCommand):
    def __init__(self, parent=None):
        print("constructed") 
    
def main():
    print("program started")
    VTK_DATA_ROOT = vtkGetDataRoot()
    folder = "/Users/nandana/Downloads/image_ex"
    #read dicom files from specified directory
    reader = vtk.vtkDICOMImageReader()
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
 

    # Visualize
    imageViewer = vtk.vtkResliceImageViewer()
    imageViewer.SetResliceModeToAxisAligned()
    
    imageViewer.SliceScrollOnMouseWheelOff()
    
    imageViewer.SetInputData(reader.GetOutput())

    # slice status message
    sliceTextProp = vtk.vtkTextProperty()
    sliceTextProp.SetFontFamilyToCourier()
    sliceTextProp.SetFontSize(20)
    sliceTextProp.SetVerticalJustificationToBottom()
    sliceTextProp.SetJustificationToLeft()
    sliceTextMapper = vtk.vtkTextMapper()
    msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
    sliceTextMapper.SetInput(msg)
    sliceTextMapper.SetTextProperty(sliceTextProp)

    sliceTextActor = vtk.vtkActor2D()
    sliceTextActor.SetMapper(sliceTextMapper)
    sliceTextActor.SetPosition(100, 10)
    
    # coordinate display
    coordTextProp = vtk.vtkTextProperty()
    coordTextProp.SetFontFamilyToCourier()
    coordTextProp.SetFontSize(20)
    coordTextProp.SetVerticalJustificationToBottom()
    coordTextProp.SetJustificationToLeft()
    
    coordTextMapper = vtk.vtkTextMapper()
    coordTextMapper.SetInput("Pixel Coordinates: (--, --)")
    coordTextMapper.SetTextProperty(coordTextProp)

    coordTextActor = vtk.vtkActor2D()
    coordTextActor.SetMapper(coordTextMapper)
    coordTextActor.SetPosition(500, 10)
    
    
    worldCoordTextProp = vtk.vtkTextProperty()
    worldCoordTextProp.SetFontFamilyToCourier()
    worldCoordTextProp.SetFontSize(20)
    worldCoordTextProp.SetVerticalJustificationToBottom()
    worldCoordTextProp.SetJustificationToLeft()
    
    worldCoordTextMapper = vtk.vtkTextMapper()
    worldCoordTextMapper.SetInput("World Coordinates: (--, --)")
    worldCoordTextMapper.SetTextProperty(worldCoordTextProp)
    
    worldCoordTextActor = vtk.vtkActor2D()
    worldCoordTextActor.SetMapper(worldCoordTextMapper)
    coordTextActor.SetPosition(500, 30)
    
    # usage hint message
    usageTextProp = vtk.vtkTextProperty()
    usageTextProp.SetFontFamilyToCourier()
    usageTextProp.SetFontSize(14)
    usageTextProp.SetVerticalJustificationToTop()
    usageTextProp.SetJustificationToLeft()

    usageTextMapper = vtk.vtkTextMapper()
    usageTextMapper.SetInput("- Slice with mouse wheel\n- Zoom with pressed right\n  mouse button while dragging\n- Press i to toggle cursor line on/off")
    usageTextMapper.SetTextProperty(usageTextProp)

    usageTextActor = vtk.vtkActor2D()
    usageTextActor.SetMapper(usageTextMapper)
    usageTextActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedDisplay()
    usageTextActor.GetPositionCoordinate().SetValue( 0.05, 0.95)

    interactorStyle = vtk.vtkInteractorStyleImage()
    # vtkInteractorStyleImage() by default does everything
    # that the program is currently doing EXCEPT FOR SLICING A and the i thing
    
    interactor = vtk.vtkRenderWindowInteractor()
    # myStyle = MyInteractorStyle()
    # myStyle.SetInteractionModeToImageSlicing()

    imageViewer.SetupInteractor(interactor)
    interactor.SetInteractorStyle(interactorStyle)
    
    # add slice status message and usage hint message to the renderer
    imageViewer.GetRenderer().AddActor2D(coordTextActor)
    imageViewer.GetRenderer().AddActor2D(sliceTextActor)
    imageViewer.GetRenderer().AddActor2D(usageTextActor)
    imageViewer.GetRenderer().AddActor2D(worldCoordTextActor)
    
    
    # initialize rendering and interaction
    imageViewer.GetRenderWindow().SetSize(400, 300)
    imageViewer.GetRenderer().SetBackground(0.2, 0.3, 0.4)
    imageViewer.Render()
    imageViewer.GetRenderer().ResetCamera()
    imageViewer.Render()    


    actions = {}
    actions["Dolly"] = -1

    def middlePressCallback(obj, event):
        if(interactor.GetControlKey()):
            actions["Dolly"] = 0
            interactorStyle.OnRightButtonDown()
        else:
            actions["Dolly"] = 1
    
    def middleReleaseCallback(obj, event):
        if(actions["Dolly"] == 0):
            interactorStyle.OnRightButtonUp()
        elif(actions["Dolly"] == 1):
            actions["Dolly"] = 0;
       
    def mouseMoveCallback(obj, event):
        if(actions["Dolly"] == 1):
            (lastX, lastY) = interactor.GetLastEventPosition()
            (curX, curY) = interactor.GetEventPosition()
            deltaY = curY - lastY
            
            if(deltaY > 0):
                imageViewer.IncrementSlice(1)
            elif(deltaY < 0):
                imageViewer.IncrementSlice(-1)
                
            msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
            sliceTextMapper.SetInput(msg)
            imageViewer.Render()
        
        else:    
            (mouseX, mouseY) = interactor.GetEventPosition()
            mousePos = "Pixel Coordinates: (" + str(mouseX) + ", " + str(mouseY) + ")"
            coordTextMapper.SetInput(mousePos)
            imageViewer.Render()
            interactorStyle.OnMouseMove()
    
    def scrollForwardCallback(obj, event):
        
        imageViewer.IncrementSlice(1)
        
        msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
        sliceTextMapper.SetInput(msg)
        imageViewer.Render()
        
    def scrollBackwardCallback(obj, event):
        
        imageViewer.IncrementSlice(-1)
        msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
        sliceTextMapper.SetInput(msg)
        imageViewer.Render()
        
    def windowModifiedCallback(obj, event):
        # track render window width so coordinate text aligns itself
        # to the right side of the screen
        
        width = imageViewer.GetRenderWindow().GetSize()[0]

        coordTextActor.SetPosition(width-450, 10)
        worldCoordTextActor.SetPosition(width-450, 30)
        imageViewer.Render()
        
    
    interactorStyle.AddObserver("MiddleButtonPressEvent", middlePressCallback)
    interactorStyle.AddObserver("MiddleButtonReleaseEvent", middleReleaseCallback)
    interactorStyle.AddObserver("MouseMoveEvent", mouseMoveCallback)
    interactorStyle.AddObserver("MouseWheelForwardEvent", scrollForwardCallback)
    interactorStyle.AddObserver("MouseWheelBackwardEvent", scrollBackwardCallback)
    imageViewer.GetRenderWindow().AddObserver("ModifiedEvent", windowModifiedCallback)
   
    interactor.Start()
    


if __name__ == '__main__': main()
