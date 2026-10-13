import markSvg from "../assets/mark.svg?raw";

/**
 * The atlas mark: a hand-built Philippine silhouette, record dots and a leaf
 * (carried over from v1). `draw` plays the one-time line draw on the
 * Overview; everywhere else it is static.
 */
export function Mark({ size = 28, draw = false, className = "" }: { size?: number; draw?: boolean; className?: string }) {
  return (
    <span
      className={`mark${draw ? " mark--draw" : ""} ${className}`}
      style={{ width: size, height: size }}
      aria-hidden="true"
      dangerouslySetInnerHTML={{ __html: markSvg }}
    />
  );
}
