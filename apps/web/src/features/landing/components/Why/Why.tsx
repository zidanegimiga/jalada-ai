import { Eyebrow } from "../Eyebrow";
import { Lines, Words } from "../SplitText";

const SCATTERED = [
  { where: "WhatsApp", what: "Receipts, sent by the shop", speed: -0.25 },
  { where: "Email", what: "Withholding certificates", speed: 0.15 },
  { where: "A drawer", what: "Paper, slowly fading", speed: -0.1 },
];

/** Why records go missing, said once, slowly. */
export function Why() {
  return (
    <section
      id="why"
      data-tone="light"
      className="relative bg-(--l-paper-deep) px-4 py-28 text-(--l-ink) md:px-8 md:py-40"
    >
      <div className="mx-auto max-w-[90rem]">
        <Eyebrow number="01">Why</Eyebrow>
        <p
          data-motion="words"
          className="mt-10 max-w-6xl text-[clamp(1.75rem,4.4vw,4.25rem)] leading-[1.08] font-bold tracking-[-0.03em]"
        >
          <Words text="Salary for part of the year. Freelance work for the rest. Clients who deduct tax, and family who help between jobs. All of it through one M-Pesa line, and none of it written down until the return is due." />
        </p>

        <div className="mt-24 grid gap-14 md:mt-36 md:grid-cols-[1fr_1.4fr] md:gap-20">
          <h2
            className="text-[clamp(2.25rem,5vw,4.5rem)] leading-[0.95] font-bold tracking-[-0.035em]"
            data-motion="lines"
          >
            <Lines lines={["The year is", "in pieces."]} />
          </h2>
          <ul className="grid gap-4 sm:grid-cols-3">
            {SCATTERED.map((item, index) => (
              <li
                key={item.where}
                data-motion="parallax"
                data-speed={item.speed}
                className={`rounded-[1.75rem] p-6 ${index === 1 ? "bg-(--l-ink) text-(--l-paper)" : "bg-(--l-card)"}`}
              >
                <p className="font-mono text-tiny tracking-[0.16em] uppercase opacity-70">
                  0{index + 1}
                </p>
                <p className="mt-16 text-title">{item.where}</p>
                <p className="mt-1 text-small opacity-75">{item.what}</p>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
