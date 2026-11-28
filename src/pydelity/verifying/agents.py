"""Page-break verification's agent, which the judge and the verifier both use.

The agent's output validator runs every check on each verdict. While retries remain,
a verdict that fails a check is sent back with a message listing every failure. The
verdict given at the last allowed attempt is accepted as it is, and the caller
records the checks it still fails. The validator never compares a verdict with the
hints, so a hint difference never sends a verdict back.
"""

# Third Party Library
from loguru import logger
from pydantic_ai import Agent, ModelRetry, RunContext

# Package Library
from pydelity.extracting.schemas import PageFile
from pydelity.providers.factory import structured_output
from pydelity.providers.ledger_model import LedgerModel
from pydelity.verifying.schemas import BreakVerdict
from pydelity.verifying.validators import retry_message, run_checks


def _break_label(earlier: PageFile, *, agent: str) -> str:
    """Name a break and the agent judging it for log lines.

    Parameters
    ----------
    earlier
        The page file of the page before the break.
    agent
        The agent's name, ``judge`` or ``verifier``.

    Returns
    -------
    str
        Such as ``Break after page 4 (pages 4 and 5), judge``.
    """

    number = earlier.page_index + 1
    return f"Break after page {number} (pages {number} and {number + 1}), {agent}"


def create_break_agent(  # noqa: PLR0913 - the agent's name, its pages and settings
    *,
    agent: str,
    check_retries: int,
    earlier: PageFile,
    instructions: str,
    later: PageFile,
    model: LedgerModel,
) -> Agent[None, BreakVerdict]:
    """Create the agent that judges one break, for the judge or the verifier.

    Parameters
    ----------
    agent
        The agent's name, ``judge`` or ``verifier``, for log lines.
    check_retries
        How many times the model may answer again. A verdict that does not match
        `BreakVerdict` also uses one.
    earlier
        The page file of the page before the break, which verdicts are checked
        against.
    instructions
        The request's instructions.
    later
        The page file of the page after the break, which verdicts are checked
        against.
    model
        The model, wrapped for this break and agent.

    Returns
    -------
    Agent[None, BreakVerdict]
        The agent, to be run once.
    """

    created: Agent[None, BreakVerdict] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, BreakVerdict),
        retries={"output": check_retries},
    )
    label = _break_label(earlier, agent=agent)

    @created.output_validator
    def check_verdict(run: RunContext[None], verdict: BreakVerdict) -> BreakVerdict:
        """Run the checks on a verdict and ask for a corrected one if it fails any.

        Parameters
        ----------
        run
            The run's context, for the retry count.
        verdict
            The model's verdict.

        Returns
        -------
        BreakVerdict
            The verdict, when it passes every check or no retries are left.

        Raises
        ------
        ModelRetry
            If the verdict fails a check and retries remain.
        """

        failures = run_checks(verdict, earlier, later)
        count = sum(len(found) for found in failures.values())
        number = run.retry + 1
        if not count:
            logger.info(
                "{label}: verdict {number} passed the checks",
                label=label,
                number=number,
            )
            return verdict

        for found in failures.values():
            for failure in found:
                logger.debug("  {message}", message=failure.message)
        if run.last_attempt:
            logger.info(
                "{label}: verdict {number} has {count} check failures and no retries "
                "are left; keeping it and recording each failure",
                count=count,
                label=label,
                number=number,
            )
            return verdict
        logger.info(
            "{label}: verdict {number} has {count} check failures; asking the model "
            "to fix them",
            count=count,
            label=label,
            number=number,
        )
        raise ModelRetry(retry_message(failures))

    return created
