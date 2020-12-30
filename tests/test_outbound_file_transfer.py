from paramiko import Channel
from pytest_sftpserver.sftp.server import SFTPServer


def test_create_bucket(s3):
    # s3 is a fixture defined above that yields a boto3 s3 client.
    # Feel free to instantiate another boto3 S3 client -- Keep note of the region though.
    s3.create_bucket(Bucket="somebucket")

    result = s3.list_buckets()
    assert len(result['Buckets']) == 1
    assert result['Buckets'][0]['Name'] == 'somebucket'


def test_get_auth_type():
    """
    Tests whether a value passed is an approved auth type.
    :return:
    """
    from outbound_file_transfer import get_auth_type
    result = get_auth_type('BASIC')
    assert result == 'BASIC'




def test_sftpserver_available(sftpserver):
    assert isinstance(sftpserver, SFTPServer)
    assert sftpserver.is_alive()
    assert str(sftpserver.port) in sftpserver.url

def test_sftpserver_connect(sftpclient):
    assert isinstance(sftpclient.sock, Channel)

def test_sftpserver_put_file_list(content, sftpclient):
    with sftpclient.open("/a/f/2", "w") as f:
        f.write("testfile7")
    assert set(sftpclient.listdir("/a/f")) == set(["0", "1", "2"])
