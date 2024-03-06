
import os
import requests
import json
import uuid

class SHARKwebAPI():
    """Datasource base class, used for fetching and filtering data
    before transformation to ekostat data format.

    Note: the data files are expected to be tab seperated fields with
    first row holding the headers.

    """
    def __init__(self, result_directory, file_parser=None):
        self.result_directory = result_directory

    def save_files(self, datatypes, year_interval):

        filenames = []

        # We need to split download into several ones due to timeouts
        # on server. It seems that we can query a full year without a
        # timeout appear, so lets do that.

        for datatype in datatypes:

            filename = os.path.join(self.result_directory, f'sharkweb_{datatype}_{year_interval[0]}-{year_interval[1]}.txt')
            filenames.append(filename)

            # if self.no_download and os.path.exists(filename):
            #     self.logger.info('Skipping download, file exists \'%s\'' % filename)
            #     continue

            payload = {

                'params': {
                    'headerLang': 'short',
                    'encoding': 'utf-8',
                    'delimiters': 'point-tab',
                    'tableView': 'sample_col_physicalchemical_columnparams'
                },

                'query': {
                    'fromYear': year_interval[0],
                    'toYear': year_interval[1],
                    'dataTypes': datatype,
                    # 'projects': ["NAT Nationell miljöövervakning"],
                    # 'bounds': [[10.4, 58.2], [10.6, 58.3]],
                },

                'downloadId': str(uuid.uuid4()),
            }

            api_server = 'https://sharkweb.smhi.se'
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'text/plain',
            }

            # self.logger.info("Requesting download of samples for year '%s' id '%s'" % (year, payload['downloadId']))
            with requests.post('%s/api/sample/download' % api_server,
                                data=json.dumps(payload), headers=headers) as response:

                response.raise_for_status()

                data_location = response.headers['location']
                # self.logger.info("Downloading data from location '%s' into filename '%s'" % (data_location , filename))
                with requests.get('%s%s' % (api_server, data_location), stream=True) as data_response:
                    data_response.raise_for_status()
                    chunk_size = 1024*1024
                    with open(filename, 'wb') as data_file:
                        for chunk in data_response.iter_content(chunk_size=chunk_size):
                            if not chunk:
                                continue
                            data_file.write(chunk)

        return filenames

if __name__ == "__main__":
    SHARKwebAPI(result_directory = '..\data')._prepare(datatypes = ['Physical and Chemical'], year_interval = [1960,2024])