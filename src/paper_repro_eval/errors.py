"""Domain errors with concise CLI-facing messages."""


class PaperReproEvalError(Exception):
    """Base class for expected framework errors."""


class ConfigurationError(PaperReproEvalError):
    """A manifest or repository configuration is invalid."""


class IntegrityError(PaperReproEvalError):
    """A path, digest, or isolation invariant was violated."""


class StateTransitionError(PaperReproEvalError):
    """A run lifecycle operation is invalid in the current state."""


class EvaluationError(PaperReproEvalError):
    """Evaluation infrastructure failed independently of candidate behavior."""
