"""The survey's agents: the survey model and its verifier.

Each agent's output validator runs checks C1 to C7 on each answer, or on the
verifier's correction. While retries remain, an answer that fails a check is sent back
with a message listing every failure. The answer to the last allowed attempt is
accepted as it is, and the caller records the checks it still fails.
"""

# Third Party Library
from loguru import logger
from pydantic_ai import Agent, ModelRetry, RunContext

# Package Library
from pydelity.providers.factory import structured_output
from pydelity.providers.ledger_model import LedgerModel
from pydelity.surveying.schemas import Facts, SurveyAnswer, SurveyVerdict
from pydelity.surveying.validators import retry_message, run_checks


def create_survey_agent(
    *, check_retries: int, facts: Facts, instructions: str, model: LedgerModel
) -> Agent[None, SurveyAnswer]:
    """Create the agent that surveys one PDF.

    Its output validator runs checks C1 to C7 on each answer. While retries remain, an
    answer that fails a check is sent back with a message listing every failure. The
    answer to the last allowed attempt is accepted as it is, and the caller records
    the checks it still fails as review issues.

    Parameters
    ----------
    check_retries
        How many times the model may answer again. An answer that does not match
        `SurveyAnswer` also uses one.
    facts
        The measured facts the answers are checked against.
    instructions
        The survey's instructions to the model.
    model
        The step's model.

    Returns
    -------
    Agent[None, SurveyAnswer]
        The agent, to be run once.
    """

    agent: Agent[None, SurveyAnswer] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, SurveyAnswer),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_answer(context: RunContext[None], answer: SurveyAnswer) -> SurveyAnswer:
        """Run the checks on an answer and ask for a corrected one if it fails any.

        Parameters
        ----------
        context
            The run's context, for the retry count.
        answer
            The model's answer.

        Returns
        -------
        SurveyAnswer
            The answer, when it passes every check or no retries are left.

        Raises
        ------
        ModelRetry
            If the answer fails a check and retries remain.
        """

        failures = run_checks(answer, facts)
        count = sum(len(found) for found in failures.values())
        number = context.retry + 1
        if not count:
            logger.info("Survey answer {number} passed the checks", number=number)
            return answer

        for found in failures.values():
            for failure in found:
                logger.debug("  {message}", message=failure.message)
        if context.last_attempt:
            logger.info(
                "Survey answer {number} has {count} check failures and no retries "
                "are left; keeping it and recording each failure for review",
                count=count,
                number=number,
            )
            return answer
        logger.info(
            "Survey answer {number} has {count} check failures; asking the model to "
            "fix them",
            count=count,
            number=number,
        )
        raise ModelRetry(retry_message(failures))

    return agent


def create_verifier_agent(
    *, check_retries: int, facts: Facts, instructions: str, model: LedgerModel
) -> Agent[None, SurveyVerdict]:
    """Create the agent that reviews the survey of one PDF.

    Its output validator runs checks C1 to C7 on a verdict's correction, when it has
    one. A verdict whose correction still fails on the last attempt is accepted as it
    is; the caller then keeps the survey's answer.

    Parameters
    ----------
    check_retries
        How many times the verifier may answer again. A verdict that does not match
        `SurveyVerdict` also uses one.
    facts
        The measured facts corrections are checked against.
    instructions
        The verifier's instructions.
    model
        The step's model, wrapped for the verifier.

    Returns
    -------
    Agent[None, SurveyVerdict]
        The agent, to be run once.
    """

    agent: Agent[None, SurveyVerdict] = Agent(
        model,
        instructions=instructions,
        output_type=structured_output(model, SurveyVerdict),
        retries={"output": check_retries},
    )

    @agent.output_validator
    def check_verdict(
        context: RunContext[None], verdict: SurveyVerdict
    ) -> SurveyVerdict:
        """Run the checks on a verdict's correction and ask again if it fails any.

        Parameters
        ----------
        context
            The run's context, for the retry count.
        verdict
            The verifier's verdict.

        Returns
        -------
        SurveyVerdict
            The verdict, when it has no correction, its correction passes every
            check, or no retries are left.

        Raises
        ------
        ModelRetry
            If the correction fails a check and retries remain.
        """

        if verdict.corrected is None:
            logger.info(
                "The survey's verifier {outcome}",
                outcome="passed the survey"
                if verdict.passed
                else f"found {len(verdict.problems)} problems and gave no correction",
            )
            return verdict

        failures = run_checks(verdict.corrected, facts)
        count = sum(len(found) for found in failures.values())
        if not count or context.last_attempt:
            logger.info(
                "The survey's verifier found {problems} problems; its correction "
                "{outcome}",
                outcome="passed the checks"
                if not count
                else f"still has {count} check failures and no retries are left",
                problems=len(verdict.problems),
            )
            return verdict
        for found in failures.values():
            for failure in found:
                logger.debug("  {message}", message=failure.message)
        logger.info(
            "The survey verifier's correction has {count} check failures; asking it "
            "to fix them",
            count=count,
        )
        raise ModelRetry(
            "Your corrected survey does not pass every check. Give the whole verdict "
            "again, with the correction fixed.\n" + retry_message(failures)
        )

    return agent
