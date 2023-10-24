# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import boto3
import os
from urllib.parse import urlsplit

from otcextensions.sdk import sdk_proxy
from otcextensions.sdk.s3.v1.container import Container


class Proxy(sdk_proxy.Proxy):
    skip_discovery = True

    def get_container_endpoint(self, region):
        """Override to return mapped endpoint if override and region are set

        """
        split_url = urlsplit(self.get_endpoint())

        return (f'{split_url.scheme}://{split_url.netloc}'
                % {'region_name': region})

    def get_boto3_client(self, region_name):
        endpoint = self.get_container_endpoint(region_name)
        ak, sk = self._set_ak_sk_keys()
        s3_client = boto3.client(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=ak,
            aws_secret_access_key=sk,

        )
        return s3_client

    def _set_ak_sk_keys(self):
        conn = self.session._sdk_connection
        if hasattr(conn, 'get_ak_sk'):
            (ak, sk) = conn.get_ak_sk(conn)
        if not (ak and sk):
            self.log.error('Cannot obtain AK/SK from config')
            return None
        return ak, sk

    # ======== Containers ========

    def containers(self, region, **query):
        """Obtain Container objects for this account.

        :param kwargs query: Optional query parameters to be sent to limit
                                 the resources being returned.

        :returns: List of containers
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.list_buckets()
        buckets = response.get('Buckets')
        for bucket in buckets:
            container = Container.new()
            yield container._translate_container_response(bucket)

    def create_container(self, container_name, region, **kwargs):
        """Create a new container from attributes

        :param container_name: Bucket to create
        :param region: String region to create bucket in, e.g., 'eu-de'
        :param kwargs: Could be ACL, GrantFullControl, GrantRead,
            GrantReadACP, GrantWrite, GrantWrite, ObjectLockEnabledForBucket,
            ObjectOwnership
        :returns: The results of container creation
        """
        s3_client = self.get_boto3_client(region)
        location = {'LocationConstraint': region}
        response = s3_client.create_bucket(Bucket=container_name,
                                           CreateBucketConfiguration=location,
                                           **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def get_container(self, container_name, region, **kwargs):
        """Get container

        :param container_name: Bucket to get
        :param region: Region , e.g., 'eu-de'
        :param kwargs: Additional params
        :returns: The result of container get
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.head_bucket(Bucket=container_name,
                                         **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def delete_container(self, container_name, region):
        """Delete a container

        :returns: ``None``
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.delete_bucket(Bucket=container_name)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 204:
                container = Container.new()
                return container._translate_response(response)
        return response

    def get_container_acl(self, container_name, region, **kwargs):
        """Get bucket acl

        :param container_name: Bucket to create
        :param kwargs: Could be ExpectedBucketOwner- the account ID of the
            expected bucket owner.
        :param region: String region to create bucket in, e.g., 'eu-de'
        :returns: The results of container creation
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.get_bucket_acl(Bucket=container_name, **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def put_container_acl(self, container_name, region,
                          **kwargs):
        """Put acl to bucket

        :param container_name: Bucket to create
        :param acl: The canned ACL to apply to the bucket
        :param access_control_policy: Contains the elements that set the ACL
            permissions for an object per grantee.
        :param region: String region to create bucket in, e.g., 'eu-de'
        :param kwargs: Could be ACL, AccessControlPolicy, ChecksumAlgorithm,
            GrantFullControl, GrantRead, GrantReadACP, GrantWrite,
            GrantWriteACP, ExpectedBucketOwner
        :returns: The results of container creation
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.put_bucket_acl(Bucket=container_name,
                                            **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def put_container_policy(self, container_name, policy, region, **kwargs):
        """Apply policy to container

        :param container_name: Bucket name
        :param region: String region to create bucket in, e.g., 'eu-de'
        :param policy: The bucket policy as a JSON document.
        :param kwargs: Can be ChecksumAlgorithm, ConfirmRemoveSelfBucketAccess,
            ExpectedBucketOwner
        :returns: The results of operation
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.put_bucket_policy(Bucket=container_name,
                                               Policy=policy,
                                               **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def get_container_policy(self, container_name, region, **kwargs):
        """Get policy to container

        :param container_name: Bucket name
        :param region: String region in, e.g., 'eu-de'
        :param kwargs: Can only be ExpectedBucketOwner
        :returns: The results of operation
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.get_bucket_policy(Bucket=container_name,
                                               **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 200:
                container = Container.new()
                return container._translate_response(response)
        return response

    def delete_container_policy(self, container_name, region, **kwargs):
        """Delete policy to container

        :param container_name: Bucket name
        :param region: String region, e.g., 'eu-de'
        :param kwargs: Can only be ExpectedBucketOwner
        :returns: The results of operation
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.delete_bucket_policy(Bucket=container_name,
                                                  **kwargs)
        if response.get('ResponseMetadata'):
            if response.get('ResponseMetadata').get('HTTPStatusCode',
                                                    None) == 204:
                container = Container.new()
                return container._translate_response(response)
        return response

    # ======== Objects ========

    def objects(self, container_name, region, **kwargs):
        """List objects.

        :param container_name: Container name
        :param region: String region, e.g., 'eu-de'
        :param kwargs: Additional params
        """

        s3_client = self.get_boto3_client(region)
        response = s3_client.list_objects(
            Bucket=container_name, **kwargs
        )
        return response

    def upload_object(self, container_name, file_name, region,
                      key=None, **kwargs):
        """Upload a file to an S3 bucket

        :param container_name: Container name to upload to
        :param file_name: File to upload
        :param region: String region, e.g., 'eu-de'
        :param key: S3 object name. If not specified then file_name is used
        :param kwargs: Additional parameters
        :return: True if file was uploaded, else False
        """

        if key is None:
            key = os.path.basename(file_name)

        s3_client = self.get_boto3_client(region)
        response = s3_client.upload_file(Fileobj=file_name,
                                         Bucket=container_name,
                                         Key=key, **kwargs)
        return response

    def download_object(self, file_name, container_name, region,
                        key=None):
        """Upload a file to an S3 bucket

        :param file_name: A file-like object to download into.
        :param container_name: Container name to download from.
        :param key: S3 object name to download.
        :return: True if file was uploaded, else False
        """

        s3_client = self.get_boto3_client(region)
        with open(file_name, 'wb') as f:
            s3_client.download_fileobj(container_name, key, f)
        return

    def copy_object(self, container_name, copy_source, key, region, acl=None,
                    **kwargs):
        """Copy an object.

        :param container_name: Container name
        :param copy_source: The name of the source bucket.
        :param key: The key of the destination object.
        :param kwargs: Can be CacheControl, ChecksumAlgorithm,
            ChecksumAlgorithm, ContentEncoding, ContentLanguage, ContentType,
            CopySourceIfMatch, CopySourceIfModifiedSince,
            CopySourceIfNoneMatch, CopySourceIfUnmodifiedSince, Expires,
            GrantFullControl, GrantRead, GrantReadACP, GrantWriteACP,
            Metadata and etc
        """

        if acl:
            kwargs['ACL'] = acl
        s3_client = self.get_boto3_client(region)
        response = s3_client.copy_object(
            Bucket=container_name,
            CopySource=copy_source,
            Key=key,
            **kwargs
        )
        return response

    def upload_part_copy(self, container_name, copy_source,
                         key, part_number, upload_id, region, **kwargs):
        """Uploads a part by copying data from an existing object as data
            source.

        :param container_name: Container name
        :param copy_source: The name of the source bucket.
        :param key: The key of the destination object.
        :param part_number: Part number of part being copied.
        :param upload_id: Upload ID identifying the multipart upload whose
            part is being copied.
        :param kwargs: Additional parameters.
        """

        s3_client = self.get_boto3_client(region)
        response = s3_client.upload_part_copy(
            Bucket=container_name,
            CopySource=copy_source,
            PartNumber=part_number,
            UploadId=upload_id,
            Key=key,
            **kwargs
        )
        return response

    def get_object(self, container_name, key, region, **kwargs):
        """Copy an object.

        :param container_name: Container name
        :param key: Key of the object to get.
        :param kwargs: Additional parameters.
        """

        s3_client = self.get_boto3_client(region)
        response = s3_client.get_object(
            Bucket=container_name,
            Key=key,
            **kwargs
        )
        return response

    def delete_object(self, container_name, key, region, **kwargs):
        """Delete a object

        :param container_name: Container name
        :param key: Key of the object to delete.
        :param kwargs: Additional parameters.
        :returns: ``None``
        """
        s3_client = self.get_boto3_client(region)
        response = s3_client.delete_object(Bucket=container_name, Key=key)
        return response
