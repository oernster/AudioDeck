"""Switch lock interface."""

from typing import ContextManager, Protocol


class ISwitchLock(Protocol):
    """Interface for the per-user lock held for the length of a switch.

    The GUI and the CLI each hold it while they change the defaults, so two
    switches never interleave into a mix of both profiles.
    """

    def hold(self) -> ContextManager[None]:
        """Hold the lock for the body of a with statement.

        Raises:
            SwitchInProgressException: If another switch keeps it past the
                bounded wait
        """
        ...
