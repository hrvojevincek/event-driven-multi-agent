import type { Edge, Node } from "@xyflow/react";

import {
  PIPELINE_STAGES,
  type JobStageSnapshot,
  type StageStatus,
} from "@/types/job-stream";

import { agentNameForStage } from "./stage-agents";
import type { PipelineEdgeData } from "./pipeline-edge";
import type { PipelineNodeData } from "./pipeline-node";

const NODE_WIDTH = 160;
const NODE_GAP = 80;
const ROW_Y = 0;

function stageStatus(
  stageId: string,
  stages: Record<string, JobStageSnapshot>,
): StageStatus {
  return stages[stageId]?.status ?? "pending";
}

function isEdgeCompleted(sourceStatus: StageStatus): boolean {
  return sourceStatus === "completed";
}

function isEdgeAnimated(
  sourceStatus: StageStatus,
  targetStatus: StageStatus,
): boolean {
  return sourceStatus === "completed" && targetStatus === "running";
}

export function buildPipelineGraph(
  stages: Record<string, JobStageSnapshot>,
): { nodes: Node<PipelineNodeData>[]; edges: Edge<PipelineEdgeData>[] } {
  const nodes: Node<PipelineNodeData>[] = PIPELINE_STAGES.map((stage, index) => ({
    id: stage.id,
    type: "pipeline",
    position: { x: index * (NODE_WIDTH + NODE_GAP), y: ROW_Y },
    data: {
      stageId: stage.id,
      label: stage.label,
      agentName: agentNameForStage(stage.id),
      status: stageStatus(stage.id, stages),
    },
  }));

  const edges: Edge<PipelineEdgeData>[] = PIPELINE_STAGES.slice(0, -1).map(
    (stage, index) => {
      const targetStage = PIPELINE_STAGES[index + 1];
      const sourceStatus = stageStatus(stage.id, stages);
      const targetStatus = stageStatus(targetStage.id, stages);

      return {
        id: `${stage.id}->${targetStage.id}`,
        source: stage.id,
        target: targetStage.id,
        type: "pipeline",
        data: {
          active: isEdgeCompleted(sourceStatus),
          animated: isEdgeAnimated(sourceStatus, targetStatus),
        },
      };
    },
  );

  return { nodes, edges };
}
