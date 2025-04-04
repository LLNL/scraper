class AzureDevOpsCollection:
    def __init__(self, id="", name="", url=""):
        self.id = id
        self.name = name
        self.url = url

class AzureDevOpsProject:
    def __init__(self, project_id="", project_name="", project_description="", project_url="", repo_url="", project_create_time="", project_last_update_time="", collection_or_org_name = ""):
        self.project_id = project_id
        self.project_name = project_name
        self.project_description = project_description
        self.project_url = project_url
        self.repo_url = repo_url
        self.project_create_time = project_create_time
        self.project_last_update_time = project_last_update_time
        self.collection_or_org_name = collection_or_org_name