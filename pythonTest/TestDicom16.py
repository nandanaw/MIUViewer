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

# Wasil
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import vtk
import numpy as np
from vtk.util import numpy_support

def numpy_array_as_vtk_image_data(source_numpy_array):
    """
    :param source_numpy_array: source array with 2-3 dimensions. If used, the third dimension represents the channel count.
    Note: Channels are flipped, i.e. source is assumed to be BGR instead of RGB (which works if you're using cv2.imread function to read three-channel images)
    Note: Assumes array value at [0,0] represents the upper-left pixel.
    :type source_numpy_array: np.ndarray
    :return: vtk-compatible image, if conversion is successful. Raises exception otherwise
    :rtype vtk.vtkImageData
    """

    if len(source_numpy_array.shape) > 2:
        channel_count = source_numpy_array.shape[2]
    else:
        channel_count = 1

    output_vtk_image = vtk.vtkImageData()
    output_vtk_image.SetDimensions(source_numpy_array.shape[1], source_numpy_array.shape[0], channel_count)

    vtk_type_by_numpy_type = {
        np.uint8: vtk.VTK_UNSIGNED_CHAR,
        np.uint16: vtk.VTK_UNSIGNED_SHORT,
        np.uint32: vtk.VTK_UNSIGNED_INT,
        np.uint64: vtk.VTK_UNSIGNED_LONG if vtk.VTK_SIZEOF_LONG == 64 else vtk.VTK_UNSIGNED_LONG_LONG,
        np.int8: vtk.VTK_CHAR,
        np.int16: vtk.VTK_SHORT,
        np.int32: vtk.VTK_INT,
        np.int64: vtk.VTK_LONG if vtk.VTK_SIZEOF_LONG == 64 else vtk.VTK_LONG_LONG,
        np.float32: vtk.VTK_FLOAT,
        np.float64: vtk.VTK_DOUBLE
    }
    vtk_datatype = vtk_type_by_numpy_type[source_numpy_array.dtype.type]

    source_numpy_array = np.flipud(source_numpy_array)

    # Note: don't flip (take out next two lines) if input is RGB.
    # Likewise, BGRA->RGBA would require a different reordering here.
    if channel_count > 1:
        source_numpy_array = np.flip(source_numpy_array, 2)

    depth_array = numpy_support.numpy_to_vtk(source_numpy_array.ravel(), deep=True, array_type = vtk_datatype)
    depth_array.SetNumberOfComponents(channel_count)
    output_vtk_image.SetSpacing([1, 1, 1])
    output_vtk_image.SetOrigin([-1, -1, -1])
    output_vtk_image.GetPointData().SetScalars(depth_array)

    output_vtk_image.Modified()
    return output_vtk_image

###########################################################


class PyView2D(QVTKRenderWindowInteractor):
# class PyView2D:
    def __init__(self, *args, **kwargs):
        super(PyView2D, self).__init__(*args, **kwargs)
        self.block_signal = False
        self.reader = vtkDICOMImageReader()
        self.reader2 = vtkDICOMImageReader()
        self.window = self.GetRenderWindow()
        self.window.BordersOff()    #attempt to remove imageactor borders, can remove
        self.center = [0,0,0]
        self.current_image = vtk.vtkImageData()
        self.viewer_id = "default"
        self.viewer_setup()      # flexible for future
        self.image_loaded = False
        self.viewer_initialized = False
        # self.read_image(image_path=None, orientation="axial")            # flexible for future
        
        

        self.window_level = vtkImageMapToWindowLevelColors()

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
        
        

        self.renderer = vtkRenderer()   #
        self.add_text()
        self.renderer.AddActor(self.img) #
        self.renderer.AddActor(self.roi) #

        self.renderer.SetBackground(0.2, 0.3, 0.4) #

        ### Wasil added ###
        #QVTKRenderWindowInteractor relays Qt events to VTK
        # self.frame = Qt.QFrame()    # do i need this
        # self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
       
        # miu_viewer = PyView2D()
        # vtkWidget has its own RenderWindow
        # self.ren = vtk.vtkRenderer()
        # or 
        # self.ren = miu_viewer.renderer # should have the actors already
        # self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)

        # self.vtkWidget.GetRenderWindow().SetSize(1000, 1000)
    


        # miu_viewer.window.Render()
        # or
        # self.vtkWidget.GetRenderWindow().Render()
        ##########################
        
        # have vtkRenderWindow
        # add VTKrenderer 
        # self.window = vtkRenderWindow()
        self.window.AddRenderer(self.renderer) #

        # self.window.SetSize(1000, 1000)
        self.window.SetSize(300, 300)

        self.interactor_style = vtkInteractorStyleImage()
        self.interactor_style.SetInteractionModeToImageSlicing()

        # self.interactor = vtkRenderWindowInteractor()   #
        # self.iren is the interactor (also from RenderWindow)
        self.interactor = self.GetRenderWindow().GetInteractor()
        self.interactor.SetInteractorStyle(self.interactor_style) #
        self.window.SetInteractor(self.interactor) #

        self.window_level.SetWindow(1000)
        self.window_level.SetLevel(200)
        self.window_level.Update()

        self.window.Render()
        
        ### moved this down to after image is loaded 
        # self.interactor_style.AddObserver("MouseWheelForwardEvent", self.scroll_forward_callback)
        # self.interactor_style.AddObserver("MouseWheelBackwardEvent", self.scroll_backward_callback)
        # self.interactor_style.AddObserver("MouseMoveEvent", self.mouse_move_callback)
        # self.interactor_style.AddObserver("KeyPressEvent", self.key_press_callback)
        # self.interactor_style.AddObserver("LeftButtonPressEvent", self.left_press_callback)
        # self.window.AddObserver("ModifiedEvent", self.window_mod_callback)

        self.actions = {"Slicing": 0, "Cursor": 0, "CurrentPos": -1, "LastPos": -1, "DoubleClick": 0}
    
    ### maybe don't load in here. load in miu_viewer wrapper, and feed into here 
    ### Reason: doesn't have to be loaded more than once 
    def load_image_qia(self, image_path):
        self.image = qimage.read(image_path)
        # fill out image 
        """
        1) iterate through each point and fill in vtk image object
        2) return image object
        
        eventually need to have the image fed into the connecting port instead of the reader
        """
        return
        
    def load_roi(self, roi_path):
        roi = qimage.cast(self.image)
        
    def load_image_dir(self, dicom_dir):
        VTK_DATA_ROOT = vtkGetDataRoot()
        self.reader.SetDirectoryName(dicom_dir)
        # self.reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter") # UNIX FRIENDLY
        self.reader.SetFilePrefix(VTK_DATA_ROOT + r"\Data\headsq\quarter")  # WINDOWS FRIENDLY
        self.reader.SetDataExtent(0, 63, 0, 63, 1, 93)
        self.reader.SetDataSpacing(3.2, 3.2, 1.5)
        self.reader.SetDataOrigin(0.0, 0.0, 0.0)
        self.reader.SetDataScalarTypeToUnsignedShort()
        self.reader.UpdateWholeExtent()
        self.reader.Update()
        self.current_image = self.reader.getOutput()
        
    ### This only needs to be run once. After that you can just update the matrix.
    def init_view(self, orientation="axial", center=None):
    
        if center is not None: self.center = center 
        
        # can make this more efficient by just having one enabled
        # need to change a couple other functions that use self.axial (and equivalents)
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
        if orientation=="axial":
            self.set_orientation(self.axial)
        elif orientation=="coronal":
            self.set_orientation(self.coronal)
        elif orientation=="sagittal":
            self.set_orientation(self.sagittal)
        else:
            raise("Orientation not properly selected.")
        self.viewer_initialized = True
    ### read_image is the default image reading function if a dicom directory is supplied
    def read_image(self, image_path=None, orientation="axial"):
        if image_path is None:
            # self.folder = "/Users/nandana/Downloads/image_ex"             #NANDANA PATH            
            image_folder = r"O:\personal\wasil\supervise\dluximon\miu_viewer\image_ex"
        else:
            # dicom_seri = os.path.join(image_path, "dicom.seri")
            # if os.path.exists(dicom_seri):
                # QIA version of loading
            self.image_folder = image_path
                
        self.load_image_dir(image_folder)
        
        ### Temporary to try to change the voxel values
        image = self.reader.GetOutput()
        VTK_DATA_ROOT = vtkGetDataRoot()
        # self.reader2.SetDirectoryName(dicom_dir)
        # self.reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter") # UNIX FRIENDLY
        # self.reader2.SetFilePrefix(VTK_DATA_ROOT + r"\Data\headsq\quarter")  # WINDOWS FRIENDLY
        # self.reader2.SetDataExtent(0, 63, 0, 63, 1, 93)
        # self.reader2.SetDataSpacing(3.2, 3.2, 1.5)
        # self.reader2.SetDataOrigin(0.0, 0.0, 0.0)
        # self.reader2.SetDataScalarTypeToUnsignedShort()
        # self.reader2.UpdateWholeExtent()
        # self.reader2.Update()
        # image_temp = self.reader2.GetOutput()
        image2 = vtk.vtkImageData()
        # image2.CopyStructure(image)
        # image2.ShallowCopy(image_temp) # need this if i make from vtkimagedata
        image2.ShallowCopy(image) # need this if i make from vtkimagedata
        image2.SetSpacing(.6, .6, 1)
        image2.SetExtent(0, 100, 0, 100, 0, 100) # 
        image2.SetOrigin(0, 0, 0)
        image2.SetDirectionMatrix(image.GetDirectionMatrix())   # hhmmmm
        extent = image2.GetExtent()
        
        imageData = vtk.vtkImageData()
        imageData.SetDimensions(100, 100, 100)
        if vtk.VTK_MAJOR_VERSION <= 5:
            imageData.SetNumberOfScalarComponents(1)
            imageData.SetScalarTypeToDouble()
        else:
            imageData.AllocateScalars(vtk.VTK_DOUBLE, 1)

        dims = imageData.GetDimensions()

        # Fill every entry of the image data with "2.0"
        for z in range(dims[2]):
            for y in range(dims[1]):
                for x in range(dims[0]):
                    if image.GetScalarComponentAsDouble(x, y, z, 0) > -100:
                        imageData.SetScalarComponentFromDouble(x, y, z, 0, 1000)
                    else:
                        imageData.SetScalarComponentFromDouble(x, y, z, 0, 0)
        imageData.SetSpacing(.6, .6, 1)
        imageData.SetExtent(0, 100, 0, 100, 0, 100) # 
        imageData.SetOrigin(0, 0, 0)
        imageData.SetDirectionMatrix(image.GetDirectionMatrix())   # hhmmmm
        self.imageData = imageData
        
        
        self.img_reslice.SetInputData(0, self.imageData)
        self.img_reslice.SetOutputDimensionality(2)
        self.img_reslice.SetInterpolationModeToLinear()

        self.roi_reslice.SetInputData(0, self.reader.GetOutput())
        self.roi_reslice.SetOutputDimensionality(2)
        self.roi_reslice.SetInterpolationModeToLinear()

        
        self.window.Render()

        self.center = self.calculate_center()
        self.update_view(orientation=orientation)   #TODO: it is not update_view anymore
        if not self.image_loaded:
            self.interactor_style.AddObserver("MouseWheelForwardEvent", self.scroll_forward_callback)
            self.interactor_style.AddObserver("MouseWheelBackwardEvent", self.scroll_backward_callback)
            self.interactor_style.AddObserver("MouseMoveEvent", self.mouse_move_callback)
            self.interactor_style.AddObserver("KeyPressEvent", self.key_press_callback)
            self.interactor_style.AddObserver("LeftButtonPressEvent", self.left_press_callback)
            self.window.AddObserver("ModifiedEvent", self.window_mod_callback)
            self.image_loaded = True

    ### update_image is meant to be called from outside, if you have loaded the image already
    # image is a vtkimagedata object already loaded outside
    def update_image(self, imageData, window_level=None):
        print("update_image", self.viewer_id)
        self.current_image = imageData
        self.img_reslice.SetInputData(0, imageData)
        self.img_reslice.SetOutputDimensionality(2)
        self.img_reslice.SetInterpolationModeToLinear()
        self.window.Render()

        if not self.image_loaded:   #if image wasn't loaded before, then connect functionalities
            self.interactor_style.AddObserver("MouseWheelForwardEvent", self.scroll_forward_callback)
            self.interactor_style.AddObserver("MouseWheelBackwardEvent", self.scroll_backward_callback)
            self.interactor_style.AddObserver("MouseMoveEvent", self.mouse_move_callback)
            self.interactor_style.AddObserver("KeyPressEvent", self.key_press_callback)
            self.interactor_style.AddObserver("LeftButtonPressEvent", self.left_press_callback)
            self.window.AddObserver("ModifiedEvent", self.window_mod_callback)
            self.image_loaded = True
            self.origin = self.get_origin()
            self.extent = self.get_extent()

    def update_roi(self, roiData):
        print("update_roi", self.viewer_id)
        self.roi_reslice.SetInputData(0, roiData)
        self.roi_reslice.SetOutputDimensionality(2)
        self.roi_reslice.SetInterpolationModeToLinear()

        self.window.Render()

    def viewer_setup(self,):
        print("viewer_setup", self.viewer_id)
        self.img_reslice = vtkImageReslice()
        self.roi_reslice = vtkImageReslice()

        ### Depracated old way -- GetOutputPort doesn't work here
        # self.img_reslice.SetInputConnection(0, self.reader.GetOutputPort())
        # self.img_reslice.SetInputData(0, self.reader.GetOutput())
        self.img_reslice.SetInputData(0, self.current_image)
        self.img_reslice.SetOutputDimensionality(2)
        self.img_reslice.SetInterpolationModeToLinear()

        # self.roi_reslice.SetInputConnection(0, self.reader.GetOutputPort())
        # self.roi_reslice.SetInputData(0, self.reader.GetOutput())
        self.roi_reslice.SetInputData(0, self.current_image)
        self.roi_reslice.SetOutputDimensionality(2)
        self.roi_reslice.SetInterpolationModeToLinear()

            
    def get_extent(self): # get extent in format (xMin, xMax, yMin, yMax, zMin, zMax)
        # return self.reader.GetExecutive().GetWholeExtent(self.reader.GetOutputInformation(0))
        return self.current_image.GetExtent()   # TODO: double check that this gets the same as "getWholeExtent"

    def get_extent_max(self): # get maximum extent values in format (xMax, yMax, zMax)
        return self.get_extent()[1], self.get_extent()[3], self.get_extent()[5]

    # assumes we are getting it from self.reader()
    def get_spacing(self): # get spacing in form (xSpacing, ySpacing, zSpacing)
        return self.current_image.GetSpacing()

    # assumes we are getting it from self.reader()
    def get_origin(self): # get origin in form (x0, y0, z0)
        return self.current_image.GetOrigin()

    def calculate_center(self, extent=None, spacing=None, origin=None):
        if extent is None: extent=self.get_extent() 
        if spacing is None: spacing=self.get_spacing() 
        if origin is None: origin=self.get_origin()
        
        (xMin, xMax, yMin, yMax, zMin, zMax) = extent
        (xSpacing, ySpacing, zSpacing) = spacing
        (x0, y0, z0) = origin

        return [x0 + xSpacing * int( 0.5 * (xMin + xMax)),
                y0 + ySpacing * int( 0.5 * (yMin + yMax)),
                z0 + zSpacing * int( 0.5 * (zMin + zMax))]
    # from this, we know that origin is (x0, y0, z0)
    #   if we have something that can get physical 
    def set_orientation(self, orientation):
        self.img_reslice.SetResliceAxes(orientation)
        self.roi_reslice.SetResliceAxes(orientation)

    def get_orientation(self):
        return self.img_reslice.GetResliceAxes()

    ### Detached this so that we can call it externally with an external window_level obj
    def connect_window_level(self, external_window_level=None):
        if external_window_level is not None:
            self.window_level = external_window_level
        self.window_level.SetInputConnection(self.img_reslice.GetOutputPort())
        self.img_color.SetLookupTable(self.img_table)
        self.img_color.SetInputConnection(self.window_level.GetOutputPort())

    ### sets up img stuff to return image actor
    def map_img(self,): # greyscale lookup table
        self.img_table = vtkLookupTable()
        self.img_color = vtkImageMapToColors()
        self.img_table.SetRange(0, 2000) # image intensity range
        self.img_table.SetValueRange(0.0, 1.0) # from black to white
        self.img_table.SetSaturationRange(0.0, 0.0) # no color saturation
        self.img_table.SetRampToSQRT()
        self.img_table.Build()
        
        self.connect_window_level()

        img_actor = vtkImageActor()
        img_actor.GetMapper().SetInputConnection(self.img_color.GetOutputPort())
        return img_actor

    ### sets up roi stuff to return roi actor
    def map_roi(self): # colored lookup table
        self.roi_table = vtkLookupTable()
        self.roi_table.SetNumberOfTableValues(2)
        self.roi_table.SetRange(0.0,1.0)
        self.roi_table.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
        self.roi_table.SetTableValue(1, 0.0, 1.0, 0.0, 1.0) # value, r, g, b, a
        self.roi_table.Build()

        self.roi_color = vtkImageMapToColors()
        self.roi_color.SetLookupTable(self.roi_table)
        self.roi_color.SetInputConnection(self.roi_reslice.GetOutputPort())

        roi_actor = vtkImageActor()
        roi_actor.GetMapper().SetInputConnection(self.roi_color.GetOutputPort())

        return roi_actor

    ### Text stuff -- left unchanged ###
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

    def update_centers(self, current_viewer_index):
        # to be overriden by outside function 
        return 
    def update_window_level(self, current_viewer_index):
        # to be overriden by outside function
        return
        
    def increment_slice(self, inc, reslice_axes):
        x_inc = y_inc = z_inc = 0
        # upperBound = lowerBound = 0
        center = self.center
        (x_spacing, y_spacing, z_spacing) = self.get_spacing()
        (x_max, y_max, z_max) = self.get_extent_max()

        i = -1

        if reslice_axes == self.sagittal:
            # lowerBound = self.origin[2] # hint: it's not 2. #TODO: set this for other reslice axes
            x_inc = inc*x_spacing
            upperBound = floor(x_max*x_spacing)
            i = 0
        elif reslice_axes == self.coronal:
            # lowerBound = self.origin[2] # hint: it's not 2. #TODO: set this for other reslice axes
            y_inc = inc*y_spacing
            upperBound = floor(y_max*y_spacing)
            i = 1
        elif reslice_axes == self.axial:
            lowerBound = self.origin[2]
            z_inc = inc*z_spacing
            upperBound = floor(lowerBound+z_max*z_spacing)
            i = 2

        elif reslice_axes == self.oblique:
            pass
        else:
            sys.stderr.write("ERROR: Invalid view orientation")
            exit(1)

        # slice through image by changing center
        if (inc < 0 and center[i] > lowerBound) or (inc > 0 and center[i] < upperBound):
        # if True:
            self.center = (center[0]+x_inc, center[1]+y_inc, center[2]+z_inc)
            self.update_centers(self.viewer_id)
            
    # Remove all ROIs
    def reset_rois(self):
        self.update_roi(None)   # replace ROI with None so it updates with empty ROI actor
        
        ### Saved for future if we have more than 1 ROI enabled.
        # for roi in self.rois:
            # self.renderer.RemoveViewProp(roi)
        return
        
    ### TODO: Implement clear
    # clear images and rois 
    def clear(self):
        print("Not Implemented Yet.")
        
    ### if submitted in image position ...
    def set_position(self, pos, format="viewer_coordinates"):
        # if self.view == "axial":
        print("set_position", self.viewer_id)
        if format=="image_coordinates":
            bounds = (-196, 196, -196, 196, 0, 0)   #TODO: fix hack
            Z_OFFSET = 0
            pos = ( pos[0] / ( self.extent[1] - self.extent[0]) * (bounds[1]-bounds[0]) ,
                        (pos[1] -  ( self.extent[3] - self.extent[2])) / ( self.extent[3] - self.extent[2]) * (bounds[3]-bounds[2]),
                        pos[2]*self.get_spacing()[2] + self.origin[2])
        print(">>>>>>",pos)
        self.center = pos
        self.get_orientation().SetElement(0, 3, self.center[0])
        self.get_orientation().SetElement(1, 3, self.center[1])
        self.get_orientation().SetElement(2, 3, self.center[2])
        # other views:
        ###
        
        # self.window.Render()  # assume render is done outside? not sure about this

    ### Nandana's example of changing parameters (super useful, thank you)
    def load_example(self, img, roi, alpha, window_size, window_val, level_val, n_center):
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

    ### Callback section ###
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

    ### Separate this because it might be used by other functions
    def _get_mouse_pos(self):
        (mouseX, mouseY) = self.interactor.GetEventPosition()
        Z_OFFSET = 0
        bounds = self.img.GetMapper().GetInput().GetBounds()    # move this somewhere else and define as class variable, only needs to be retrieved once
        # print("bounds 1:", bounds)
        # print("displayextent",  self.img.GetMapper().GetInput().GetDisplayExtent())
        bounds = self.img.GetDisplayBounds()    # move this somewhere else and define as class variable, only needs to be retrieved once
        # print("bounds 2:", bounds)
        bounds = self.img.GetBounds()    # move this somewhere else and define as class variable, only needs to be retrieved once
        # print("bounds 2:", bounds)
        bounds = (-196, 196, -196, 196, 0, 0)
        testCoord = vtkCoordinate()
        testCoord.SetCoordinateSystemToDisplay()
        testCoord.SetValue(mouseX, mouseY, 0) # TODO: set 3rd val to slice num
        # print("GetResliceAxesOrigin", self.img_reslice.GetResliceAxesOrigin())
        # print("GetResliceAxesDirectionCosines", self.img_reslice.GetResliceAxesDirectionCosines())
        self.img_reslice.SetOutputOrigin(self.get_origin())
        self.img_reslice.SetOutputExtent(self.get_extent())
        self.img_reslice.SetOutputSpacing(self.get_spacing())
        self.img_reslice.TransformInputSamplingOff()
        # print("GetOutputOrigin", self.img_reslice.GetOutputOrigin())
        # print("GetOutputExtent", self.img_reslice.GetOutputExtent())
        # print("GetOutputSpacing", self.img_reslice.GetOutputSpacing())
        # print("GetSlabSliceSpacingFraction", self.img_reslice.GetSlabSliceSpacingFraction())
        # print("GetSlabNumberOfSlices", self.img_reslice.GetSlabNumberOfSlices())
        # print("GetAutoCropOutput", self.img_reslice.GetAutoCropOutput())
        # print("GetTransformInputSampling", self.img_reslice.GetTransformInputSampling())
        (posX, posY, _) = testCoord.GetComputedWorldValue(self.renderer)
        # print(mouseX,mouseY, "    |||     ", posX, posY)
        # print(self.center)
        # print(self.origin)
        #mouseX and mouseY are the image positions in the overall window itself
        posZ = self.center[2]
        if posX < bounds[0] or posX > bounds[1] or posY < bounds[2] or posY > bounds[3]:
            return None
        
            
        (xSpacing, ySpacing, zSpacing) = self.get_spacing()
        # print(self.get_spacing())
        # (xMin, xMax, yMin, yMax, zMin, zMax) = extent
        # weird window
        window_pos = (posX - bounds[0], posY - bounds[1])
        # print("window pos",window_pos[1])
        # print("bounds",bounds[3], bounds[2])
        # print("extent..",self.extent[3], self.extent[2])
        image_pos = ( window_pos[0]/(bounds[1]-bounds[0])*( self.extent[1] - self.extent[0]),
                      window_pos[1]/(bounds[3]-bounds[2])*( self.extent[3] - self.extent[2]) + ( self.extent[3] - self.extent[2]), # because 0,0 should be bottom left instead of top left   
                      (posZ-self.origin[2])/zSpacing )   #need to incorporate directioncosines 
                        
        phys_pos = (    image_pos[0]*xSpacing + self.origin[0], #technically has an orientation factor but ignored for now
                        image_pos[1]*ySpacing + self.origin[1],
                        posZ, # TODO: double check physical position for z
                        )
                        

        # print(window_pos[0], image_pos[0], phys_pos[0])
        # return ( int((posX+self.center[0])/xSpacing - self.origin[0]), int((posY+self.center[1])/ySpacing - self.origin[1]), int(posZ-Z_OFFSET - self.origin[2]) )
        # return ( int((posX+self.center[0])/xSpacing - self.origin[0]), int((posY+self.center[1])/ySpacing - self.origin[1]), int(posZ-Z_OFFSET - self.origin[2]) )
        return dict(image_pos=image_pos, phys_pos=phys_pos)
        # return ( int((posX+self.center[0])/xSpacing), int((posY+self.center[1])/ySpacing), int(posZ-Z_OFFSET) )
        
    def mouse_move_callback(self, obj, event):
        positions = self._get_mouse_pos()
        image_pos = positions["image_pos"]
        phys_pos = positions["phys_pos"]
        # (mouseX, mouseY) = self.interactor.GetEventPosition()
        # Z_OFFSET = 0
        # bounds = self.img.GetMapper().GetInput().GetBounds()    # move this somewhere else and define as class variable, only needs to be retrieved once

        # testCoord = vtkCoordinate()
        # testCoord.SetCoordinateSystemToDisplay()
        # testCoord.SetValue(mouseX, mouseY, 0) # TODO: set 3rd val to slice num
        # (posX, posY, _) = testCoord.GetComputedWorldValue(self.renderer)
        # posZ = self.center[2]

        # inBounds = True;
        # if posX < bounds[0] or posX > bounds[1] or posY < bounds[2] or posY > bounds[3]:
            # inBounds = False

        if image_pos is not None:
            # wMousePos = "Pixel Coordinates: (" + "{:d}".format(int((posX+self.center[0])/xSpacing)) + ", " + "{:d}".format(int((posY+self.center[1])/ySpacing)) + ", " + "{:d}".format(int(posZ-Z_OFFSET)) + ")"
            # wMousePos = "Pixel Coordinates: (" + "{:d}".format(int(image_pos[0])) + ", " + "{:d}".format(int(image_pos[1])) + ", " + "{:d}".format(int(image_pos[2])) + ")"
            wMousePos = "Pixel Coordinates: (" + "{:.2f}".format(image_pos[0]) + ", " + "{:.2f}".format(image_pos[1]) + ", " + "{:.2f}".format(image_pos[2]) + ")"
            pMousePos = "World Coordinates: (" + "{:.2f}".format(phys_pos[0]) + ", " + "{:.2f}".format(phys_pos[1]) + ", " + "{:.2f}".format(phys_pos[2]) + ")"
            # pMousePos = "??? Coordinates: (" + "{:.2f}".format(mouseX) + ", " + "{:.2f}".format(mouseY) + ")"
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
            self.load_example(viewer.img, viewer.roi, 0.8, (500, 500), 1000, 200, [169.66796875, 169.66796875, 107.0])
            self.start_interaction()
            
    def location_clicked(self, image_pos):
        ### Overriden externally 
        print("still a test function")
        return
        
    def left_doublepress_callback(self, obj, event):
        print("double clicked")
        print(self.center)
        image_pos = self._get_mouse_pos()
        print("double clicked position:", image_pos)
        self.location_clicked(image_pos)
        return image_pos
        
    def left_press_callback(self, obj, event):
        diff = None
        self.actions["CurrentPos"] = timer()

        if self.actions["LastPos"] != -1:
            diff = self.actions["CurrentPos"] - self.actions["LastPos"]

        if diff is not None and diff < 0.5: # valid double click
            print("double clicked")
            self.left_doublepress_callback(obj, event)
            # print(self.center)
            # image_pos = _get_mouse_pos()
            # print("double clicked position:", image_pos)
            
            # return image_pos
                
        self.actions["LastPos"] = self.actions["CurrentPos"]
        self.interactor_style.OnLeftButtonDown()
        # self.update_window_level(self.viewer_id)
        return None
        
    def window_mod_callback(self, obj, event):
        width = self.window.GetSize()[0]
        self.px_coord_text_actor.SetPosition(width-550, 10)
        self.world_coord_text_actor.SetPosition(width-550, 30)

        self.window.Render()

    def start_interaction(self):
        self.interactor.Start()
    
    def block_signals(self, bool_val):
        self.block_signal = bool_val
        # Blocks signal inputs so there isn't an overload of input and feedback
        


# if __name__ == "__main__":
    # app = Qt.QApplication(sys.argv)
    # window = MainWindow()
    # sys.exit(app.exec_())


# if __name__ == '__main__':
    # app = QtWidgets.QApplication([])
    # viewer = PyView2D()
    # # volume = PowerBar()
    # # viewer.show()
    # app.exec_()

    # # viewer = MIUViewer()
    # # viewer.start_interaction()
