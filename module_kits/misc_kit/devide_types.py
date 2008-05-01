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

