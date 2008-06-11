# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

class MedicalMetaData:
    def __init__(self):
        self.medical_image_properties = None
        self.direction_cosines = None

    def close(self):
        del self.medical_image_properties
        del self.direction_cosines

    def deep_copy(self, source_mmd):
        """Given another MedicalMetaData instance source_mmd, copy its
        contents to this instance.
        """

        if not source_mmd is None:
            self.medical_image_properties.DeepCopy(
                    source_mmd.medical_image_properties)
            self.direction_cosines.DeepCopy(
                    source_mmd.direction_cosines)

