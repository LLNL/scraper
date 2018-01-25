#! /usr/bin/env python
# -*- coding: UTF-8 -*-

SEPARATOR = ';'


def to_cell(string):
    string = str(string)
    string = string.replace('\n', ' ')  # Newlines will break CSV cells
    string = string.replace('\r', ' ')  # Newlines will break CSV cells
    string = string.replace(SEPARATOR, '')
    return string


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
    return SEPARATOR.join([
        '',
        '',
        '',
        '',
        to_cell(project['name']),
        to_cell(project['description']),
        to_cell(project['license']),
        to_cell(project['openSourceProject']),
        to_cell(project['governmentWideReuseProject']),
        to_cell(project['exemption']),
        to_cell(project['tags']),
        to_cell(project['contact']['email']),
        to_cell(project['contact']['name']),
        to_cell(project['contact']['twitter']),
        to_cell(project['contact']['phone']),
        to_cell(project['status']),
        to_cell(project['vcs']),
        to_cell(project['repository']),
        to_cell(project['homepage']),
        to_cell(project['downloadURL']),
        to_cell(project['languages']),
        to_cell(project['partners']),
        to_cell(project['partners']),
        to_cell(project['updated']['metadataLastUpdated']),
        to_cell(project['updated']['lastCommit']),
        to_cell(project['updated']['sourceCodeLastModified']),
    ])
