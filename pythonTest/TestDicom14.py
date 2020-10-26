#
# This example demonstrates how to read a series of dicom images
# and how to scroll with the mousewheel or the up/down keys
# through all slices
#
# some standard vtk headers
import sys, os
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.util.misc import vtkGetDataRoot
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkImagingCore import vtkImageReslice, vtkImageMapToColors
from vtkmodules.vtkInteractionImage import vtkResliceImageViewer
from vtkmodules.vtkRenderingCore import vtkTextProperty, vtkTextMapper,\
    vtkActor2D, vtkRenderWindowInteractor, vtkCoordinate, vtkImageActor,\
    vtkVolume, vtkRenderWindow
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleImage
from vtkmodules import vtkRenderingVolumeOpenGL2
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkCommonDataModel import vtkImageData
from vtkmodules.vtkRenderingImage import vtkImageStack
from vtkmodules.vtkCommonCore import vtkLookupTable

      
def main():
    VTK_DATA_ROOT = vtkGetDataRoot()
    folder = "/Users/nandana/Downloads/image_ex"
    
    #read dicom files from specified directory
    reader = vtkDICOMImageReader()
    reader.SetDirectoryName(folder)
    reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter")
   
    reader.SetDataExtent(0, 63, 0, 63, 1, 93)
    reader.SetDataSpacing(3.2, 3.2, 1.5)
    reader.SetDataOrigin(-150.0, 150.0, 3.0)
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
    yd = ((yMax-yMin) + 1)*ySpacing
   
    # Visualize
    imageViewer = vtkResliceImageViewer()
    imageViewer2 = vtkResliceImageViewer()
    imageViewer.SetSliceOrientationToXY()

    #imageViewer.SetSlice(9)
 
    imageViewer.SetResliceModeToAxisAligned()
    imageViewer.SliceScrollOnMouseWheelOff()
    imageViewer.SetInputData(reader.GetOutput())

    imageViewer2.SetResliceModeToAxisAligned()
    imageViewer2.SliceScrollOnMouseWheelOff()
    #imageViewer2.SetInputData(reader.GetOutput())
    
    #imageViewer.Render()
    camera = imageViewer.GetRenderer().GetActiveCamera()
    camera2 = imageViewer2.GetRenderer().GetActiveCamera()
    
    print(camera.GetOrientationWXYZ())
    
    # slice status message
    sliceTextProp = vtkTextProperty()
    sliceTextProp.SetFontFamilyToCourier()
    sliceTextProp.SetFontSize(20)
    sliceTextProp.SetVerticalJustificationToBottom()
    sliceTextProp.SetJustificationToLeft()
    sliceTextMapper = vtkTextMapper()
    msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
    sliceTextMapper.SetInput(msg)
    sliceTextMapper.SetTextProperty(sliceTextProp)

    sliceTextActor = vtkActor2D()
    sliceTextActor.SetMapper(sliceTextMapper)
    sliceTextActor.SetPosition(100, 10)

    # coordinate display
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
    
    # usage hint message
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
    usageTextActor.GetPositionCoordinate().SetValue( 0.05, 0.95)

    actor = imageViewer.GetImageActor()
    #image = vtkImageActor()
    #actor.GetMapper().SetInputData(reader.GetOutput())
    
    image = imageViewer.GetInput()
    
    roiData = vtkImageData()
    roiImage = vtkImageActor()
    
    roiData.DeepCopy(image)
    extent = roiData.GetExtent()
    
    #roiData.SetExtent(0, 10, 0, 10, 0, 10)
    #print(roiData.GetExtent())
    #input()
    
    for i in range(extent[0], extent[1]):
        for j in range(extent[2], extent[3]):
            for k in range(extent[4], extent[5]):
                if image.GetScalarComponentAsDouble(i, j, k, 0) > 300:
                    roiData.SetScalarComponentFromDouble(i, j, k, 0, 1000)
                    #roiData.SetScalarComponentFromDouble(0, i, j, k, 1)
                elif image.GetScalarComponentAsDouble(i, j, k, 0) > -100:
                    roiData.SetScalarComponentFromDouble(i, j, k, 0, 1.0)
                    
                else:   #just in case
                    roiData.SetScalarComponentFromDouble(i, j, k, 0, 0.0)
                    #roiData.SetScalarComponentFromDouble(0, i, j, k, 0.0)

    print(extent)
    
    table = vtkLookupTable()
    table.SetNumberOfTableValues(3)
    table.SetRange(0.0,2.0)
    table.SetTableValue(0, 0.0, 0.0, 0.0, 1.0)
    
    #table.SetTableValue(0, 0.0, 0.0, 1.0, 0.3)
    table.SetTableValue(1, 0.0, 1.0, 0.0, 1.0) # intensity, r, g, b, a
    #table.Build()
    
    table.SetTableValue(2, 1.0, 0.0, 0.0, 1.0)

    mapToColor = vtkImageMapToColors()
    mapToColor.SetLookupTable(table)
    mapToColor.PassAlphaToOutputOn()
    
    mapToColor.AddInputData(roiData)
        
    #mapToColor.UpdateExtent((0, 511, 0, 511, 0, 108))
    maskData = mapToColor.GetOutput()
    print(maskData.GetExtent())
    print(mapToColor.GetActiveComponent())
      
    #actor.GetMapper().SetInputConnection(mapToColor.GetOutputPort())
    
    #roiImage.GetInput().SetExtent(roiData.GetExtent())
    #roiImage.GetMapper().SetInputConnection(mapToColor.GetOutputPort())
    
    roiImage.SetInputData(maskData)
    #roiImage.GetInput().SetExtent(roiData.GetExtent())
    
    print("extent")
    print(roiImage.GetInput().GetExtent())
    print(roiData.GetExtent())
    
    
    imageViewer2.SetInputData(roiData) 
       
    interactorStyle = vtkInteractorStyleImage()
    interactor = vtkRenderWindowInteractor()
    imageViewer.SetupInteractor(interactor)    
    interactor.SetInteractorStyle(interactorStyle)

    # add slice status message and usage hint message to the renderer

    imageViewer.GetRenderer().AddActor2D(coordTextActor)
    imageViewer.GetRenderer().AddActor2D(sliceTextActor)
    imageViewer.GetRenderer().AddActor2D(usageTextActor)
    imageViewer.GetRenderer().AddActor2D(worldCoordTextActor)
    
    imageViewer2.GetRenderer().AddActor(roiImage)
    #imageViewer2.GetImageActor().SetOpacity(0)
    

    # initialize rendering and interaction
    imageViewer2.SetRenderWindow(imageViewer.GetRenderWindow())
    
    imageViewer.GetRenderWindow().SetSize(1000, 1000) 
    
    imageViewer.GetRenderer().SetBackground(0.2, 0.3, 0.4)     
    imageViewer2.GetRenderer().SetBackground(0.2, 0.3, 0.4)
    
   
    imageViewer.GetWindowLevel().SetWindow(1000)
    imageViewer.GetWindowLevel().SetLevel(-1000)  
    
    
    imageViewer.Render()
    imageViewer2.Render()
    
    yd = (yMax-yMin + 1)*ySpacing
    xd = (xMax-xMin + 1)*xSpacing
    """
    d = camera.GetDistance()
    camera.SetParallelScale(0.5*xd)   
    camera.SetFocalPoint(center[0]+150,center[1], 0)
    camera.SetPosition(center[0]+150,center[1],+d)

    camera2.SetParallelScale(0.5*xd)
    camera2.SetFocalPoint(center[0]-150,center[1], 0)
    camera2.SetPosition(center[0]-150,center[1],+d)
    """
    
    imageViewer.GetRenderer().SetViewport(0.0, 0.0, 0.5, 1.0)
    imageViewer2.GetRenderer().SetViewport(0.5, 0.0, 1.0, 1.0)

    
    actions = {}
    actions["Dolly"] = -1
    actions["Cursor"] = 0
    
    def middlePressCallback(obj, event):
        # if middle + ctrl pressed, zoom in/out
        # otherwise slice through image (handled by mouseMoveCallback)
        if interactor.GetControlKey():
            actions["Dolly"] = 0
            interactorStyle.OnRightButtonDown()
            #interactorStyle2.OnRightButtonDown()
        else:
            actions["Dolly"] = 1
    def middleReleaseCallback(obj, event):
        if(actions["Dolly"] == 0):
            interactorStyle.OnRightButtonUp()
            #interactorStyle2.OnRightButtonUp()
        elif(actions["Dolly"] == 1):
            actions["Dolly"] = 0
            
    def mouseMoveCallback(obj, event):
        # if the middle button is pressed + mouse is moved, slice through image
        # otherwise, update world/pixel coords as mouse is moved
        if(actions["Dolly"] == 1):      
            print("mm dolly") 
            (lastX, lastY) = interactor.GetLastEventPosition()
            (curX, curY) = interactor.GetEventPosition()
            deltaY = curY - lastY
            
            if(deltaY > 0):
                imageViewer.IncrementSlice(1)
                imageViewer2.IncrementSlice(1)
            elif(deltaY < 0):
                imageViewer.IncrementSlice(-1)
                imageViewer2.IncrementSlice(-1)
                
            msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
            sliceTextMapper.SetInput(msg)
            imageViewer.Render()
            imageViewer2.Render()
        
        else:   
             
            (mouseX, mouseY) = interactor.GetEventPosition()            
            bounds = actor.GetMapper().GetInput().GetBounds()
                
            testCoord = vtkCoordinate()
            testCoord.SetCoordinateSystemToDisplay()
            testCoord.SetValue(mouseX, mouseY, 0);
            
            (posX, posY, posZ) = testCoord.GetComputedWorldValue(imageViewer.GetRenderer())
            
            inBounds = True;
            if posX < bounds[0] or posX > bounds[1] or posY < bounds[2] or posY > bounds[3]:
                inBounds = False
                                    
            if inBounds:
                wMousePos = "World Coordinates: (" + "{:.2f}".format(posX) + ", " + "{:.2f}".format(posY) + ", " + "{:.2f}".format(posZ) + ")"
                pMousePos = "Pixel Coordinates: (" + "{:.2f}".format(mouseX) + ", " + "{:.2f}".format(mouseY) + ")"
                worldCoordTextMapper.SetInput(wMousePos)
                coordTextMapper.SetInput(pMousePos)
                
                imageViewer.Render()

            interactorStyle.OnMouseMove()
            #interactorStyle2.OnMouseMove()
  
            
    def scrollForwardCallback(obj, event):
        # slice through image on scroll, update slice text
        imageViewer.IncrementSlice(1)
        imageViewer2.IncrementSlice(1)
                
        msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
        sliceTextMapper.SetInput(msg)
        imageViewer.Render()  
        imageViewer2.Render()
        
    def scrollBackwardCallback(obj, event):
        imageViewer.IncrementSlice(-1)
        imageViewer2.IncrementSlice(-1)
        
        msg = "Slice {} out of {}".format(imageViewer.GetSlice() + 1, \
                                     imageViewer.GetSliceMax() + 1)
        sliceTextMapper.SetInput(msg)
        imageViewer.Render()
        imageViewer2.Render()
        
    def windowModifiedCallback(obj, event):
       
        # track render window width so coordinate text aligns itself
        # to the right side of the screen
        
        width = imageViewer.GetRenderWindow().GetSize()[0]
        coordTextActor.SetPosition(width-550, 10)
        worldCoordTextActor.SetPosition(width-550, 30)
        
        imageViewer.Render()
        imageViewer2.Render()
    def keyPressCallback(obj, event):
        # toggle cursor on/off when t key is pressed
        
        key = interactor.GetKeySym()
        if(key == "t"):
            if(actions["Cursor"] == 0):
                imageViewer.GetRenderWindow().HideCursor()
                actions["Cursor"] = 1
            elif(actions["Cursor"] == 1):
                imageViewer.GetRenderWindow().ShowCursor()
                actions["Cursor"] = 0  
                
    interactorStyle.AddObserver("MiddleButtonPressEvent", middlePressCallback)
    interactorStyle.AddObserver("MiddleButtonReleaseEvent", middleReleaseCallback)
    interactorStyle.AddObserver("MouseMoveEvent", mouseMoveCallback)
    interactorStyle.AddObserver("MouseWheelForwardEvent", scrollForwardCallback)
    interactorStyle.AddObserver("MouseWheelBackwardEvent", scrollBackwardCallback)
    interactorStyle.AddObserver("KeyPressEvent", keyPressCallback)
    imageViewer.GetRenderWindow().AddObserver("ModifiedEvent", windowModifiedCallback)

    interactor.Start()
   
    


if __name__ == '__main__': main()


"""
    PROBLEMS/TODO:
    - roi stuffs
    - sagittal/coronal/stuffs @ runtime
    
    THINGS TO THINK ABOUT
    - where is thei to toggle crosshair coded
    
    WHAT THE BUTTONS CURRENTLY DO
    - left->window level
    - right->dolly
    - middle->pan
    - scroll->slice
    
    - shift+left->pan
    - ctrl/cmd+left->rotate
    - shift+right->nothing
    - ctrl/cmd+right->dolly
    - shift+middle->pan
    - ctrl/cmd+middle->dolly
    
    - i->toggle crosshair on/off
        - where is this coded omg
    - r->revert window/level
    - t->toggle cursor on/off
"""





    

