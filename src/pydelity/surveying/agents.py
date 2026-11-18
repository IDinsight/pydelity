"""The survey's agent, whose output validator runs checks C1 to C7 on each answer."""

# Third Party Library
from loguru import logger
from pydantic_ai import Agent, ModelRetry, RunContext

# Package Library
from pydelity.providers.factory import structured_output
from pydelity.providers.ledger_model import LedgerModel
from pydelity.surveying.schemas import Facts, SurveyAnswer
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
