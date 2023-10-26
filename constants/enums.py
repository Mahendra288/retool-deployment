import enum


class EnvironmentEnum(enum.Enum):
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    STAGING = "staging"
    PROD = "prod"

    @classmethod
    def get_list_of_values(cls):
        return [each.value for each in cls]


class S3BucketACLPermissions(enum.Enum):
    PUBLIC_READ = "public-read"
    PRIVATE = "private"

