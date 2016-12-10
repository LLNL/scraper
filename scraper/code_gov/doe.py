#! /usr/bin/env python
# -*- coding: UTF-8 -*-

def to_doe_csv(project):
    """
    Returns a comma separated string containing the following information

    Headers from DOE Data Call:
        - Agency
        - Secretary Level
        - Program Office
        - Program/Office Component
        - Project Name
        - Project Description
        - URL to Project License
        - Is the Project Open source?
        - Is Project Built for Government-Wide Reuse?
        - Government-Wide Reuse Exemption Type
        - Project Tags
        - Project Point of Contact's Email
        - Project Point of Contact's Name
        - Project's Twitter URL
        - Project Point of Contact's Phone Number
        - Project Status
        - Version Control System
        - URL of the Public Project Repository
        - URL of the Public Project Homepage
        - URL to Download a Distribution of the Project
        - Programming Languages Utilized
        - Names of Project's Partnering Agencies
        - Partner Agencies' Project Email
        - Date of Last Metadata Updated
        - Date of Last Commit to Project Repository
        - Last Modified Date of Source Code or Package
    """
    return ';'.join([
        '',
        '',
        '',
        '',
        str(project['name']),
        str(project['description']),
        str(project['license']),
        str(project['openSourceProject']),
        str(project['governmentWideReuseProject']),
        str(project['exemption']),
        str(project['tags']),
        str(project['contact']['email']),
        str(project['contact']['name']),
        str(project['contact']['twitter']),
        str(project['contact']['phone']),
        str(project['status']),
        str(project['vcs']),
        str(project['repository']),
        str(project['homepage']),
        str(project['downloadURL']),
        str(project['languages']),
        str(project['partners']),
        str(project['partners']),
        str(project['updated']['metadataLastUpdated']),
        str(project['updated']['lastCommit']),
        str(project['updated']['sourceCodeLastModified']),
    ])
