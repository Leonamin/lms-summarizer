import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { Artifact, Job } from "../types";
import {
  getAvailableArtifacts,
  getSelectedArtifact,
  type ArtifactSelection,
} from "../lib/jobResults";

export function useJobResult(
  job: Job | null,
  report: (cause: unknown) => void,
) {
  const [selection, setSelection] = useState<ArtifactSelection | null>(null);
  const [content, setContent] = useState<{
    artifactId: string;
    text: string;
    isLoading: boolean;
  } | null>(null);
  const [requestVersion, setRequestVersion] = useState(0);
  const [jobModel, setJobModel] = useState("chatgpt");
  const available = getAvailableArtifacts(job);
  const artifact = getSelectedArtifact(job, selection);
  const artifactId = artifact?.id;

  useEffect(() => {
    let isAlive = true;
    setJobModel("chatgpt");
    if (job)
      api<{ settings: { ai_model: string } }>(`/jobs/${job.id}/settings`)
        .then((result) => {
          if (isAlive) setJobModel(result.settings.ai_model);
        })
        .catch(() => {});
    return () => {
      isAlive = false;
    };
  }, [job?.id, job?.settings_revision_id]);

  useEffect(() => {
    if (!artifactId) {
      setContent(null);
      return;
    }
    let isAlive = true;
    setContent({ artifactId, text: "", isLoading: true });
    api<{ text: string }>(`/artifacts/${artifactId}/content`)
      .then((result) => {
        if (isAlive)
          setContent({ artifactId, text: result.text, isLoading: false });
      })
      .catch((cause) => {
        if (isAlive) {
          setContent({ artifactId, text: "", isLoading: false });
          report(cause);
        }
      });
    return () => {
      isAlive = false;
    };
  }, [artifactId, requestVersion, report]);

  const openArtifact = useCallback(
    (item: Artifact) => {
      if (!job) return;
      setSelection({
        jobId: job.id,
        attemptId: job.current_attempt_id,
        kind: item.kind,
      });
      setRequestVersion((version) => version + 1);
    },
    [job?.id, job?.current_attempt_id],
  );

  const hasCurrentContent = !!artifactId && content?.artifactId === artifactId;
  return {
    available,
    artifact,
    jobModel,
    openArtifact,
    text: hasCurrentContent ? content.text : "",
    isLoadingText: !!artifactId && (!hasCurrentContent || content.isLoading),
  };
}
