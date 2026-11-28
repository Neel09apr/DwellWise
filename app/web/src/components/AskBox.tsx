import { type FormEvent, useState } from "react";

import { type Answer, api } from "../api/client";
import { checkedAgainst, historyOf, paragraphs } from "../askText";
import { useResource } from "../useResource";
import { ShortlistTable } from "./ShortlistTable";

type Exchange = { question: string; answer: Answer };
type Status = { kind: "idle" } | { kind: "asking" } | { kind: "error"; message: string };

/** A short conversation with the assistant about a town or Ireland. Hidden while the assistant is off. */
export function AskBox({ place, settlement }: { place: string; settlement?: string }) {
  const status = useResource((signal) => api.assistant(signal), "assistant");
  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [state, setState] = useState<Status>({ kind: "idle" });
  if (status.kind !== "ready" || !status.data.enabled) return null;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const asked = question.trim();
    if (asked.length < 3) return;
    setState({ kind: "asking" });
    try {
      const history = historyOf(
        exchanges.map((e) => ({
          question: e.question,
          answer: e.answer.answer,
        })),
      );
      const answer = await api.ask(asked, settlement, history);
      setExchanges([...exchanges, { question: asked, answer }]);
      setQuestion("");
      setState({ kind: "idle" });
    } catch (error) {
      setState({
        kind: "error",
        message: error instanceof Error ? error.message : "Something went wrong.",
      });
    }
  };

  const restart = () => {
    setExchanges([]);
    setState({ kind: "idle" });
  };

  return (
    <section aria-labelledby="ask-title" className="level ask notice-half">
      <h2 id="ask-title" className="level-title">
        Ask about {place}
      </h2>
      {exchanges.map((e, i) => (
        <div key={i} className="ask-exchange">
          <p className="ask-question">{e.question}</p>
          <Reply answer={e.answer} />
        </div>
      ))}
      <form onSubmit={submit} className="ask-form">
        <label className="sr-only" htmlFor="ask-question">
          {exchanges.length ? "Your follow-up" : "Your question"}
        </label>
        <textarea
          id="ask-question"
          value={question}
          maxLength={500}
          rows={2}
          placeholder={
            exchanges.length
              ? "Ask a follow-up"
              : settlement
                ? "e.g. What have homes sold for here?"
                : "e.g. I want to build eight homes in Kildare. Which towns?"
          }
          onChange={(e) => setQuestion(e.target.value)}
        />
        <button type="submit" className="cost-submit" disabled={state.kind === "asking"}>
          {state.kind === "asking" ? "Checking the data…" : "Ask"}
        </button>
      </form>
      {exchanges.length > 0 && (
        <button type="button" className="ask-restart" onClick={restart}>
          Start again
        </button>
      )}
      {state.kind === "error" && (
        <p className="failure" role="alert">
          {state.message}
        </p>
      )}
      <p className="note">
        Answers come from DwellWise&rsquo;s own data. Every number is checked against it before it is shown; an answer
        that fails the check is not shown. Not planning advice, and never the value of a site.
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
      {(answer.shortlists ?? []).map((s, i) => (
        <ShortlistTable key={i} shortlist={s} />
      ))}
      {answer.grounded && sources ? <p className="row-meta">Checked against: {sources}.</p> : null}
    </div>
  );
}
