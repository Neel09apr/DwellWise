/** Loading and error lines, the same on every page. */
export function Loading({ what }: { what: string }) {
  return (
    <p className="muted" role="status">
      Loading {what}…
    </p>
  );
}

export function Failure({ message }: { message: string }) {
  return (
    <p className="failure" role="alert">
      {message}
    </p>
  );
}
