import { type FormEvent, useState } from "react";

import { type Answer, api } from "../api/client";
import { checkedAgainst, paragraphs } from "../askText";
import { useResource } from "../useResource";

type State =
  | { kind: "idle" }
  | { kind: "asking" }
  | { kind: "answer"; answer: Answer }
  | { kind: "error"; message: string };

/** A question about a town or Ireland, answered by the assistant. Hidden while the assistant is off. */
export function AskBox({ place, settlement }: { place: string; settlement?: string }) {
  const status = useResource((signal) => api.assistant(signal), "assistant");
  const [question, setQuestion] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });
  if (status.kind !== "ready" || !status.data.enabled) return null;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (question.trim().length < 3) return;
    setState({ kind: "asking" });
    try {
      setState({ kind: "answer", answer: await api.ask(question.trim(), settlement) });
    } catch (error) {
      setState({ kind: "error", message: error instanceof Error ? error.message : "Something went wrong." });
    }
  };

  return (
    <section aria-labelledby="ask-title" className="level ask">
      <h2 id="ask-title" className="level-title">
        Ask about {place}
      </h2>
      <form onSubmit={submit} className="ask-form">
        <label className="sr-only" htmlFor="ask-question">
          Your question
        </label>
        <textarea
          id="ask-question"
          value={question}
          maxLength={500}
          rows={2}
          placeholder={settlement ? "e.g. What have homes sold for here?" : "e.g. Where are most homes being started?"}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="cost-submit" disabled={state.kind === "asking"}>
          {state.kind === "asking" ? "Checking the data…" : "Ask"}
        </button>
      </form>
      {state.kind === "error" && (
        <p className="failure" role="alert">
          {state.message}
        </p>
      )}
      {state.kind === "answer" && <Reply answer={state.answer} />}
      <p className="note">
        Answers come from DwellWise&rsquo;s own data. Every number is checked against it before it is shown; an
        answer that fails the check is not shown. Not planning advice, and never the value of a site.
      </p>
    </section>
  );
}

function Reply({ answer }: { answer: Answer }) {
  const sources = checkedAgainst(answer.tools);
  return (
    <div className={answer.grounded ? "ask-answer" : "ask-answer muted"} role="status">
      {paragraphs(answer.answer).map((p, i) => (
        <p key={i}>{p}</p>
      ))}
      {answer.grounded && sources ? <p className="row-meta">Checked against: {sources}.</p> : null}
    </div>
  );
}
