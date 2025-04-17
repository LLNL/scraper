import base64
import logging
import os
import re
from typing import List

import requests

from scraper.azuredevops.models import AzureDevOpsCollection, AzureDevOpsProject

logger = logging.getLogger(__name__)


class AzureDevOpsClient:
    def __init__(self, baseurl, api_version, token=None):
        self.baseurl = baseurl
        self.api_version = api_version
        self.is_cloud_ado = "dev.azure.com" in baseurl
        self.session = self._create_client_session(token)

    def get_projects_metadata(self) -> List[AzureDevOpsProject]:
        """
        Get metadata for all projects
        """
        collections = self._get_all_collections()
        return self._get_all_projects(collections)

    def _create_client_session(self, token):
        """
        Creates the Azure DevOps Client Context with the provided token.
        If no token is provided, it will look for the ADO_API_TOKEN environment variable.
        """
        if token is None:
            token = os.environ.get("ADO_API_TOKEN", None)

        if token is None:
            raise RuntimeError("Azure Dev Ops Token was not provided.")

        session = requests.Session()
        auth_string = f":{token}"
        encoded_auth = base64.b64encode(auth_string.encode("ascii")).decode("ascii")
        session.headers.update(
            {"Authorization": f"Basic {encoded_auth}", "Accept": "application/json"}
        )
        return session

    def _get_all_collections(self) -> List[AzureDevOpsCollection]:
        """
        Get all collections from the Azure DevOps API.
        """
        collections = []

        if self.is_cloud_ado:
            # For cloud Azure DevOps, get all organizations from the API
            profile_url = f"https://app.vssps.visualstudio.com/_apis/profile/profiles/me?api-version={self.api_version}"
            profile_response = self.session.get(profile_url)

            if profile_response.status_code == 200:
                profile = profile_response.json()

                # Get user's organizations/accounts
                accounts_url = f"https://app.vssps.visualstudio.com/_apis/accounts?memberId={profile['id']}&api-version={self.api_version}"
                accounts_response = self.session.get(accounts_url)

                if accounts_response.status_code == 200:
                    accounts_json = accounts_response.json()

                    if accounts_json.get("value") and len(accounts_json["value"]) > 0:
                        for org in accounts_json["value"]:
                            collections.append(
                                AzureDevOpsCollection(
                                    id=org["accountId"],
                                    name=org["accountName"],
                                    url=f"https://dev.azure.com/{org['accountName']}",
                                )
                            )
                            logger.debug(
                                f"Found cloud organization: {org['accountName']}"
                            )
                    else:
                        logger.warning("No organizations found with your access token.")

                        # Fallback: Try to extract organization from baseAddress
                        org_name = self.baseurl.rstrip("/").split("/")[-1]
                        if org_name and org_name != "dev.azure.com":
                            collections.append(
                                AzureDevOpsCollection(
                                    id=org_name,
                                    name=org_name,
                                    url=f"https://dev.azure.com/{org_name}",
                                )
                            )
                            logger.debug(
                                f"Using organization from base address: {org_name}"
                            )
                else:
                    raise RuntimeError(
                        f"Failed to retrieve organizations. Status Code: {accounts_response.status_code} Response: {accounts_response.text}"
                    )
            else:
                logger.warning(
                    f"Failed to retrieve user profile: {profile_response.status_code} Response: {profile_response.text}"
                )
                logger.warning(
                    "Falling back to base address for organization extraction."
                )
                # Fallback: Try to extract organization from baseAddress
                org_name = self.baseurl.rstrip("/").split("/")[-1]
                if org_name and org_name != "dev.azure.com":
                    collections.append(
                        AzureDevOpsCollection(
                            id=org_name,
                            name=org_name,
                            url=f"https://dev.azure.com/{org_name}",
                        )
                    )
                    logger.debug(f"Using organization from base address: {org_name}")
                else:
                    raise RuntimeError(
                        "Could not determine organization. Please specify organization in the baseurl."
                    )
        else:
            # For on-premises, get collections via API
            collections_url = f"{self.baseurl}/_apis/projectcollections?api-version={self.api_version}"
            collections_response = self.session.get(collections_url)

            if collections_response.status_code == 200:
                collections_json = collections_response.json()
                for collection in collections_json.get("value", []):
                    collections.append(
                        AzureDevOpsCollection(
                            id=collection["id"],
                            name=collection["name"],
                            url=collection["url"],
                        )
                    )
            else:
                raise RuntimeError(
                    f"Failed to retrieve collections. Status Code: {collections_response.status_code} Response: {collections_response.text}"
                )

        logger.debug(f"Found {len(collections)} collections/organizations")
        return collections

    def _get_web_url_from_api_url(self, api_url, project_name):
        """
        Convert an API URL to a web-accessible URL

        Parameters:
            api_url (str): API URL for the project
            project_name (str): Name of the project

        Returns:
            str: Web URL for the project
        """
        if self.is_cloud_ado:
            # For cloud ADO, convert URL like:
            # https://dev.azure.com/org-name/_apis/projects/project-id
            # to: https://dev.azure.com/org-name/project-name
            match = re.search(r"https://dev\.azure\.com/([^/]+)", api_url)
            if match:
                org_name = match.group(1)
                return f"https://dev.azure.com/{org_name}/{project_name}"
        else:
            # For on-premises ADO, convert URL like:
            # https://server/collection/_apis/projects/project-id
            # to: https://server/collection/project-name
            base_url = api_url.split("/_apis/projects")[0]
            return f"{base_url}/{project_name}"

    def _get_repo_web_url(self, api_url, project_name):
        """
        Generate web-accessible URL for repositories page

        Parameters:
            api_url (str): API URL for the project
            project_name (str): Name of the project

        Returns:
            str: Web URL for the project's repositories page
        """
        project_web_url = self._get_web_url_from_api_url(api_url, project_name)
        return f"{project_web_url}/_git"

    def _get_all_projects(
        self, collections: List[AzureDevOpsCollection] = None
    ) -> List[AzureDevOpsProject]:
        """
        Get all projects from the provided collections or from all collections if none are provided

        Parameters:
        collections (List[AzureDevOpsCollection]): List of collections to get projects from
        """
        if collections is None:
            collections = self._get_all_collections()

        projects = []
        for collection in collections:
            collection_url = (
                f"https://dev.azure.com/{collection.name}"
                if self.is_cloud_ado
                else f"{self.baseurl}/{collection.name}"
            )
            logger.debug("Getting projects from collection: %s", collection_url)

            top = 100
            project_skip = 0
            total_projects = 0
            has_more_projects = True

            while has_more_projects:
                url = f"{collection_url}/_apis/projects?$top={top}&$skip={project_skip}&api-version={self.api_version}&includeCapabilities=true"

                response = self.session.get(url)
                if response.status_code != 200:
                    raise RuntimeError(
                        f"Failed to get projects: {response.status_code}"
                    )

                result = response.json()
                for project in result.get("value", []):
                    project_api_url = project.get("url")
                    project_name = project.get("name")

                    project_web_url = self._get_web_url_from_api_url(
                        project_api_url, project_name
                    )
                    repo_web_url = self._get_repo_web_url(project_api_url, project_name)

                    projects.append(
                        AzureDevOpsProject(
                            project_id=project.get("id"),
                            project_name=project_name,
                            project_description=project.get("description") or "",
                            project_url=project_web_url,
                            repo_url=repo_web_url,
                            project_create_time="",  # Not provided in API response
                            project_last_update_time=project.get("lastUpdateTime"),
                            collection_or_org_name=collection.name,
                        )
                    )

                count = len(result.get("value", []))
                total_projects += count
                project_skip += top

                has_more_projects = count == top

        return projects
