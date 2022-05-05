from .psa_file import PSAfile

import logging


logger = logging.getLogger(__name__)


class DerivePSAfile(PSAfile):
    def __init__(self, file_path):
        super().__init__(file_path)

    def turn_tau_correction_on(self):
        self.set_tau_correction(True)

    def turn_tau_correction_off(self):
        self.set_tau_correction(False)

    def set_tau_correction(self, state):
        state = str(int(state))
        for element in self.tree.find('CalcArray'):
            calc_element = element.find('Calc').find('ApplyTauCorrection')
            if calc_element is not None:
                calc_element.set('value', state)
        for element in self.tree.find('MiscellaneousDataForCalculations'):
            logger.debug(f'DerivePSAfile.MiscellaneousDataForCalculations.element: {element}')
            calc_element = element.find('ApplyTauCorrection')
            if calc_element is None:
                logger.debug(f'ApplyTauCorrection NOT found for element: {element}')
                continue
            logger.debug(f'ApplyTauCorrection found for element: {element}')
            calc_element.set('value', state)

        self.save()