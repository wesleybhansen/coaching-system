"""Entry point for GitHub Actions to run workflows by name."""

import logging
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("run_workflow")

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
    logger.info(f"Starting workflow: {name}")
    start_time = time.time()

    try:
        module = __import__(WORKFLOWS[name], fromlist=["run"])
        module.run()
        elapsed = round(time.time() - start_time, 1)
        logger.info(f"Workflow '{name}' completed in {elapsed}s")
    except Exception as e:
        elapsed = round(time.time() - start_time, 1)
        logger.error(f"Workflow '{name}' failed after {elapsed}s: {e}", exc_info=True)
        sys.exit(1)
