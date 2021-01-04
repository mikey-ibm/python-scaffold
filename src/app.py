"""
This module provides the functionality of uploading files from s3 to an FTP
server.
"""

import base64
import json
import logging
import os

import boto3
import paramiko
from botocore.exceptions import ClientError
from exceptions import BinarySecretError, InvalidAuthTypeError

SECRET_KEY = os.getenv("SECRET_KEY")
VERSION = 1.0
PYTHONUNBUFFERED = True
AWS_REGION = os.getenv("AWS_REGION")
CHUNKSIZE = os.getenv("CHUNKSIZE")
CONCURRENCY = os.getenv("CONCURRENCY")
AUTH_METHOD = os.getenv("AUTH_METHOD")
FILE_LIST = os.getenv("FILE_LIST")
PROFILE = os.getenv("PROFILE")
THRESHOLD = os.getenv("THRESHOLD")
SECRET_ARN = os.getenv("SECRET_ARN")
# SESSION = boto3.Session(profile_name=PROFILE)  # use this for development
SESSION = boto3.Session()  #


def get_module_logger(mod_name):
    """
    To use this, do logger = get_module_logger(__name__)
    This function sets up consistent log formatting for the module
    """
    logger = logging.getLogger(mod_name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger


LOGGER = get_module_logger(__name__)


def bail_out(return_code):
    """
    Single point of exit for exceptions
    @param return_code: int representing a non-zero value for error condition
    @return:
    """
    LOGGER.error("System Bailing Out with return code%s", return_code)
    SystemExit(return_code)


def create_aws_client(self, client_type):
    """

    :return:
    """
    client = SESSION.client(service_name=client_type, region_name="us-east-1")
    return client


# SESSION = boto3.Session(profile_name=PROFILE)  # use this for development
# SESSION = boto3.Session()  #


class S3Ftp:
    def __init__(self):
        LOGGER.info("S3Ftp Class Initializing")

        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.sftp_client = None
        self.ssh_ok = False
        self.sftp_ok = False
        self.sftp_host = None
        self.sftp_port = None
        self.public_key = None
        self.private_key = None
        self.sftp_username = None
        self.ftp_password = None
        self.sftp_directory_path = None
        self.s3_bucket_name = None
        LOGGER.info("Getting Secrets")
        self.auth_status = self.get_auth_type(AUTH_METHOD)
        self.get_secret()

    def get_auth_type(option):
        """
        Returns a string representing the valid authorization type.
        Parameters:
        option (str): A string
        Returns:
        option (boolean): Returns True if the option is valid
        """
        if option == "BASIC":

            result = True

            print("\nAuth method is  = ", result)

        elif option == "KEY_PAIR":
            result = True

            print("\nAuth method is  = ", result)

        else:

            raise InvalidAuthTypeError(option)

        return option

        auth_type = AUTH_METHOD
        return auth_type

    def create_sftp_client(host, port):
        """
        :return: paramiko.SFTPClient
        """
        transport = paramiko.Transport((host, port))
        transport.default_window_size = paramiko.common.MAX_WINDOW_SIZE
        transport.packetizer.REKEY_BYTES = pow(2, 40)
        transport.packetizer.REKEY_PACKETS = pow(2, 40)
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)
        except paramiko.SFTPError as sftp_error:
            LOGGER.error(
                "Error at %s",
                "Could not establish sftp connection",
                exc_info=sftp_error,
            )
            bail_out(1)

        return sftp

    def get_secrets(self):
        """
        This method retrieves secrets from AWS Secrets Manager
        @return: voic
        """
        LOGGER.info("Invoking secrets manager")
        ssm_client = "secretsmanager"

        try:
            LOGGER.info("trying for secret value response")
            # pylint: disable=no-member
            # this is a call to a c library function that pylint misses
            get_secret_value_response = ssm_client.get_secret_value(SecretId=SECRET_ARN)

        except ClientError as error:
            if error.response["Error"]["Code"] == "DecryptionFailureException":
                LOGGER.error(
                    "Error at %s", "DecryptionFailureException", exc_info=error
                )
                # print("ClientError: %s" % error)
                bail_out(1)
                raise error

            if error.response["Error"]["Code"] == "InternalServiceErrorException":
                LOGGER.error(
                    "Error at %s", "InternalServiceErrorException", exc_info=error
                )
                # print("ClientError: %s" % e)
                bail_out(1)
                raise error

            if error.response["Error"]["Code"] == "InvalidParameterException":
                LOGGER.error("Error at %s", "InvalidParameterException", exc_info=error)
                # print("ClientError: %s" % e)
                bail_out(1)
                raise error

            if error.response["Error"]["Code"] == "InvalidRequestException":
                LOGGER.error("Error at %s", "InvalidRequestException", exc_info=error)
                # print("ClientError: %s" % e)
                bail_out(1)

            if error.response["Error"]["Code"] == "ResourceNotFoundException":
                LOGGER.error("Error at %s", "ResourceNotFoundException", exc_info=error)
                # print("ClientError: %s" % e)
                bail_out(1)
        else:

            LOGGER.debug("Call to SSM successful")
            if "SecretString" in get_secret_value_response:
                secret = get_secret_value_response["SecretString"]
                self.private_key = json.loads(secret)["privateKey"]
                self.public_key = json.loads(secret)["publicKey"]
                self.sftp_host = json.loads(secret)["hostName"]
                self.sftp_port = json.loads(secret)["portNumber"]
                self.sftp_username = json.loads(secret)["userName"]
                self.ftp_password = json.loads(secret)["password"]
                self.sftp_directory_path = json.loads(secret)["directoryPath"]
                self.sftp_port = json.loads(secret)["portNumber"]
                self.s3_bucket_name = json.loads(secret)["s3BucketName"]
                # enable this if password auth is used and the value exists
                # in secrets manager

            else:
                raise BinarySecretError()

    def s3_transfer_file(self):
        s3_client = boto3.client("s3", region_name="us-east-1")
        sftp = self.create_sftp_client(self.sftp_host, self.sftp_port)
        try:
            with sftp.open("/sftp/path/filename", "wb", 32768) as f:
                s3_client.download_fileobj("mybucket", "mykey", f)
        except Exception as ex:
            LOGGER.error(("Error at %s", "FileTransferException", ex))

    def create_file_list(self):
        """

        :return: Python list of files to be uploaded
        """

        file_list = [1, 2, 3]
        return file_list


# Press the green button in the gutter to run the script.
if __name__ == "__main__":
    print("foo")
