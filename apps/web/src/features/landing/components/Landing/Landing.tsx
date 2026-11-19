import { Cursor } from "../Cursor";
import { SiteHeader } from "../SiteHeader";
import { LandingMotion } from "../LandingMotion";
import { Ask } from "../Ask";
import { Closing } from "../Closing";
import { Figures } from "../Figures";
import { Hero } from "../Hero";
import { How } from "../How";
import { Promises } from "../Promises";
import { Questions } from "../Questions";
import { Reading } from "../Reading";
import { Ribbon } from "../Ribbon";
import { Why } from "../Why";
import { Offer } from "../Offer";
import { SectionPill } from "../SectionPill";
import { ReceiptEdge } from "../ReceiptEdge";

import "../../landing.css";

/** The page signed-out visitors see first. */
export function Landing() {
  return (
    <LandingMotion>
      <div data-landing="" className="flex-1">
        <SiteHeader />
        <main>
          <Hero />
          <ReceiptEdge
            facing="up"
            className="-mb-px block h-3.5 w-full bg-(--l-paper) text-(--l-ink)"
          />
          <Ribbon />
          <Why />
          <ReceiptEdge
            facing="up"
            className="-mb-px block h-3.5 w-full bg-(--l-paper-deep) text-(--l-flax)"
          />
          <Offer />
          <ReceiptEdge
            facing="up"
            className="-mb-px block h-3.5 w-full bg-(--l-flax) text-(--l-ink)"
          />
          <How />
          <Reading />
          <Ask />
          <Promises />
          <Figures />
          <Questions />
        </main>
        <Closing />
        <SectionPill />
        <Cursor />
      </div>
    </LandingMotion>
  );
}
