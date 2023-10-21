class S3GetObjectError(Exception):
    pass


class FileNotFound(S3GetObjectError):
    pass


class FileIsEmpty(S3GetObjectError):
    pass
