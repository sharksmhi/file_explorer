
from . import mvp_files
from .bl_file import BlFile
from .btl_file import BtlFile
from .cnv_file import CnvFile
from .con_file import ConFile
from .dat_file import DatFile
from .hdr_file import HdrFile
from .hex_file import HexFile
from .jpg_file import JpgFile
from .png_file import PngFile
from .ros_file import RosFile
from .txt_file import TxtFile
from .xmlcon_file import XmlconFile
from .xml_file import XmlFile
from .zip_file import ZipFile
from .sensorinfo_file import SensorinfoFile
from .metadata_file import MetadataFile
from .deliverynote_file import DeliverynoteFile

from .edit_txt import add_event_id

from .compare import MismatchWarning

from .paths import SBEPaths


METADATA_COLUMNS = [
    'SHIPC',
    'MYEAR',
    'CRUISE_NO',
    'VISITID',
    'MPROG',
    'PROJ',
    'ORDERER',
    'SLABO',
    'ALABO, '
    'REFSK',
    'WADEP',
    'WINDIR',
    'WINSP',
    'AIRTEMP',
    'AIRPRES',
    'WEATH',
    'CLOUD',
    'WAVES',
    'ICEOB',
    'COMNT_VISIT',
    'station',
    'latitude',
    'longitude',
    'cruise',
    'serno',
    'year'
]


