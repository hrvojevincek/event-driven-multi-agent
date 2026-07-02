"use client";

import { BaseEdge, getBezierPath, type EdgeProps } from "@xyflow/react";

export type PipelineEdgeData = {
  /** Source stage finished — keep the connector lit. */
  active?: boolean;
  /** Handoff into the currently running stage — show moving dot. */
  animated?: boolean;
};

export function PipelineEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
}: EdgeProps) {
  const edgeData = (data ?? {}) as PipelineEdgeData;
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          stroke: edgeData.active ? "var(--primary)" : "var(--border)",
          strokeWidth: edgeData.active ? 2.5 : 1.5,
        }}
      />
      {edgeData.animated ? (
        <circle r="4" fill="var(--primary)">
          <animateMotion dur="1.2s" repeatCount="indefinite" path={edgePath} />
        </circle>
      ) : null}
    </>
  );
}
