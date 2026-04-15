#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path

import anthropic

from scripts.utils import parse_skill_md

_DEFAULT_MODEL = os.environ.get("LILITH_MODEL", "claude-opus-4-6")


def _call_api(prompt: str, model: str | None) -> str:
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model=model or _DEFAULT_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip() if response.content else ""


def improve_description(
    skill_name: str,
    skill_content: str,
    current_description: str,
    eval_results: dict,
    history: list[dict],
    model: str,
    test_results: dict | None = None,
    log_dir: Path | None = None,
    iteration: int | None = None,
) -> str:
    failed_triggers = [
        r for r in eval_results["results"]
        if r["should_trigger"] and not r["pass"]
    ]
    false_triggers = [
        r for r in eval_results["results"]
        if not r["should_trigger"] and not r["pass"]
    ]

    train_score = (
        f"{eval_results['summary']['passed']}/{eval_results['summary']['total']}"
    )
    if test_results:
        test_score = (
            f"{test_results['summary']['passed']}/{test_results['summary']['total']}"
        )
        scores_summary = f"Train: {train_score}, Test: {test_score}"
    else:
        scores_summary = f"Train: {train_score}"

    prompt = (
        f'You are optimizing a skill description for a skill called "{skill_name}". '
        f"A skill has a title and description that an AI agent uses to decide whether "
        f"to invoke it, plus a detailed SKILL.md file with full instructions.\n\n"
        f"The description appears in the agent's available_skills list. "
        f"Your goal: write a description that triggers for relevant queries "
        f"and doesn't trigger for irrelevant ones.\n\n"
        f"Current description:\n"
        f'<current_description>\n"{current_description}"\n</current_description>\n\n'
        f"Current scores ({scores_summary}):\n<scores_summary>\n"
    )

    if failed_triggers:
        prompt += "FAILED TO TRIGGER (should have triggered but didn't):\n"
        for r in failed_triggers:
            prompt += f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
        prompt += "\n"

    if false_triggers:
        prompt += "FALSE TRIGGERS (triggered but shouldn't have):\n"
        for r in false_triggers:
            prompt += f'  - "{r["query"]}" (triggered {r["triggers"]}/{r["runs"]} times)\n'
        prompt += "\n"

    if history:
        prompt += "PREVIOUS ATTEMPTS (try something structurally different):\n\n"
        for h in history:
            train_s = (
                f"{h.get('train_passed', h.get('passed', 0))}"
                f"/{h.get('train_total', h.get('total', 0))}"
            )
            test_s = (
                f"{h.get('test_passed', '?')}/{h.get('test_total', '?')}"
                if h.get("test_passed") is not None
                else None
            )
            score_str = "train=" + train_s + (f", test={test_s}" if test_s else "")
            prompt += f"<attempt {score_str}>\n"
            prompt += f'Description: "{h["description"]}"\n'
            if "results" in h:
                prompt += "Train results:\n"
                for r in h["results"]:
                    status = "PASS" if r["pass"] else "FAIL"
                    prompt += (
                        f'  [{status}] "{r["query"][:80]}"'
                        f' (triggered {r["triggers"]}/{r["runs"]})\n'
                    )
            if h.get("note"):
                prompt += f'Note: {h["note"]}\n'
            prompt += "</attempt>\n\n"

    prompt += (
        f"</scores_summary>\n\n"
        f"Skill content (context only):\n"
        f"<skill_content>\n{skill_content}\n</skill_content>\n\n"
        f"Write an improved description under 200 words (hard limit: 1024 chars). "
        f"Use imperative phrasing ('Use this skill for...'). "
        f"Focus on user intent, not implementation details. "
        f"Generalize from failures — avoid overfitting to specific queries.\n\n"
        f"Respond with only the new description in <new_description> tags."
    )

    text = _call_api(prompt, model)
    match = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    description = match.group(1).strip().strip('"') if match else text.strip().strip('"')

    transcript: dict = {
        "iteration": iteration,
        "prompt": prompt,
        "response": text,
        "parsed_description": description,
        "char_count": len(description),
        "over_limit": len(description) > 1024,
    }

    if len(description) > 1024:
        shorten_prompt = (
            f"{prompt}\n\n---\n\n"
            f"A previous attempt produced this {len(description)}-char description "
            f"(over the 1024-char hard limit):\n\n"
            f'"{description}"\n\n'
            f"Rewrite it under 1024 characters. "
            f"Respond with only the new description in <new_description> tags."
        )
        shorten_text = _call_api(shorten_prompt, model)
        match = re.search(
            r"<new_description>(.*?)</new_description>", shorten_text, re.DOTALL
        )
        shortened = (
            match.group(1).strip().strip('"')
            if match
            else shorten_text.strip().strip('"')
        )
        transcript.update({
            "rewrite_prompt": shorten_prompt,
            "rewrite_response": shorten_text,
            "rewrite_description": shortened,
            "rewrite_char_count": len(shortened),
        })
        description = shortened

    transcript["final_description"] = description

    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"improve_iter_{iteration or 'unknown'}.json").write_text(
            json.dumps(transcript, indent=2)
        )

    return description


def main():
    parser = argparse.ArgumentParser(
        description="Improve a skill description based on eval results"
    )
    parser.add_argument("--eval-results", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--history", default=None)
    parser.add_argument("--model", required=True)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    skill_path = Path(args.skill_path)
    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md at {skill_path}", file=sys.stderr)
        sys.exit(1)

    eval_results = json.loads(Path(args.eval_results).read_text())
    history = json.loads(Path(args.history).read_text()) if args.history else []

    name, _, content = parse_skill_md(skill_path)
    current_description = eval_results["description"]

    if args.verbose:
        print(f"Current: {current_description}", file=sys.stderr)
        s = eval_results["summary"]
        print(f"Score: {s['passed']}/{s['total']}", file=sys.stderr)

    new_description = improve_description(
        skill_name=name,
        skill_content=content,
        current_description=current_description,
        eval_results=eval_results,
        history=history,
        model=args.model,
    )

    if args.verbose:
        print(f"Improved: {new_description}", file=sys.stderr)

    print(json.dumps({
        "description": new_description,
        "history": history + [{
            "description": current_description,
            "passed": eval_results["summary"]["passed"],
            "failed": eval_results["summary"]["failed"],
            "total": eval_results["summary"]["total"],
            "results": eval_results["results"],
        }],
    }, indent=2))


if __name__ == "__main__":
    main()
