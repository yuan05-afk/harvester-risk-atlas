import { Link } from "react-router-dom";

export function NotFound({ what = "page" }: { what?: string }) {
  return (
    <div className="page narrow">
      <h1>That {what} is not in the atlas</h1>
      <p>
        The link may be out of date. Search for a plant with <kbd>/</kbd>, or start from the{" "}
        <Link to="/plants">list of plants</Link>.
      </p>
    </div>
  );
}
