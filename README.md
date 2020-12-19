# MIUViewer

An application for visualizing and parsing through DICOM image files.

All updated code is in the pythonTest folder, and the different versions are organized as thus follows:

**TestDicom 15 -- Creates the MIUViewer class, most of my future work will go into this file. This version has the same functionality as TestDicom12, so it will eventually replace that file in this repository. 

TestDicom12 -- Version that can display the image + the ROI overlay and slice through both of them simeultaneously. 

TestDicom13 -- Same as TestDicom13_1, but with an ROI overlay over the original image. The overlay currently only displays over the first slice of the image, and disappears for every other slice. The functionalities in terms of key bindings are also the same as TestDicom13_1, but the window/leveling only works on the first slice.

TestDicom13_1 -- The basic viewer with various features in terms of interacting with an image (slicing through, window/leveling, zooming in/out, moving the image). This version also displays current world and pixel coordinates based on the location of the cursor, as well as the current slice number. Currently, this viewer cannot view an image from different orientations.

TestDicom14 -- The viewer with two different viewports. One of the viewports displays the original image, and is identical to TestDicom13_1, while the other displays the ROI overlay over the image data (which has been altered from the original image). One can slice through both images at once (though the ROI overlay is only applied to the first three slices), but other interactions such as window/leveling must be done separately as of right now. This viewer cannot view an image from different orientations, but most of the development/testing in terms of that will probably go in this file.
