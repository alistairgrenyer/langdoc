"""Custom exception hierarchy for LangDoc."""

class LangDocError(Exception):
    """Base exception for all LangDoc-related errors."""
    pass


class ConfigurationError(LangDocError):
    """Error related to configuration issues."""
    pass


class APIKeyError(ConfigurationError):
    """Error related to missing or invalid API keys."""
    pass


class DocumentationGenerationError(LangDocError):
    """Error occurring during documentation generation."""
    pass


class CodebaseAnalysisError(LangDocError):
    """Error occurring during codebase analysis."""
    pass


class VectorStoreError(LangDocError):
    """Error related to vector store operations."""
    pass


class FilesystemError(LangDocError):
    """Error related to filesystem operations."""
    pass
