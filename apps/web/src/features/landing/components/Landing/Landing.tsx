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

import "../../landing.css";

/** The page signed-out visitors see first. */
export function Landing() {
  return (
    <LandingMotion>
      <div data-landing="" className="flex-1">
        <SiteHeader />
        <main>
          <Hero />
          <Ribbon />
          <Why />
          <How />
          <Reading />
          <Ask />
          <Promises />
          <Figures />
          <Questions />
        </main>
        <Closing />
        <Cursor />
      </div>
    </LandingMotion>
  );
}
