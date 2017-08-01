import os

class FileBundler():

    def __init__(self, max_files_per_folder, depth):
        self.max_files_per_folder = max_files_per_folder
        self.depth = depth

    def bundleFilesInEqualFolders(self, collected_files):
        folders = self.enumerateFolders(collected_files)
        for folder_name, files in folders.items():
            if len(files)<=self.max_files_per_folder:
                continue
            mini_bundles = self.getMiniBundlesFromFilesList(files)
            bundles = self.getBigBundlesFromMiniBundles(mini_bundles)
            self.assignBundlesToFilesInBundles(bundles)

    def enumerateFolders(self, collected_files):
        folders = {}
        for game_wos_id, files in collected_files.items():
            for i, file in enumerate(files):
                if not file:
                    continue
                file_dest_dir = os.path.dirname(file.getDestPath())
                if not folders.get(file_dest_dir):
                    folders[file_dest_dir]=[]
                folders[file_dest_dir].append(file)
        return folders

    def getMiniBundlesFromFilesList(self, files):
        mini_bundles = {}
        for file in files:
            mini_bundle_name = file.getBundleName()
            if not mini_bundles.get(mini_bundle_name):
                mini_bundles[mini_bundle_name] = []
            mini_bundles[mini_bundle_name].append(file)
        mini_bundles = [{
            'name':key,
            'files':value
        } for key, value in mini_bundles.items()]
        mini_bundles = sorted(mini_bundles, key=lambda x: x['name'])
        return mini_bundles

    def getBigBundlesFromMiniBundles(self, mini_bundles):
        bundles = {}
        current_bundle = []
        while True:
            if mini_bundles:
                current_bundle.append(mini_bundles.pop(0)['files'])
            files_in_current_bundle = sum([len(bundle) for bundle in current_bundle])
            if not mini_bundles or \
              len(mini_bundles[0]['files'])+files_in_current_bundle >= self.max_files_per_folder:
                if current_bundle:
                    current_bundle_name = self.getBundleName(current_bundle)
                    bundles[current_bundle_name] = [file for file in current_bundle]
                current_bundle = []
            if not mini_bundles:
                break
        return bundles

    def getBundleName(self, bundle):
        return '{}-{}'.format(bundle[0][0].getBundleName(),
                              bundle[-1][-1].getBundleName())

    def assignBundlesToFilesInBundles(self, bundles):
        for bundle_name, mini_bundles in bundles.items():
            for mini_bundle in mini_bundles:
                for file in mini_bundle:
                    file.setBundle(bundle_name)
