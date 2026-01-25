"""LLM integration for TaskMan using the llms library."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from pydantic import BaseModel, Field

from taskman.config import get_config
from taskman.export import task_to_prompt_format
from taskman.policy import Policy
from taskman.uda import format_uda_prompt_reference, get_uda_names

if TYPE_CHECKING:
    from taskdantic import Task as TaskdanticTask
else:
    TaskdanticTask = Any


class AnalysisResult(BaseModel):
    """Result of analyzing a task."""

    uuid: str
    summary: str = Field(description="Brief summary of the task analysis")
    insights: list[str] = Field(
        default_factory=list,
        description="Key insights about the task",
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Suggestions for improving or clarifying the task",
    )
    missing_context: list[str] = Field(
        default_factory=list,
        description="What context or information is missing",
    )
    priority_assessment: str | None = Field(
        default=None,
        description="Assessment of whether priority is appropriate",
    )
    next_actions: list[str] = Field(
        default_factory=list,
        description="Suggested next actions",
    )


class ReviseOutput(BaseModel):
    """Output from a revise operation."""

    analysis: str = Field(description="Analysis of what needs to change and why")
    revise_script: str = Field(description="Revise script with task commands")
    rationale: str = Field(description="Rationale for the proposed changes")


class BatchAnalysisResult(BaseModel):
    """Result of batch analyzing multiple tasks."""

    total_tasks: int
    analyses: list[AnalysisResult]
    global_insights: list[str] = Field(
        default_factory=list,
        description="Insights across all tasks",
    )
    consistency_issues: list[str] = Field(
        default_factory=list,
        description="Consistency issues found across tasks",
    )


class PromptBuilder:
    """Builder for LLM prompts."""

    def __init__(self, registry: Any | None = None, policy: Policy | None = None):
        """Initialize prompt builder.

        Args:
            registry: UDA registry for reference
            policy: Safety policy for constraints
        """
        self.registry = registry
        self.policy = policy

    def build_analyze_prompt(self, task: TaskdanticTask) -> str:
        """Build a prompt for analyzing a task.

        Args:
            task: Task to analyze

        Returns:
            Prompt string
        """
        sections = [
            "# Task Analysis Request",
            "",
            "Please analyze the following task and provide insights.",
            "",
            "## Task",
            task_to_prompt_format(task),
            "",
        ]

        if self.registry:
            sections.extend(
                [
                    "## Available UDAs",
                    format_uda_prompt_reference(self.registry),
                    "",
                ]
            )

        sections.extend(
            [
                "## Instructions",
                "- Identify what's clear and what's missing",
                "- Assess whether priority and due date are appropriate",
                "- Suggest concrete next actions",
                "- Note any missing context that would help",
                "- Consider which UDAs could add useful structure",
            ]
        )

        return "\n".join(sections)

    def build_revise_prompt(self, task: TaskdanticTask) -> str:
        """Build a prompt for revising a task.

        Args:
            task: Task to revise

        Returns:
            Prompt string
        """
        sections = [
            "# Task Revision Request",
            "",
            "Please propose changes to improve this task.",
            "",
            "## Current Task",
            task_to_prompt_format(task),
            "",
        ]

        if self.registry:
            sections.extend(
                [
                    "## Available UDAs",
                    format_uda_prompt_reference(self.registry),
                    "",
                ]
            )

        if self.policy:
            sections.extend(
                [
                    "## Safety Policy",
                    f"Mode: {self.policy.mode.value}",
                    f"Allowed fields: {self.policy.get_allowed_fields_description(get_uda_names(self.registry))}",
                    "",
                    "Forbidden operations:",
                    "- Modifying task description",
                    "- Deleting or purging tasks",
                    "- Mass operations without explicit selectors",
                    "",
                ]
            )

        sections.extend(
            [
                "## Revise Script Grammar",
                "",
                "Generate a revise script using only these commands:",
                "",
                "1. Modify fields:",
                "   task <uuid> modify <field_ops...>",
                "",
                "   Field operations:",
                "   - Set field: field:value",
                "   - Add tag: +tagname",
                "   - Remove tag: -tagname",
                "",
                "2. Add annotations:",
                "   task <uuid> annotate <text...>",
                "",
                "Rules:",
                "- One command per line",
                "- Use the task UUID, not ID",
                "- Only modify allowed fields",
                "- No shell features (pipes, redirection, etc.)",
                "- Quote values with spaces",
                "",
                "## Output Format",
                "",
                "Provide:",
                "1. Analysis: What needs to change and why",
                "2. Revise script: The actual commands",
                "3. Rationale: Why these changes improve the task",
            ]
        )

        return "\n".join(sections)

    def build_batch_analyze_prompt(
        self,
        tasks: list[TaskdanticTask],
        global_invariants: dict[str, Any] | None = None,
    ) -> str:
        """Build a prompt for batch analyzing tasks.

        Args:
            tasks: List of tasks to analyze
            global_invariants: Global conventions and heuristics

        Returns:
            Prompt string
        """
        sections = [
            "# Batch Task Analysis",
            "",
            f"Please analyze {len(tasks)} tasks for consistency and improvements.",
            "",
        ]

        if global_invariants:
            sections.extend(
                [
                    "## Global Conventions",
                    "",
                ]
            )
            for key, value in global_invariants.items():
                sections.append(f"- {key}: {value}")
            sections.append("")

        if self.registry:
            sections.extend(
                [
                    "## Available UDAs",
                    format_uda_prompt_reference(self.registry),
                    "",
                ]
            )

        sections.extend(
            [
                "## Tasks",
                "",
            ]
        )

        for i, task in enumerate(tasks, start=1):
            sections.append(f"### Task {i}")
            sections.append(task_to_prompt_format(task))
            sections.append("")

        sections.extend(
            [
                "## Instructions",
                "",
                "For each task:",
                "- Analyze clarity and completeness",
                "- Check consistency with conventions",
                "- Identify missing information",
                "- Suggest improvements",
                "",
                "Across all tasks:",
                "- Note inconsistencies in tagging, projects, or naming",
                "- Identify patterns or anti-patterns",
                "- Suggest systemic improvements",
            ]
        )

        return "\n".join(sections)


def analyze_task(
    task: TaskdanticTask,
    registry: UDARegistry | None = None,
    policy: Policy | None = None,
) -> AnalysisResult:
    """Analyze a task using LLM.

    Args:
        task: Task to analyze
        registry: UDA registry for reference
        policy: Safety policy (optional)

    Returns:
        AnalysisResult

    Note:
        This is a placeholder implementation. The actual implementation will:
        1. Use the llms library to call the LLM
        2. Request structured output (AnalysisResult model)
        3. Handle retries/repairs using library features
    """
    config = get_config()
    builder = PromptBuilder(registry=registry, policy=policy)
    prompt = builder.build_analyze_prompt(task)

    # TODO: Integrate with llms library
    # For now, return a placeholder
    if config.show_prompt:
        print("=== PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===\n")

    # Placeholder result
    return AnalysisResult(
        uuid=task.uuid,
        summary="Analysis not yet implemented - llms library integration pending",
        insights=["This is a placeholder"],
        suggestions=["Integrate llms library for actual analysis"],
    )


def revise_task(
    task: TaskdanticTask,
    registry: UDARegistry | None = None,
    policy: Policy | None = None,
) -> ReviseOutput:
    """Generate a revise script for a task using LLM.

    Args:
        task: Task to revise
        registry: UDA registry for reference
        policy: Safety policy

    Returns:
        ReviseOutput with script and rationale

    Note:
        This is a placeholder implementation. The actual implementation will:
        1. Use the llms library to call the LLM
        2. Request structured output (ReviseOutput model)
        3. Handle validation errors with retries
        4. Ensure script follows grammar
    """
    config = get_config()
    builder = PromptBuilder(registry=registry, policy=policy)
    prompt = builder.build_revise_prompt(task)

    # TODO: Integrate with llms library
    if config.show_prompt:
        print("=== PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===\n")

    # Placeholder result
    return ReviseOutput(
        analysis="Revise not yet implemented - llms library integration pending",
        revise_script=f"# Placeholder script\n# task {task.uuid} modify +needs-implementation",
        rationale="This is a placeholder until llms library is integrated",
    )


def batch_analyze(
    tasks: list[TaskdanticTask],
    registry: UDARegistry | None = None,
    policy: Policy | None = None,
    global_invariants: dict[str, Any] | None = None,
) -> BatchAnalysisResult:
    """Batch analyze multiple tasks using LLM.

    Args:
        tasks: List of tasks to analyze
        registry: UDA registry for reference
        policy: Safety policy (optional)
        global_invariants: Global conventions and heuristics

    Returns:
        BatchAnalysisResult

    Note:
        This is a placeholder implementation.
    """
    config = get_config()
    builder = PromptBuilder(registry=registry, policy=policy)
    prompt = builder.build_batch_analyze_prompt(tasks, global_invariants)

    # TODO: Integrate with llms library
    if config.show_prompt:
        print("=== PROMPT ===")
        print(prompt)
        print("=== END PROMPT ===\n")

    # Placeholder result - analyze each individually
    analyses = [
        analyze_task(task, registry=registry, policy=policy) for task in tasks
    ]

    return BatchAnalysisResult(
        total_tasks=len(tasks),
        analyses=analyses,
        global_insights=["Batch analysis not yet fully implemented"],
    )
