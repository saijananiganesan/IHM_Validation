###################################
# Script :
# 1) Contains class for em validation
#
# ganesans - Salilab - UCSF
# ganesans@salilab.org
###################################

from validation import get_input_information


class em_validation(get_input_information):
    def __init__(self, mmcif_file):
        super().__init__(mmcif_file)
        self.ID = str(get_input_information.get_id(self))
        self.nos = get_input_information.get_number_of_models(self)
        self.dataset = get_input_information.get_dataset_comp(self)
