from .psa_file import PSAfile


class DatCnvPSAfile(PSAfile):

    def __init__(self, file_path):
        super().__init__(file_path)

    def get_parameter_info(self):
        pars = self.tree.find('CalcArray').getchildren()
        pars_info = []
        for par in pars:
            info = {}
            info.update(par.attrib)
            calc = par.find('Calc')
            info.update(calc.attrib)
            full_name = calc.find('FullName')
            info.update(full_name.attrib)
            info['name'] = info['value']
            pars_info.append(info)
        return pars_info


