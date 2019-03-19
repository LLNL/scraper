class TFSProject:
    def __init__(self, projectInfo, collectionInfo):
        self.projectInfo = projectInfo
        self.collectionInfo = collectionInfo
        self.projectCreateInfo = {}
        self.projectLastUpdateInfo = {}
        self.gitInfo = []
        self.tfvcInfo = []
