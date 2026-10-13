import { useId, useState, type ReactNode } from "react";

/**
 * A chart on a sheet: title, one-line takeaway, the figure, a source line,
 * and a toggle that swaps the figure for its data table.
 */
export function FigureFrame({
  title,
  takeaway,
  source,
  table,
  children,
  id,
}: {
  title: string;
  takeaway?: ReactNode;
  source?: ReactNode;
  table?: ReactNode;
  children: ReactNode;
  id?: string;
}) {
  const [asTable, setAsTable] = useState(false);
  const titleId = useId();
  return (
    <section className="figure sheet" aria-labelledby={titleId} id={id}>
      <header className="figure__head">
        <div>
          <h3 id={titleId} className="figure__title">
            {title}
          </h3>
          {takeaway ? <p className="figure__takeaway">{takeaway}</p> : null}
        </div>
        {table ? (
          <button type="button" className="link-button" aria-pressed={asTable} onClick={() => setAsTable((v) => !v)}>
            {asTable ? "Show chart" : "Show as table"}
          </button>
        ) : null}
      </header>
      <div className="figure__body">{asTable && table ? table : children}</div>
      {source ? <p className="figure__source">{source}</p> : null}
    </section>
  );
}
