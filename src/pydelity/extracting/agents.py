"""Page extraction's agents: the extraction model and the verifier.

Each agent's output validator runs every check on each answer, or on the verifier's
correction. While retries remain, an answer that fails a check is sent back with a
message listing every failure. The answer to the last allowed attempt is accepted as
it is, and the caller records the checks it still fails. The validators never compare
an answer with the hints, so a hint difference never sends an answer back.
"""

# Standard Library

# Third Party Library
from loguru import logger
from pydantic_ai import Agent, ModelRetry, RunContext

# Package Library
from pydelity.extracting.schemas import PageAnswer, PageContext, VerifierVerdict
from pydelity.extracting.text_layer import PageText
from pydelity.extracting.validators import retry_message, run_checks
from pydelity.providers.factory import structured_output
from pydelity.providers.ledger_model import LedgerModel


def _page_label(context: PageContext) -> str:
    """Name a page for log lines.

    Parameters
    ----------
    context
        The page's context.

    Returns
    -------
    str
        Such as ``Page 4 (index 3)``.
    """

    return f"Page {context.page_index + 1} (index {context.page_index})"


def create_extraction_agent(
    *,
    check_retries: int,
    context: PageContext,
    instructions: str,
    model: LedgerModel,
    page_text: PageText,
) -> Agent[None, PageAnswer]:
    """Create the agent that extracts one page.

    Parameters
    ----------
    check_retries
        How many times the model may answer again. An answer that does not match
        `PageAnswer` also uses one.
    context
        The page's context, which the answers are checked against.
    instructions
        The extraction model's instructions.
    model
        The model, wrapped for this page and agent.
    page_text
        The page's text layer, which the checks are given.

    Returns
    -------
    Agent[None, PageAnswer]
        The agent, to be run once.
    """

    agent: Agent[None, PageAnswer] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, PageAnswer),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_answer(run: RunContext[None], answer: PageAnswer) -> PageAnswer:
        """Run the checks on an answer and ask for a corrected one if it fails any.

        Parameters
        ----------
        run
            The run's context, for the retry count.
        answer
            The model's answer.

        Returns
        -------
        PageAnswer
            The answer, when it passes every check or no retries are left.

        Raises
        ------
        ModelRetry
            If the answer fails a check and retries remain.
        """

        failures = run_checks(answer, context, page_text)
        count = sum(len(found) for found in failures.values())
        label = _page_label(context)
        number = run.retry + 1
        if not count:
            logger.info(
                "{label}: answer {number} passed the checks", label=label, number=number
            )
            return answer

        for found in failures.values():
            for failure in found:
                logger.debug("  {message}", message=failure.message)
        if run.last_attempt:
            logger.info(
                "{label}: answer {number} has {count} check failures and no retries "
                "are left; keeping it and recording each failure for review",
                count=count,
                label=label,
                number=number,
            )
            return answer
        logger.info(
            "{label}: answer {number} has {count} check failures; asking the model "
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
    context: PageContext,
    instructions: str,
    model: LedgerModel,
    page_text: PageText,
) -> Agent[None, VerifierVerdict]:
    """Create the agent that reviews one page's extraction.

    Its output validator runs every check on a verdict's correction, when it has
    one. A verdict whose correction still fails on the last attempt is accepted as
    it is; the caller then keeps the extraction.

    Parameters
    ----------
    check_retries
        How many times the verifier may answer again. A verdict that does not match
        `VerifierVerdict` also uses one.
    context
        The page's context, which corrections are checked against.
    instructions
        The verifier's instructions.
    model
        The model, wrapped for this page and agent.
    page_text
        The page's text layer, which the checks are given.

    Returns
    -------
    Agent[None, VerifierVerdict]
        The agent, to be run once.
    """

    agent: Agent[None, VerifierVerdict] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, VerifierVerdict),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_verdict(
        run: RunContext[None], verdict: VerifierVerdict
    ) -> VerifierVerdict:
        """Run the checks on a verdict's correction and ask again if it fails any.

        Parameters
        ----------
        run
            The run's context, for the retry count.
        verdict
            The verifier's verdict.

        Returns
        -------
        VerifierVerdict
            The verdict, when it has no correction, its correction passes every
            check, or no retries are left.

        Raises
        ------
        ModelRetry
            If the correction fails a check and retries remain.
        """

        label = _page_label(context)
        if verdict.corrected is None:
            logger.info(
                "{label}: the verifier {outcome}",
                label=label,
                outcome="passed the extraction"
                if verdict.passed
                else f"found {len(verdict.problems)} problems and gave no correction",
            )
            return verdict

        failures = run_checks(verdict.corrected, context, page_text)
        count = sum(len(found) for found in failures.values())
        if not count or run.last_attempt:
            logger.info(
                "{label}: the verifier found {problems} problems; its correction "
                "{outcome}",
                label=label,
                outcome="passed the checks"
                if not count
                else f"still has {count} check failures and no retries are left",
                problems=len(verdict.problems),
            )
            return verdict
        logger.info(
            "{label}: the verifier's correction has {count} check failures; asking "
            "it to fix them",
            count=count,
            label=label,
        )
        raise ModelRetry(
            "Your corrected extraction does not pass every check. Give the whole "
            "verdict again, with the correction fixed.\n" + retry_message(failures)
        )

    return agent
