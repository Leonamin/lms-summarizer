"""Dependency-free diagnostic entry point for the shared domain layer."""
import json
from src.core.models.jobs import JobStatus
from src.core.models.stages import PipelineStage

def main():
    print(json.dumps({"stages": [s.name for s in PipelineStage], "statuses": [s.value for s in JobStatus]}))

if __name__ == "__main__":
    main()
