import copy
import json
import logging
import os
import re
import shutil
import urllib
import urlparse
import zipfile

import progressbar
import requests

ENV_VAR_TEMP_DIR = 'TEMP_DIR'
ENV_VAR_SOURCE_PLUGIN_URL = 'SOURCE_PLUGIN_URL'
ENV_VAR_DEST_PLUGIN_URL = 'DEST_PLUGIN_URL'
ENV_VAR_JMETER_VERSIONS_DOWNLOAD = 'JMETER_VERSIONS'

_NOT_SET = '$__NOT_SET__$'


def get_env_var(env_var, default=_NOT_SET, convert_to_type=None, fail=True):
    if env_var not in os.environ and fail and default is _NOT_SET:
        raise EnvironmentError("{} env var is not set!".format(env_var))

    value = os.environ.get(env_var, default)
    if convert_to_type:
        return convert_to_type(value)
    return value


class PluginDownloader(object):
    TEMP_DIR = get_env_var(ENV_VAR_TEMP_DIR, default='/tmp/jpd')
    DOWNLOAD_DEST = os.path.join(TEMP_DIR, 'jars')
    OUT_ZIP_PATH = os.path.join(TEMP_DIR, 'out.zip')
    INDEX_JSON_NAME = 'index.json'
    ALLOWED_SCHEMES = ['http', 'https', 'ftp']
    JMETER_FORMATTER_SYMBOL = '%1$s'

    def __init__(self, source_url, dest_url, jmeter_versions):
        self._source_url = source_url
        self._dest_url = dest_url if dest_url.endswith('/') else dest_url + '/'
        self._jmeter_versions = jmeter_versions if isinstance(jmeter_versions, list) else [x.strip() for x in
                                                                                           jmeter_versions.split(',')]

        self._urls_to_download = {}  # <url>: <fname>

    def _handle_index_string(self, string):
        parsed = urlparse.urlparse(string)
        if parsed.scheme not in self.ALLOWED_SCHEMES:
            return string

        url = string

        capture = re.findall(string=url, pattern=r'https?:\/\/.+\/(.+jar)$', flags=re.IGNORECASE)
        if not capture:
            return url

        jar_file_name = capture[0]
        if self.JMETER_FORMATTER_SYMBOL in url:
            for version in self._jmeter_versions:
                download_url = url.replace(self.JMETER_FORMATTER_SYMBOL, version)
                self._submit_download_url(download_url, jar_file_name.replace(self.JMETER_FORMATTER_SYMBOL, version))
        else:
            self._submit_download_url(url, jar_file_name)

        return urlparse.urljoin(self._dest_url, jar_file_name)

    def _submit_download_url(self, download_url, filename):
        self._urls_to_download[download_url] = filename

    def _traverse(self, data, should_copy=True):
        if should_copy:
            data = copy.deepcopy(data)

        if isinstance(data, list):
            tmp = []
            for item in data:
                tmp.append(self._traverse(item, should_copy=False))
            data = tmp
        elif isinstance(data, dict):
            for key in data:
                data[key] = self._traverse(data[key], should_copy=False)
        elif isinstance(data, basestring):
            return self._handle_index_string(data)

        return data

    def _get_source_index(self):
        return requests.get(self._source_url).json()

    def _download_urls(self, urls):
        pb = progressbar.progressbar(xrange(len(urls.keys())), redirect_stdout=True)

        for url, filename in urls.iteritems():
            try:
                logging.info("Downloading {}".format(url))
                downloaded_fname, _ = urllib.urlretrieve(url, os.path.join(self.DOWNLOAD_DEST, filename))
                pb.next()
            except:
                raise

    def _make_zip(self, folder_path, zip_path):
        logging.info("Creating zip at {}".format(zip_path))
        zipf = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                zipf.write(os.path.join(root, file))

    def _write_modified_index(self, modified_index_obj, path):
        logging.info("Writing {}".format(self.INDEX_JSON_NAME))
        with open(path, 'w') as f:
            f.write(json.dumps(modified_index_obj, indent=4))

    def run(self):
        try:
            os.makedirs(self.TEMP_DIR)
        except OSError:
            pass

        shutil.rmtree(self.DOWNLOAD_DEST, ignore_errors=True)
        os.makedirs(self.DOWNLOAD_DEST)

        self._urls_to_download = {}
        source_index = self._get_source_index()
        dest_index = self._traverse(source_index)

        self._write_modified_index(dest_index, os.path.join(self.DOWNLOAD_DEST, self.INDEX_JSON_NAME))
        self._download_urls(self._urls_to_download)
        self._make_zip(self.DOWNLOAD_DEST, self.OUT_ZIP_PATH)


def main():
    logFormatter = logging.Formatter("%(asctime)s [%(threadName)s] [%(levelname)s]  %(message)s")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    source_url = get_env_var(ENV_VAR_SOURCE_PLUGIN_URL)
    dest_url = get_env_var(ENV_VAR_DEST_PLUGIN_URL)
    jmeter_versions = get_env_var(ENV_VAR_JMETER_VERSIONS_DOWNLOAD, '5.0,4.0,3.3')

    logging.info("Downloading from {}".format(source_url))
    logging.info("Replacing source url with {}".format(dest_url))
    logging.info("Supported JMeter versions are {}".format(jmeter_versions))
    logging.info("-" * 50)

    downloader = PluginDownloader(source_url=source_url, dest_url=dest_url, jmeter_versions=jmeter_versions)
    downloader.run()


if __name__ == "__main__":
    main()
