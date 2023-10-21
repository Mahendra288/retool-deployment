import enum


class EnvironmentEnum(enum.Enum):
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    STAGING = "staging"
    PROD = "prod"


class S3BucketACLPermissions(enum.Enum):
    PUBLIC_READ = "public-read"
    PRIVATE = "private"

