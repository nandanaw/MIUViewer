import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QFileDialog, QStyleFactory, QProgressBar
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPalette, QColor
from PyQt5.QtCore import pyqtSlot, QSize, Qt, QItemSelectionModel
from ui_miu_viewer import Ui_MainWindow

qia_loaded = False
# try:
    # import __medview__
    # from qia.common.threadpool import ThreadPool
    # import qia.common.img.image as qimage
    # import qia.common.img.lut as qlut
    # from qia.common.img.utils import get_casted_roi
    # qia_loaded = True
####

import vtk 
import numpy as np
from vtkmodules.vtkImagingColor import vtkImageMapToWindowLevelColors
from vtkmodules.vtkIOImage import vtkDICOMImageReader
from vtkmodules.util.misc import vtkGetDataRoot


def load_solution(file):
    solution_element_list = []
    with open(file, "r") as f:
        current_sol_element = None
        current_item = None
        for l in f:
            line = l.strip()
            if line:
                line = line.split(": ")
                if line[0]=="SolElement":
                    current_sol_element = {
                        "Name":line[1].strip(),
                        "Attributes":[],
                        "Candidates":[],
                        "MatchedPrimitiveRoi":None
                    }
                    solution_element_list.append(current_sol_element)
                elif line[0]=="Attribute":
                    if current_item is not None: 
                        raise Exception("Invalid termination encountered when processing "+repr(cur_item))
                    current_item = [(line[1], line[2])]
                    current_sol_element["Attributes"].append(current_item)
                elif line[0]=="Candidate_start":
                    if current_item is not None: raise Exception("Invalid termination encountered when processing "+repr(cur_item))
                    current_item = {"Index":len(current_sol_element["Candidates"])}
                    current_sol_element["Candidates"].append(current_item)
                elif line[0]=="MatchedPrimitiveRoiFile":
                    current_sol_element["MatchedPrimitiveRoi"] = line[1]
                elif line[0]=="End" or line[0]=="Candidate_end":
                    current_item = None
                else:
                    if current_item is not None:
                        if type(current_item) is dict:
                            current_item[line[0]] = line[1]
                        else:
                            current_item.append((line[0], line[1]))
    return solution_element_list

def ReadTillNextSpace(roi_str):
    read_str = ""
    i = 0
    character = roi_str[i]
    str_len = len(roi_str)
    while not character==" ":
        read_str+=character
        if i+1 <= str_len:
            i+=1
            character = roi_str[i:i+1]
        else:
            character = " "
        
    return int(read_str), roi_str[i+1:] #assume that that read number is always int
    

"""
    roi_file = r"\\dingo\scratch\wasil\se_cnn_research_pipeline\results\10073_sample\roi\1.2.392.200036.9116.2.5.1.48.1221398669.1435023456.141510_0\1000619395.roi"
    read_roi(roi_file)

"""
def read_roi(roi_file, mode="list"):
    ### Prep
    
    if mode=="list":
        output = []
    
    with open(roi_file, 'r') as f:
        roi_str = f.read()
        
    slice_num, roi_str = ReadTillNextSpace(roi_str)
    
    for s in range(slice_num):
        z, roi_str = ReadTillNextSpace(roi_str)
        line_num, roi_str = ReadTillNextSpace(roi_str)
        
        for l in range(line_num):
            y, roi_str = ReadTillNextSpace(roi_str)
            interval_num, roi_str = ReadTillNextSpace(roi_str)
            
            for i in range(interval_num):
                x_start, roi_str = ReadTillNextSpace(roi_str)
                x_end, roi_str = ReadTillNextSpace(roi_str)
                
                if mode=="list":
                    for x in range(x_start, x_end+1):
                        print(x, y, z) #debugging only
                        output.append((x, y, z))
    return output
    
class RoiObject(list):
    def __init__(self, *args, **kwargs):
        super(RoiObject, self).__init__(*args, **kwargs)
        self.origin = None
        self.spacing = None
        self.origin = None
        self.roi_region = None
        self.size = None
        self.roi_pts_lookup = dict()
    def fill_with_roi(self, roi_file, val=1):
        roi_pts = read_roi(roi_file)
        for pt in roi_pts:
            self.roi_pts_lookup[pt] = val
        self.extend(roi_pts)
        # res = list(zip(*test_list)) 
        # roi_pts = zip( res[0], res[1], res[2], [val for _ in range(len(res[0])) ]
    ### Updates attributes via QIA object
    def update_qia(self, image_qia):
        self.origin = image_qia.get_origin()
        self.spacing = image_qia.get_spacing()
        self.size = image_qia.get_size()
    def get_size(self):
        return self.size
    def get_origin(self):
        return self.origin
    def get_spacing(self):
        return self.spacing
    def get_roi_region(self, val=None):
        
        res = list(zip(*self))   
        # 0 is x, 1 is y, 2 is zfill
        
        self.roi_region = ( (min(res[0]), min(res[1]), min(res[2])), (max(res[0]), max(res[1]), max(res[2])))
        return self.roi_region
    def contain(self, point):
        return point in self
        
    def get_value(self, point):
        return self.roi_pts_lookup.get(point, 0)
    def set_value(self, point, val):
        self.roi_pts_lookup[point] = val

### Unused ###
"""
def get_wl_range(level, window):
    print(level, window)
    minv = (2*level - window)/2
    maxv = (2*level + window)/2
    print((maxv+minv)/2, maxv-minv)
    
    return (2*level - window)/2, (2*level + window)/2
"""

r"""
Command:
#pilot
M:\apps\personal\wasil\medviewer\test\miu_viewer.py M:\apps\personal\wasil\trash\test_miu_output

#nandana
M:\apps\personal\wasil\medviewer\test\miu_viewer.py C:\Users\wanwar\Desktop\Nandana\seg
M:\apps\personal\wasil\medviewer\test\miu_viewer.py C:\Users\wanwar\Desktop\Nandana\seg "demo_mode"

python3 /Users/nandana/MIUViewer/pythonTest/miu_viewer.py /Users/nandana/MIUViewer/pythonTest/sample/seg "demo_mode"
"""

### Initialize the GUI ###
class MainWindow(QMainWindow):
    def __init__(self, pool=None):
        super().__init__()
        # self.pool = pool
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.sol_elements = None
        self.basepath = None
        self.image = None
        self.alt_image = None
        self.lut = None
        self.viewer_center = (0,0,0)
        
        ### default LUT (in QIA format) ###
        # self.roi_lut = ipplut.new({
            # 0: (0,0,0,0),
            # 1: (0,1,0,self.ui.opacity.value()/100),
            # "table": (0,1)
        # })
        self.roi = None
        
        ### enable all of these when ready 
        self.views = (
            self.ui.axial,
            self.ui.coronal,
            # self.ui.sagittal,
            # self.ui.three_d
        )
        
        # connecting functionalities
        for i, v in enumerate(self.views):
            print("connect try")
            v.location_clicked = self.location_clicked
            v.update_centers = self.update_centers
            # v.update_window_level = self.update_window_level  ### Disabled for now because it's not working
            print("connected")
            v.viewer_id = i
            
        ### Connect more things ###
        # for v in self.views:
            # for i in [q for q in self.views if q!=v]:
                # v.positionChanged.connect(i.setPosition)
                # v.zoomed.connect(i.setZoom)
                # if v!=self.ui.three_d and i!=self.ui.three_d:
                    # v.cameraReset.connect(i.resetCamera)
                    
        self.show_crosshair(self.ui.show_crosshair.isChecked())
        
        ### Initializing opacity
        self.opacity_changed(0) # what is the zero there for 
        
        self.ui.actionRefresh.setEnabled(False)
        self.loading_solution_file = False
        
        self.render_progress = QProgressBar(self)
        self.render_progress.setFormat("Rendering %p%")
        # self.ui.three_d.progress.connect(self.render_progress.setValue)   #temp disabled
        self.ui.statusbar.addPermanentWidget(self.render_progress)
                
        # global window level to make it all the same
        self.window_level = vtkImageMapToWindowLevelColors()

                
    ### This is already done in PyViewer
    """
    def wheel(self, view, event):
        if self.image is None:
            return
        point = view.getPosition()
        spacing = self.image.get_spacing()
        axis = view.getAxis(2)
        offset = sum((i*j for i,j in zip(axis,spacing)))
        if event.angleDelta().y()>0:
            vec = [i*offset for i in axis]
        else:
            vec = [-i*offset for i in axis]
        new_point = [i+j for i,j in zip(point, vec)]
        view.setPosition(new_point)
        view.skipInteractorCallbackOnce()
        
    """
    
    ### TODO: Not implemented yet ###
    @pyqtSlot()
    def reset_view(self):
        print("Reset view not implemented yet")
        # for v in self.views:
            # v.resetCamera()
    
    @pyqtSlot()
    def load(self, path=None, demo_mode=None, alt_image_file=None):
        self.demo_mode = demo_mode is not None
        if path is None:
            if self.basepath is not None:
                start_path = os.path.dirname(self.basepath)
            else:
                start_path = ""
            path = QFileDialog.getExistingDirectory(self, "Load directory", start_path, QFileDialog.ShowDirsOnly)
            if not path:
                return
        for v in self.views:
            v.clear()

        ### UI Stuff ###
        self.ui.showAltImage.setChecked(False)
        if alt_image_file is None:
            self.alt_image = None
            self.ui.showAltImage.setEnabled(False)
        else:
            self.alt_image = ippimg.read(alt_image_file)
            self.ui.showAltImage.setEnabled(True)
            
        self.ui.actionRefresh.setEnabled(True)
        self.loading_solution_file = True
        self.basepath = path
        self.ui.sol_elements.clearSelection()
        self.ui.sol_elements.clear()
        self.clear_table(self.ui.attributes)
        self.clear_table(self.ui.parameters)
        self.clear_table(self.ui.candidates)
        self.clear_table(self.ui.attribute_values)
        
        ### load solution elements from MIU ###
        self.sol_elements = load_solution(os.path.join(path, "solution_info.txt"))
        for i in self.sol_elements:
            self.ui.sol_elements.addItem(i["Name"])
        self.loading_solution_file = False
        
        # #pool.apply(self.load_image, args=[os.path.join(path, "dicom.seri")]) ## for thread pool parallelization ??
        ##################
        
        if not self.demo_mode:
            ### Loading the .seri file
            if os.path.exists(os.path.join(path, "dicom.seri")):
                self.load_image(os.path.join(path, "dicom.seri"))
            else:
                with open(os.path.join(path, "source_image.txt")) as f:
                    for l in f:
                        file = l.strip()
                        if file:
                            if not os.path.isabs(file):
                                file = os.path.join(path, file)
                        self.load_image(file)
                        break            
        else:
            with open(os.path.join(path, "dicom_dir.txt"), 'r') as f:
                contents = f.read()
            dicom_dir = contents.strip()
            self.load_image(dicom_dir)
        # self.load_image_demo()
        #################################
    @pyqtSlot()
    def reload(self):
        self.load(self.basepath)
            
    ### Seems to work okay.. ###
    def render(self):
        for v in self.views:
            v.window.Render()   # not general but probably fine

    """         
    ### Special for Nandana's set-up ###
    def load_image_demo(self):
        dicom_dir = r"\\dingo\data\PechinTest2\cad_aapm2017_batch_1\library\recon\10\8382bb95bd0127acac284c6dcec17e76_k1_st2.0\img\GAN-v1-ref-d100-k2-st1.0_8382bb95bd0127acac284c6dcec17e76_d10_k1_st2.0"
        image_file = r"M:\apps\personal\wasil\trash\test_miu_output\dicom.seri"
        self.image = qimage.read(image_file)
        roi_file = r"M:\apps\personal\wasil\trash\test_miu_output\lung_init.roi"
        roi = qimage.cast(self.image)
        roi.fill_with_roi(roi_file)
        image_npy = np.array(self.image.get_array())
        image_npy = np.moveaxis(image_npy, 0, 2) #because I saved the numpy files (z, x, y) -_-
        image_npy = np.rot90(image_npy, 3)
        image_npy = np.flip(image_npy, 1)
        image_info = dict(image_data=image_npy, spacing=self.image.get_spacing(), origin=self.image.get_origin())
        self.ui.axial.update_image(image_info, "axial")

        roi_foreground = roi.find(1, None)
        roi_info = dict(roi_foreground=roi_foreground)
        self.ui.axial.update_roi(roi_info,)
    """
    def load_roi(self, roi):
        if qia_loaded:
            roi_foreground = roi.find(1, None)
        else:
            roi_foreground = roi    # already in list form if not loaded by QIA
        ### Saves the points of an ROI in a text file, useful for crossreferencing moused-over points to ROIs
        # roi_points_list = r"M:\apps\personal\wasil\medviewer\test\roi_pts.txt"
        # with open(roi_points_list, 'w') as f:
            # f.write("\n".join([str(pt) for pt in roi_foreground]))
        ###
        
        roi_info = dict(roi_foreground=roi_foreground)
        roiData = vtk.vtkImageData()
        if roi_info is not None:
            print("Filling vtk image data")
            if qia_loaded:
                dims = self.image.get_size()
                roi_info.update(dict(spacing=self.image.get_spacing(), origin=self.image.get_origin()) )
            else:
                dims = self.image.GetDimensions()
                roi_info.update(dict(spacing=self.image.GetSpacing(), origin=self.image.GetOrigin()) )

            roiData.SetDimensions(dims[0], dims[1], dims[2])

            # (2) Update the vtk obj image information
            roiData.SetSpacing(roi_info["spacing"][0], roi_info["spacing"][1], roi_info["spacing"][2])
            roiData.SetExtent(0, dims[0]-1, 0, dims[1]-1, 0, dims[2]-1) # 
            roiData.SetOrigin(roi_info["origin"][0], roi_info["origin"][1], roi_info["origin"][2]) #unsure if it's this one
            # roiData.SetOrigin(roi_info["origin"][0], roi_info["origin"][1], 0) #unsure if it's this one
            # roiData.SetDirectionMatrix(self.current_image.GetDirectionMatrix())   # TODO: implement this later? not sure if needed
            if vtk.VTK_MAJOR_VERSION <= 5:
                roiData.SetNumberOfScalarComponents(1)
                roiData.SetScalarTypeToDouble()
            else:
                roiData.AllocateScalars(vtk.VTK_DOUBLE, 1)
            
            # assume all points are 0 by default
            print("points:", len(roi_info["roi_foreground"]))
            for point in roi_info["roi_foreground"]:
                if qia_loaded:
                    (x,y,z,v) = point
                else:
                    (x,y,z) = point 
                roiData.SetScalarComponentFromDouble(x, y, z, 0, 1 ) # all foreground automatically 1, to make binary
        return roiData

    def load_image(self, file):
        # (1) Read File
        # (2) Get min, max, window-level
        # (3) Update views 
        
        # (1) 
        
        if self.demo_mode:
            print(file)
            print("......")
            self.reader = vtkDICOMImageReader()
            VTK_DATA_ROOT = vtkGetDataRoot()
            self.reader.SetDirectoryName(file)
            self.reader.SetFilePrefix(VTK_DATA_ROOT + "/Data/headsq/quarter") # UNIX FRIENDLY
            # self.reader.SetFilePrefix(VTK_DATA_ROOT + r"\Data\headsq\quarter")  # WINDOWS FRIENDLY
            
            ### Extract 
            # TODO: double check that the image attributes are correct when using vtkDICOMimageReader
            
            
            # self.reader.SetDataExtent(0, 63, 0, 63, 1, 93)
            # self.reader.SetDataSpacing(3.2, 3.2, 1.5)
            # self.reader.SetDataOrigin(0.0, 0.0, 0.0)
            self.reader.SetDataScalarTypeToUnsignedShort()
            # self.reader.UpdateWholeExtent()
            self.reader.Update()
            imageData = self.reader.GetOutput()
            self.image = imageData
            image_info = dict(image_data=imageData, spacing=imageData.GetSpacing(), origin=imageData.GetOrigin())
            minv, maxv = (-1024, 1024)  #close enough estimate
        else:
            if qia_loaded:
                print(file)
                self.image = qimage.read(file)

                ### QIA version
                image_info = dict(image_data=self.image, spacing=self.image.get_spacing(), origin=self.image.get_origin())
                dims = image_info["image_data"].get_size()
            else:   #assume numpy array
                print("Not implemented yet")
                # load numpy array
            
                ### numpy version >>> for future compatibility 
                # image_npy = np.array(self.image.get_array())
                # image_npy = np.moveaxis(image_npy, 0, 2) #because I saved the numpy files (z, x, y) -_-
                # image_npy = np.rot90(image_npy, 3)
                # image_npy = np.flip(image_npy, 1)
                # image_info = dict(image_data=image_npy, spacing=self.image.get_spacing(), origin=self.image.get_origin())
                # dims = image_info["image_data"].shape


            imageData = vtk.vtkImageData()
            
            print("dims", dims)
            #instantiating imageData obj
            imageData.SetDimensions(dims[0], dims[1], dims[2])
            if vtk.VTK_MAJOR_VERSION <= 5:
                imageData.SetNumberOfScalarComponents(1)
                imageData.SetScalarTypeToDouble()
            else:
                imageData.AllocateScalars(vtk.VTK_DOUBLE, 1)

            # (2) Update the vtk obj image information
            imageData.SetSpacing(image_info["spacing"][0], image_info["spacing"][1], image_info["spacing"][2])
            
            ### QIA Version 
            imageData.SetExtent(0, dims[0]-1, 0, dims[1]-1, 1, dims[2]) # with QIA it goes from [ 1 to z_max ] instead of [0 to z_max - 1]
            imageData.SetOrigin(image_info["origin"][0], image_info["origin"][1], image_info["origin"][2]) #unsure if it's this one
            # imageData.SetOrigin(image_info["origin"][0], image_info["origin"][1], 0) #unsure if it's this one

            for z in range(dims[2]):
                z+=1
                for y in range(dims[1]):
                    for x in range(dims[0]):
                        # print(x,y, z)
                        # double check if x,y,z is the appropriate order after you get the numpy array
                        # imageData.SetScalarComponentFromDouble(x, y, z, 0, image_info["image_data"][x,y,z] )  # numpy
                        imageData.SetScalarComponentFromDouble(x, y, z, 0, image_info["image_data"].get_value((x,y,z)) ) # QIA
            minv, maxv = self.image.get_min_max()
        # (2)
        self.window_level.SetWindow(maxv-minv)
        self.window_level.SetLevel((maxv+minv)/2)
        self.window_level.Update()
        
        
        # (3) 
        # TODO: Make blockSignals useful (to avoid reloading things if we click too often, etc.)
        for v in self.views:  
            v.blockSignals(True)    
        self.viewer_center = self.views[0].calculate_center(extent=imageData.GetExtent(), spacing=image_info["spacing"], origin=image_info["origin"])
        print("viewer center", self.viewer_center)
        for v in self.views:
            v.update_image(imageData)
            if not v.viewer_initialized:
                # orientation = "axial"
                orientation = "sagittal"
                #   before this, orientation has of the viewer has not been defined yet.
                #   aka it doesn't set the viewer orientation until the first image has loaded
                v.init_view(orientation=orientation, center=self.viewer_center)
            else:
                # if viewer has been initialized already, then just update the center
                v.set_position(self.viewer_center)
            v.connect_window_level(self.window_level)   #updating window level
            # v.resetCamera()   ### TODO: Implement and activate
        for v in self.views:
            v.blockSignals(False) 
        self.render()
            
    def get_selected_elem(self):
        return self.sol_elements[self.ui.sol_elements.currentRow()]
        
    def clear_table(self, table):
        table.clearSelection()
        table.clearContents()
        table.setRowCount(0)
        
    ### TODO: Implement ###
    @pyqtSlot(bool)
    def show_crosshair(self, show):
        print("Crosshairs not implemented yet")
        return
        # for v in self.views:
            # v.show_crosshair(show)
        
    @pyqtSlot()
    def sol_elem_selected(self):
        self.clear_table(self.ui.attributes)
        self.clear_table(self.ui.parameters)
        self.clear_table(self.ui.candidates)
        self.clear_table(self.ui.attribute_values)
        self.ui.partial_confidence.setText("")
        self.ui.roi_file.setText("")
        
        elem = self.get_selected_elem()
        
        attributes = elem["Attributes"]
        if attributes:
            self.ui.attributes.setRowCount(len(attributes))
            for i, row in zip(attributes, range(len(attributes))):
                for c, col in zip(i[0], (0,1)):
                    self.ui.attributes.setItem(row, col, QTableWidgetItem(c))
            self.ui.attributes.resizeColumnsToContents()
            self.ui.attributes.resizeRowsToContents()
            
        candidates = elem["Candidates"]
        row = len(candidates)
        if elem["MatchedPrimitiveRoi"] is not None:
            row += 1
        if row>0:
            self.ui.candidates.setRowCount(row)
            offset = 0
            if elem["MatchedPrimitiveRoi"] is not None:
                offset = 1
                self.ui.candidates.setItem(0, 0, QTableWidgetItem("MatchedPrimitive"))
                self.ui.candidates.setItem(0, 1, QTableWidgetItem("Yes"))
            for c, r in zip(candidates, range(len(candidates))):
                self.ui.candidates.setItem(r+offset, 0, QTableWidgetItem(str(c["Index"])))
                if c["Matched"]=="True":
                    self.ui.candidates.setItem(r+offset, 1, QTableWidgetItem("Yes"))
            self.ui.candidates.resizeColumnsToContents()
            self.ui.candidates.resizeRowsToContents()
            self.ui.candidates.selectRow(0)

        if row>1:
            self.ui.select_matched.setEnabled(True)
            self.ui.toggle_select.setEnabled(True)
        else:
            self.ui.select_matched.setEnabled(False)
            self.ui.toggle_select.setEnabled(False)
        
    @pyqtSlot()
    def attribute_selected(self):
        self.clear_table(self.ui.parameters)
        selected = self.ui.attributes.selectedIndexes()
        if selected:
            row = selected[0].row()
            attribute = self.get_selected_elem()["Attributes"][row]
            if len(attribute)>1:
                attribute = attribute[1:]
                self.ui.parameters.setRowCount(len(attribute))
                for i, row in zip(attribute, range(len(attribute))):
                    for c, col in zip(i, (0,1)):
                        self.ui.parameters.setItem(row, col, QTableWidgetItem(c))
                self.ui.parameters.resizeColumnsToContents()
                self.ui.parameters.resizeRowsToContents()
                
                
    ### Generally used to load an ROI or remove ROI
    ### or is it used to update when we change position? 
    ### ROI Filling can be made more efficient by filling the numpy array directly
    
    ### Plan:

    def _update_views(self, mask_info=None, skip_3D=False):   # for now keep skip_3D false
        if skip_3D:
            views = self.views[:-1]
        else:
            views = self.views
                        
        for v in views:
            # v.reset_rois()
            if not v.block_signal:
                v.block_signals(True)
                v.update_roi(mask_info) #if mask_info is None then it just updates ROI to have nothing
                v.block_signals(False)
            else:
                print("blocked signal!")
            # auto_render = v.autoRender()
            # v.autoRender(False)
            # v.pushBack(self._get_view_image(), self.lut)
            # if mask is not None:
                # v.pushBack(mask, vtk.vtkLookupTable(self.roi_lut))
            # v.autoRender(auto_render)
        for v in views:
            v.window.Render()
            
    # What is alt image >_> 
    ### TODO: Implement ###
    def _get_view_image(self):
        print("Alternate image not implemented yet.")
        # if self.ui.showAltImage.isChecked():
            # return self.alt_image
        # else:
            # return self.image
            
    ### TODO: Implement ###
    @pyqtSlot()
    def toggle_alt_image(self):
        print("Alternate image not implemented yet.")
        # self._update_views(self.roi, skip_3D=True)

    @pyqtSlot(tuple)
    def location_clicked(self, pos):
        ### Gets the image coordinates ###
        print("Clicked location")
        print(pos)
        
        if len(self.ui.candidates.selectedIndexes())<=2:  # basically only allows this if "Select Matched" is used
            return
        # coord = [round(i) for i in self.roi.to_image_coordinates(pos)]
        coord = pos
        print("Clicked location")

        ### Checks if the coordinates are contained within the .roi shown
        #   Gets the value, which is also the row index 
        # if qia_loaded:
        ### Should be compatible with both QIA and non-QIA
        if self.roi.contain(coord):
            print("Contained")
            index = self.roi.get_value(coord)
            print(index)
            if index>0:
                self.ui.candidates.selectRow(index-1)
                print('yeah')   
        else:
            print("Not Contained")
        # else:
            # if self.roi.contain(coord):
                # print("Contained")
                # index = self.roi.get_value(coord)
                # print(index)
                # if index>0:
                    # self.ui.candidates.selectRow(index-1)
                    # print('yeah')   
            # else:
                # print("Not Contained")

    @pyqtSlot()
    def select_matched(self):
        self.ui.candidates.blockSignals(True)
        self.ui.candidates.clearSelection()
        for row in range(self.ui.candidates.rowCount()):
            if self.ui.candidates.item(row,1) is not None:
                if self.ui.candidates.item(row,1).text()=="Yes" and self.ui.candidates.item(row,0).text()!="MatchedPrimitive":
                    for col in range(self.ui.candidates.columnCount()):
                        self.ui.candidates.selectionModel().select(self.ui.candidates.model().index(row,col), QItemSelectionModel.Select)
        self.ui.candidates.blockSignals(False)
        self.candidate_selected()
        
    @pyqtSlot()
    def toggle_selections(self):
        self.ui.candidates.blockSignals(True)
        selected = {sel.row() for sel in self.ui.candidates.selectedIndexes()}
        self.ui.candidates.clearSelection()
        for row in range(self.ui.candidates.rowCount()):
            if row not in selected and self.ui.candidates.item(row,0).text()!="MatchedPrimitive":
                for col in range(self.ui.candidates.columnCount()):
                    self.ui.candidates.selectionModel().select(self.ui.candidates.model().index(row,col), QItemSelectionModel.Select)
        self.ui.candidates.blockSignals(False)
        self.candidate_selected()
            
    ### If candidate selected, then load up the ROI ###
    @pyqtSlot()
    def candidate_selected(self):
        self.clear_table(self.ui.attribute_values)
        selected = self.ui.candidates.selectedIndexes()
        if selected:
            elem = self.get_selected_elem()
            if len(selected)==2: #Update attribute table if there is only one selected item (2 cells)
                row = selected[0].row()
                text = self.ui.candidates.item(row, 0).text()
                if text=="MatchedPrimitive":
                    self.ui.roi_file.setText(os.path.join(self.basepath, elem["MatchedPrimitiveRoi"]))
                else:
                    candidate = elem["Candidates"][int(text)]
                    self.ui.roi_file.setText(os.path.join(self.basepath, candidate["RoiFile"]))
                    self.ui.partial_confidence.setText(str(candidate["PartialConfidence"]))
                    
                    attrib = elem["Attributes"]
                    values = candidate["FeatureValue"].strip().split(" ")
                    scores = candidate["ConfidenceScore"].strip().split(" ")
                    self.ui.attribute_values.setRowCount(len(values))
                    for a,v,s,r in zip(attrib,values, scores, range(len(values))):
                        self.ui.attribute_values.setItem(r, 0, QTableWidgetItem(a[0][0]))
                        self.ui.attribute_values.setItem(r, 1, QTableWidgetItem(a[0][1]))
                        self.ui.attribute_values.setItem(r, 2, QTableWidgetItem(v))
                        self.ui.attribute_values.setItem(r, 3, QTableWidgetItem(s))
                    self.ui.attribute_values.resizeColumnsToContents()
                    self.ui.attribute_values.resizeRowsToContents()
            else:
                self.ui.partial_confidence.setText("")
                self.ui.roi_file.setText("")
                
            if qia_loaded:
                self.roi = qimage.cast(self.image, qimage.Type.int)
            else:
                self.roi = RoiObject()
            for sel in selected:    # fills ROI for _each_ ROI
                row = sel.row()
                text = self.ui.candidates.item(row, 0).text()
                if text=="MatchedPrimitive":
                    print("Matched Prim", os.path.join(self.basepath, elem["MatchedPrimitiveRoi"]), row+1)
                    self.roi.fill_with_roi(os.path.join(self.basepath, elem["MatchedPrimitiveRoi"]), row+1)
                else:
                    candidate = elem["Candidates"][int(text)]
                    print("Candidates", os.path.join(self.basepath, candidate["RoiFile"]), row+1)
                    self.roi.fill_with_roi(os.path.join(self.basepath, candidate["RoiFile"]), row+1)
            print("Loading...", self.loading_solution_file )
            if not self.loading_solution_file:  # just making sure solution file is done loading ? 
                vtk_roi = self.load_roi(self.roi)
                self._update_views(vtk_roi)
                self.auto_navigate() #
                self.render()
        else:
            self.roi = None
            if not self.loading_solution_file:
                self._update_views()

    @pyqtSlot(int)
    def opacity_changed(self, val):
        for v in self.views:
            v.roi.SetOpacity(self.ui.opacity.value()/100)
        # self.ui.three_d.changeOpacity(self.ui.opacity.value()/100)    #future 3D opacity
        self.render()
        
        
    @pyqtSlot()
    def lung_wl(self):
        for v in self.views:
            v.window_level.SetLevel(-500)
            v.window_level.SetWindow(1500)
        self.render()
        
    @pyqtSlot()
    def soft_tissue_wl(self):
        for v in self.views:
            v.window_level.SetLevel(40)
            v.window_level.SetWindow(400)
        self.render()
        
    @pyqtSlot()
    def bone_wl(self):
        for v in self.views:
            v.window_level.SetLevel(400)
            v.window_level.SetWindow(1500)
        self.render()
        
    @pyqtSlot(bool)
    def auto_navigate(self):
        mask = self.roi
        if qia_loaded:
            if self.ui.auto_navigate.isChecked() and mask is not None:
                ### TODO: Double check this. Because I think we set position based on the image coordinates.
                image_pos = [round(i+(j-i)/2) for i, j in zip(*mask.find_region(1, None))]
                phys_pos = self.image.to_physical_coordinates(image_pos)
                pos = (phys_pos[0], phys_pos[1], image_pos[2]*mask.get_spacing()[2] + mask.get_origin()[2])
                print(">>>>>>",pos)
                for v in self.views:
                    v.set_position(pos)
                self.render()
        else:
            if self.ui.auto_navigate.isChecked() and mask is not None:
                #try to find the region encapsulated 
                pos = [round(i+(j-i)/2) for i, j in zip(*mask.get_roi_region())]
                for v in self.views:
                    v.set_position(pos, format="image_coordinates")
                self.render()
                
    def update_centers(self, current_viewer_index):
        self.viewer_center = self.views[current_viewer_index].center
        for i, v in enumerate(self.views):
            print(i)
            if i==current_viewer_index:
                print("skipped!")
                continue
            v.set_position(self.viewer_center)
        self.render()
        
    ## doesn't work properly ##
    ### TODO: Make the window level sync across viewers 
    def update_window_level(self, current_viewer_index):
        window = self.views[current_viewer_index].window_level.GetWindow()
        level = self.views[current_viewer_index].window_level.GetLevel()
        print(window, level)
        self.window_level.SetWindow(window)
        self.window_level.SetLevel(level)
        self.window_level.Update()
        print("Updated window level")
        # for i, v in enumerate(self.views):
            # print(i)
            # if i==current_viewer_index:
                # print("skipped!")
                # continue
            # v.set_position(self.viewer_center)
        self.render()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("fusion"))
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53,53,53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15,15,15))
    palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53,53,53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(200,50,40).lighter());
    palette.setColor(QPalette.Highlight, QColor(200,50,40).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    palette.setColor(QPalette.Light, QColor(93,93,93))
    palette.setColor(QPalette.Midlight, QColor(73,73,73))
    palette.setColor(QPalette.Mid, QColor(33,33,33))
    palette.setColor(QPalette.Dark, QColor(15,15,15))
    palette.setColor(QPalette.Shadow, Qt.black)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, Qt.darkGray)
    palette.setColor(QPalette.Disabled, QPalette.Text, Qt.darkGray);
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, Qt.darkGray);
    app.setPalette(palette)
    app.setStyleSheet("QToolTip { color: #ffffff; background-color: #da8282; border: 1px solid white; }");
    
    # with ThreadPool(2) as pool: # disable threadpool in demo mode 
        # m = MainWindow(pool)
    if True:
        m = MainWindow()
        m.show()
        if len(sys.argv)==2:
            m.load(sys.argv[1])
        elif len(sys.argv)==3:  # temporary for nandana's system
            m.load(sys.argv[1], sys.argv[2])
        # else:
            # m.load(sys.argv[1], sys.argv[2])
        ret_val = app.exec_()
    sys.exit(ret_val)