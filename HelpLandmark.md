# Introduction #

In the MRI retrobulbar fat mobility study, multiple MRI datasets are made of a subject during different directions of gaze. Although great care is taken to prevent rigid head motion, this does still occur. So before the deformation of the fat is calculated, rigid head motion has to be eliminated by means of a landmark-based rigid registration.

One of the directions of gaze is chosen as the central or reference direction: all other datasets have to be registered onto this dataset. In this way, all datasets will share a common frame of reference.  This reference dataset is also called the target dataset, and all other datasets that are registered to it are called source datasets:  Source is registered to target.

In the next subsections, we will explain how to perform one such registration. This obviously has to be performed for all datasets that you have to register onto the reference dataset. The figure below shows an example DeVIDE network for performing this landmark-based rigid registration. Refer to it during the following explanation.

![http://devide.googlecode.com/svn/wiki/help_images/landmark_ex_dvn.png](http://devide.googlecode.com/svn/wiki/help_images/landmark_ex_dvn.png)

# Select source and target points #
Select at least 3, preferably more rigid landmarks that can be accurately localised in all datasets.

Select these points in the reference (target) dataset by using the mouse cursor in a 3D slice3dVWR. You have to name each of these points: In the slicedVWR control panel, enter the name into the "name" input box before clicking on the "Store this point" button. The names of these points have to start with "Target", for example "Target Zygoma 1".

Save your network regularly!

Now load in the first source dataset that you want to register onto the reference (target) dataset.  Select and store all corresponding points in this dataset. Use a separate slice3dVWR. The names of these points all have to start with "Source", for example "Source Zygoma 1", and the rest of the name should match their corresponding target landmarks.  For example, "source zygoma 1" and "target zygoma 1" should correspond.

# Derive the transform #
Instantiate a "landmarkTransform'' module from the Filters category. Read its help by right- clicking on the module and selecting "Help on Module".

Connect up both of the slice3dVWR's first outputs to the two inputs of the landmarkTransform.  From the "Help on Module" documentation, you'll notice that there are other possibilities as well for correctly wiring up the landmarkTransform.

# Transform the dataset #
Connect the output of the "landmarkTransform'' to the second input of a "transformVolumeData'' module (category "Filters''). Connect the source dataset that you are registering onto the reference (target) dataset to the first input of the "transformVolumeData'' module. After network execution, the output of this module will be the transformed volume dataset.

You can add it to one of the reference (target) dataset's slice3dVWR's inputs for an overlay. Select the "Primary LUT fusion'' overlay mode in the slice3dVWR control panel. The Alpha-parameter can be adjusted to "fade'' from the reference dataset to the registered dataset and back.

Don't forget to save your transformed dataset: Connect the output of the "transformVolume'' module to the input of a "vtiWRT'' module for example. Double click on the "vtiWRT'' module and then click on the browse button to select a filename. Remember to execute the network again after having done this, so that the writer module does its work.