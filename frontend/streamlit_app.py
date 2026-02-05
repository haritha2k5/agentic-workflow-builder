"""Streamlit frontend for Agentic Workflow Builder."""

import time
from typing import Any

import requests
import streamlit as st

API_BASE_URL = "http://localhost:8000"


# ---------------------------
# SESSION STATE
# ---------------------------
def init_session_state():
    if "steps" not in st.session_state:
        st.session_state.steps = []

    if "execution_id" not in st.session_state:
        st.session_state.execution_id = None


# ---------------------------
# STEP MANAGEMENT
# ---------------------------
def add_step():
    st.session_state.steps.append(
        {
            "model": "",
            "prompt": "",
            "completion_criteria": "",
            "retry_limit": 0,
        }
    )


def remove_step(index: int):
    st.session_state.steps.pop(index)


# ---------------------------
# API CALLS
# ---------------------------
def create_workflow(name: str, steps: list[dict[str, Any]]) -> dict | None:
    try:
        payload = {
            "name": name,
            "steps": [
                {
                    "model": step["model"],
                    "prompt": step["prompt"],
                    "completion_criteria": step["completion_criteria"] or None,
                    "retry_limit": step["retry_limit"],
                    "step_order": idx + 1,
                }
                for idx, step in enumerate(steps)
            ],
        }

        res = requests.post(f"{API_BASE_URL}/workflow", json=payload, timeout=15)
        res.raise_for_status()
        return res.json()

    except requests.RequestException as e:
        st.error(f"Error creating workflow: {e}")
        return None


def run_workflow_api(workflow_id: int):
    try:
        res = requests.post(
            f"{API_BASE_URL}/workflow/run/{workflow_id}", timeout=15
        )
        res.raise_for_status()
        return res.json()

    except requests.RequestException as e:
        st.error(f"Error running workflow: {e}")
        return None


def get_execution(execution_id: int):
    try:
        res = requests.get(
            f"{API_BASE_URL}/execution/{execution_id}", timeout=15
        )
        res.raise_for_status()
        return res.json()

    except requests.RequestException as e:
        st.error(f"Error fetching execution: {e}")
        return None


def get_executions():
    try:
        res = requests.get(f"{API_BASE_URL}/executions", timeout=15)
        res.raise_for_status()
        return res.json()

    except requests.RequestException as e:
        st.error(f"Error fetching executions: {e}")
        return None


# ---------------------------
# LIVE PROGRESS
# ---------------------------
def display_execution_progress(execution_id: int):

    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    logs_placeholder = st.empty()
    final_placeholder = st.empty()

    # bounded polling → safe for Streamlit
    for _ in range(100):

        execution = get_execution(execution_id)
        if not execution:
            break

        status = execution["status"]
        step_logs = execution["step_logs"]

        # Progress Bar
        total = len(step_logs)
        completed = sum(1 for s in step_logs if s["status"] == "COMPLETED")
        progress = completed / total if total else 0

        progress_placeholder.progress(
            progress, text=f"Steps Completed: {completed}/{total}"
        )

        # Status Display
        color = {"RUNNING": "🟡", "SUCCESS": "🟢", "FAILED": "🔴"}.get(status, "⚪")

        status_placeholder.markdown(
            f"### {color} Execution Status: **{status}**"
        )

        # Step Logs
        with logs_placeholder.container():
            if step_logs:
                st.subheader("Step Logs")

                for log in step_logs:
                    icon = {
                        "RUNNING": "⏳",
                        "COMPLETED": "✅",
                        "FAILED": "❌",
                    }.get(log["status"], "⚪")

                    with st.expander(
                        f"{icon} Step {log['step_order']} - {log['status']} "
                        f"(Retries: {log['retry_count']})"
                    ):
                        if log["output"]:
                            st.code(log["output"])
                        else:
                            st.info("No output yet...")

        # Final Output
        if status in ["SUCCESS", "FAILED"]:

            with final_placeholder.container():

                st.markdown("---")

                if status == "SUCCESS":
                    st.success("Workflow Completed Successfully!")

                    st.subheader("Final Outputs")
                    for log in step_logs:
                        if log["output"]:
                            st.markdown(f"**Step {log['step_order']}**")
                            st.code(log["output"])

                else:
                    st.error("Workflow Failed")

            # Reset session
            st.session_state.execution_id = None
            break

        time.sleep(2)


# ---------------------------
# MAIN UI
# ---------------------------
def main():

    st.set_page_config(page_title="Agentic Workflow Builder", layout="wide")
    st.title("🤖 Agentic Workflow Builder")

    init_session_state()

    # =====================
    # CREATE WORKFLOW
    # =====================
    st.header("1️⃣ Create Workflow")

    workflow_name = st.text_input("Workflow Name")

    st.subheader("Steps")

    if st.button("➕ Add Step"):
        add_step()

    for idx, step in enumerate(st.session_state.steps):

        with st.expander(f"Step {idx + 1}", expanded=True):

            col1, col2 = st.columns([4, 1])

            with col1:
                step["model"] = st.text_input(
                    "Model", step["model"], key=f"model_{idx}"
                )

                step["prompt"] = st.text_area(
                    "Prompt", step["prompt"], key=f"prompt_{idx}"
                )

                step["completion_criteria"] = st.text_input(
                    "Completion Criteria (Optional)",
                    step["completion_criteria"],
                    key=f"criteria_{idx}",
                )

                step["retry_limit"] = st.number_input(
                    "Retry Limit", min_value=0, value=step["retry_limit"], key=f"retry_{idx}"
                )

            with col2:
                if st.button("🗑 Remove", key=f"remove_{idx}"):
                    remove_step(idx)
                    st.rerun()

    if st.button("Create Workflow"):

        if not workflow_name:
            st.error("Enter workflow name")

        elif not st.session_state.steps:
            st.error("Add at least one step")

        else:
            result = create_workflow(workflow_name, st.session_state.steps)

            if result:
                st.success(f"Workflow Created! ID = {result['workflow_id']}")
                st.session_state.steps = []

    st.divider()

    # =====================
    # RUN WORKFLOW
    # =====================
    st.header("2️⃣ Run Workflow")

    workflow_id = st.number_input("Workflow ID", min_value=1, step=1)

    if st.button("🚀 Run Workflow"):

        result = run_workflow_api(workflow_id)

        if result:
            st.session_state.execution_id = result["execution_id"]
            st.success(f"Execution Started! ID = {result['execution_id']}")

    st.divider()

    # =====================
    # LIVE PROGRESS
    # =====================
    if st.session_state.execution_id:
        st.header("3️⃣ Execution Progress")
        display_execution_progress(st.session_state.execution_id)

    st.divider()

    # =====================
    # HISTORY
    # =====================
    st.header("4️⃣ Execution History")

    if st.button("Refresh History"):

        executions = get_executions()

        if executions:
            for exec_data in executions:

                icon = {
                    "RUNNING": "🟡",
                    "SUCCESS": "🟢",
                    "FAILED": "🔴",
                }.get(exec_data["status"], "⚪")

                with st.expander(
                    f"{icon} Execution {exec_data['id']} "
                    f"(Workflow {exec_data['workflow_id']})"
                ):
                    st.write(exec_data)


if __name__ == "__main__":
    main()
