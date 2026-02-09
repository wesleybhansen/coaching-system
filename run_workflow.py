"""Entry point for GitHub Actions to run workflows by name."""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

WORKFLOWS = {
    "process_emails": "workflows.process_emails",
    "check_in": "workflows.check_in",
    "send_approved": "workflows.send_approved",
    "re_engagement": "workflows.re_engagement",
    "cleanup": "workflows.cleanup",
}

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in WORKFLOWS:
        print(f"Usage: python run_workflow.py <{'|'.join(WORKFLOWS)}>")
        sys.exit(1)

    name = sys.argv[1]
    module = __import__(WORKFLOWS[name], fromlist=["run"])
    module.run()
