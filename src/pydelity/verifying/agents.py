"""Page-break verification's agents: the judge and the verifier.

Each agent's output validator runs every check on each verdict, or on the verifier's
correction. While retries remain, a verdict that fails a check is sent back with a
message listing every failure. The verdict given at the last allowed attempt is
accepted as it is, and the caller records the checks it still fails. The validators
never compare a verdict with the hints, so a hint difference never sends a verdict
back.
"""

# Third Party Library
from loguru import logger
from pydantic_ai import Agent, ModelRetry, RunContext

# Package Library
from pydelity.extracting.schemas import PageFile
from pydelity.providers.factory import structured_output
from pydelity.providers.ledger_model import LedgerModel
from pydelity.verifying.schemas import BreakVerdict, BreakVerifierVerdict
from pydelity.verifying.validators import retry_message, run_checks


def _break_label(earlier: PageFile) -> str:
    """Name a break for log lines.

    Parameters
    ----------
    earlier
        The page file of the page before the break.

    Returns
    -------
    str
        Such as ``Break after page 4 (pages 4 and 5)``.
    """

    number = earlier.page_index + 1
    return f"Break after page {number} (pages {number} and {number + 1})"


def create_judge_agent(
    *,
    check_retries: int,
    earlier: PageFile,
    instructions: str,
    later: PageFile,
    model: LedgerModel,
) -> Agent[None, BreakVerdict]:
    """Create the agent that judges one break.

    Parameters
    ----------
    check_retries
        How many times the model may answer again. A verdict that does not match
        `BreakVerdict` also uses one.
    earlier
        The page file of the page before the break, which verdicts are checked
        against.
    instructions
        The judge's instructions.
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

    agent: Agent[None, BreakVerdict] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, BreakVerdict),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_verdict(run: RunContext[None], verdict: BreakVerdict) -> BreakVerdict:
        """Run the checks on a verdict and ask for a corrected one if it fails any.

        Parameters
        ----------
        run
            The run's context, for the retry count.
        verdict
            The judge's verdict.

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
        label = _break_label(earlier)
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
                "are left; keeping it and recording each failure for review",
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

    return agent


def create_verifier_agent(
    *,
    check_retries: int,
    earlier: PageFile,
    instructions: str,
    later: PageFile,
    model: LedgerModel,
) -> Agent[None, BreakVerifierVerdict]:
    """Create the agent that reviews one break's verdict.

    Its output validator runs every check on the verifier's correction, when it has
    one. A correction that still fails a check at the last attempt is accepted as it
    is, and the caller then keeps the judge's verdict.

    Parameters
    ----------
    check_retries
        How many times the verifier may answer again. An answer that does not match
        `BreakVerifierVerdict` also uses one.
    earlier
        The page file of the page before the break, which corrections are checked
        against.
    instructions
        The verifier's instructions.
    later
        The page file of the page after the break, which corrections are checked
        against.
    model
        The model, wrapped for this break and agent.

    Returns
    -------
    Agent[None, BreakVerifierVerdict]
        The agent, to be run once.
    """

    agent: Agent[None, BreakVerifierVerdict] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, BreakVerifierVerdict),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_review(
        run: RunContext[None], review: BreakVerifierVerdict
    ) -> BreakVerifierVerdict:
        """Run the checks on the verifier's correction and ask again if it fails any.

        Parameters
        ----------
        run
            The run's context, for the retry count.
        review
            The verifier's answer.

        Returns
        -------
        BreakVerifierVerdict
            The answer, when it has no correction, its correction passes every
            check, or no retries are left.

        Raises
        ------
        ModelRetry
            If the correction fails a check and retries remain.
        """

        label = _break_label(earlier)
        if review.corrected is None:
            logger.info(
                "{label}: the verifier {outcome}",
                label=label,
                outcome="passed the verdict"
                if review.passed
                else f"found {len(review.problems)} problems and gave no correction",
            )
            return review

        failures = run_checks(review.corrected, earlier, later)
        count = sum(len(found) for found in failures.values())
        if not count or run.last_attempt:
            logger.info(
                "{label}: the verifier found {problems} problems; its correction "
                "{outcome}",
                label=label,
                outcome="passed the checks"
                if not count
                else f"still has {count} check failures and no retries are left",
                problems=len(review.problems),
            )
            return review
        logger.info(
            "{label}: the verifier's correction has {count} check failures; asking "
            "it to fix them",
            count=count,
            label=label,
        )
        raise ModelRetry(
            "Your corrected verdict does not pass every check. Give the whole verdict "
            "again, with the correction fixed.\n" + retry_message(failures)
        )

    return agent
