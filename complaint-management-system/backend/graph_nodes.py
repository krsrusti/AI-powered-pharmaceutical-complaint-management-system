"""
LangGraph node functions.

Each node takes the current GraphState and returns a partial dict of updates,
which LangGraph merges into state before the next node runs. Nodes are kept
free of DB access — the router loads/saves data before and after invoking the
graph, so these functions stay pure and easy to test.

Node order (see graph_workflow.py):
  classify_input -> extract -> merge_state -> completeness_check
  -> duplicate_check -> risk_assessment
"""

from datetime import datetime
from typing import Any

from schemas import (
    Complaint,
    ComplaintCategory,
    RiskLevel,
    RiskAssessment,
    FieldDiff,
    FieldSource,
    CompletenessResult,
    DuplicateCheckResult,
    REQUIRED_FIELDS,
    RISK_RELEVANT_FIELDS,
)
from llm_client import call_fast_model, call_reasoning_model, LLMExtractionError
from prompts import (
    EXTRACTION_SYSTEM_PROMPT,
    build_extraction_user_prompt,
    build_completeness_prompt,
    RISK_SYSTEM_PROMPT,
    build_risk_prompt,
    CHANGE_AWARE_RISK_SYSTEM_PROMPT,
    build_change_aware_risk_prompt,
)
from duplicate_detector import find_duplicates
from graph_state import GraphState


# ---------------------------------------------------------------------------
# Dotted-path helpers (for nested fields like "customer_details.name")
# ---------------------------------------------------------------------------

def _get_field(data: dict, path: str) -> Any:
    value = data
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def _set_field(data: dict, path: str, value: Any) -> None:
    parts = path.split(".")
    d = data
    for part in parts[:-1]:
        d = d.setdefault(part, {})
    d[parts[-1]] = value


def _sanitize_category(value: str) -> str:
    valid_values = [c.value for c in ComplaintCategory]
    return value if value in valid_values else ComplaintCategory.OTHER.value


# ---------------------------------------------------------------------------
# Node 1: classify_input — snapshot state before this turn's edits
# ---------------------------------------------------------------------------

def classify_input_node(state: GraphState) -> dict:
    complaint = state["complaint"]
    previous_snapshot = complaint.model_copy(deep=True)
    return {"previous_complaint": previous_snapshot}


# ---------------------------------------------------------------------------
# Node 2: extract — LLM extracts/updates fields from raw text
# ---------------------------------------------------------------------------

def extract_node(state: GraphState) -> dict:
    complaint = state["complaint"]
    current_json = complaint.model_dump_json(indent=2)
    user_prompt = build_extraction_user_prompt(current_json, state["raw_input_text"])

    try:
        result = call_fast_model(EXTRACTION_SYSTEM_PROMPT, user_prompt)
    except LLMExtractionError:
        return {
            "error": "extraction_failed",
            "ai_message": "Sorry, I had trouble understanding that message. Could you rephrase it?",
        }

    return {"extraction_result": result}


# ---------------------------------------------------------------------------
# Node 3: merge_state — apply extracted updates, compute diff
# ---------------------------------------------------------------------------

def merge_state_node(state: GraphState) -> dict:
    if state.get("error"):
        return {}

    result = state.get("extraction_result", {}) or {}

    if result.get("no_relevant_update"):
        return {
            "diff": [],
            "ai_message": result.get(
                "ai_message",
                "That message didn't contain any complaint information I could apply — no changes made.",
            ),
        }

    complaint = state["complaint"]
    data = complaint.model_dump(mode="json")
    diffs: list[FieldDiff] = []

    for field_path, info in (result.get("updates") or {}).items():
        new_value = info.get("value")
        source_str = info.get("source", "ai_inferred")
        if new_value is None or new_value == "":
            continue

        if field_path == "complaint_type":
            new_value = _sanitize_category(new_value)

        old_value = _get_field(data, field_path)
        if old_value == new_value:
            continue

        _set_field(data, field_path, new_value)
        try:
            source = FieldSource(source_str)
        except ValueError:
            source = FieldSource.AI_INFERRED

        diffs.append(
            FieldDiff(
                field=field_path,
                old_value=str(old_value) if old_value not in (None, "") else None,
                new_value=str(new_value),
                source=source,
            )
        )

    if not diffs:
        return {
            "diff": [],
            "ai_message": result.get("ai_message", "No new information detected — the complaint is unchanged."),
        }

    try:
        updated_complaint = Complaint(**data)
    except Exception:
        return {
            "error": "merge_validation_failed",
            "ai_message": "I extracted some information but it didn't fit the expected format — could you rephrase?",
        }

    return {
        "complaint": updated_complaint,
        "diff": diffs,
        "ai_message": result.get("ai_message", "Got it — I've updated the complaint."),
    }


# ---------------------------------------------------------------------------
# Node 4: completeness_check — rule-based required-field check
# ---------------------------------------------------------------------------

def completeness_check_node(state: GraphState) -> dict:
    if state.get("error"):
        return {}

    complaint = state["complaint"]
    data = complaint.model_dump(mode="json")
    missing = [f for f in REQUIRED_FIELDS if not _get_field(data, f)]

    if not missing:
        return {"completeness": CompletenessResult(is_complete=True, missing_fields=[], message=None)}

    system, user_template = build_completeness_prompt(complaint.model_dump_json())
    user_prompt = user_template.replace("{missing_fields}", ", ".join(missing))

    try:
        result = call_fast_model(system, user_prompt)
        message = result.get("message")
    except LLMExtractionError:
        message = f"Still missing: {', '.join(missing).replace('_', ' ')}."

    return {"completeness": CompletenessResult(is_complete=False, missing_fields=missing, message=message)}


# ---------------------------------------------------------------------------
# Node 5: duplicate_check — embedding similarity against existing complaints
# ---------------------------------------------------------------------------

def duplicate_check_node(state: GraphState) -> dict:
    if state.get("error"):
        return {}

    complaint = state["complaint"]
    if not complaint.complaint_description and not complaint.batch_number:
        return {"duplicates": DuplicateCheckResult(has_duplicates=False, matches=[])}

    existing = [c for c in state.get("existing_complaints", []) if c.complaint_id != complaint.complaint_id]
    matches = find_duplicates(complaint, existing)

    return {"duplicates": DuplicateCheckResult(has_duplicates=len(matches) > 0, matches=matches)}


# ---------------------------------------------------------------------------
# Node 6: risk_assessment — change-aware risk reasoning
# ---------------------------------------------------------------------------

def risk_assessment_node(state: GraphState) -> dict:
    if state.get("error"):
        return {}

    complaint = state["complaint"]
    previous = state.get("previous_complaint")
    diff_top_level_fields = {d.field.split(".")[0] for d in state.get("diff", [])}
    relevant_changed = bool(diff_top_level_fields.intersection(RISK_RELEVANT_FIELDS))

    is_first_assessment = previous is None or previous.risk_assessment.risk_level == RiskLevel.UNASSESSED

    # No risk-relevant change on an already-assessed complaint -> skip the LLM
    # call entirely and keep the existing assessment. This is the cost/latency
    # payoff of change-aware reasoning: not every edit needs a fresh risk call.
    if not is_first_assessment and not relevant_changed:
        unchanged_assessment = complaint.risk_assessment.model_copy(update={"changed_this_turn": False})
        complaint.risk_assessment = unchanged_assessment
        return {"complaint": complaint, "risk_changed": False}

    try:
        if is_first_assessment:
            llm_result = call_reasoning_model(RISK_SYSTEM_PROMPT, build_risk_prompt(complaint.model_dump_json()))
            risk_changed = True
        else:
            llm_result = call_reasoning_model(
                CHANGE_AWARE_RISK_SYSTEM_PROMPT,
                build_change_aware_risk_prompt(
                    previous.model_dump_json(),
                    complaint.model_dump_json(),
                    list(diff_top_level_fields),
                ),
            )
            risk_changed = bool(llm_result.get("risk_changed", True))
    except LLMExtractionError:
        return {
            "error": "risk_assessment_failed",
            "ai_message": state.get("ai_message", "")
            + " (Note: I couldn't complete the risk assessment for this update — please retry.)",
        }

    try:
        risk_level = RiskLevel(llm_result.get("risk_level", "unassessed"))
    except ValueError:
        risk_level = RiskLevel.UNASSESSED

    complaint.risk_assessment = RiskAssessment(
        risk_level=risk_level,
        product_impact=llm_result.get("product_impact"),
        patient_impact=llm_result.get("patient_impact"),
        investigation_priority=llm_result.get("investigation_priority"),
        reasoning_summary=llm_result.get("reasoning_summary"),
        rubric_criteria_matched=llm_result.get("rubric_criteria_matched", []),
        suggested_actions=llm_result.get("suggested_actions", []),
        last_updated=datetime.utcnow(),
        changed_this_turn=risk_changed,
    )

    return {"complaint": complaint, "risk_changed": risk_changed}