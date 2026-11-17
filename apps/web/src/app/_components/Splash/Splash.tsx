import Image from "next/image";
import type { CSSProperties } from "react";

import { SPLASH } from "./splash-config";
import { SplashExit } from "./SplashExit";
import "./Splash";

/**
 * Runs before the first paint. A visitor who has already seen the loading screen in this
 * session does not see it again on a reload.
 */
const SEEN_SCRIPT = `try{if(sessionStorage.getItem(${JSON.stringify(SPLASH.storageKey)}))document.documentElement.dataset.splash="seen"}catch(e){}`;

export function SplashScript() {
  return <script dangerouslySetInnerHTML={{ __html: SEEN_SCRIPT }} />;
}

/**
 * The loading screen the first time the app opens. It is in the page's first HTML, so it
 * shows while the app's code downloads, and leaves once the app is ready.
 */
export function Splash() {
  return (
    <div id="splash" className="splash" aria-hidden="true">
      <div className="splash-logo">
        <Image
          src="/logo.webp"
          alt=""
          width={176}
          height={176}
          priority
          unoptimized
          className="splash-float"
        />
      </div>
      <p className="splash-wordmark">
        {[...SPLASH.wordmark].map((letter, index) => (
          <span key={index} style={{ "--index": index } as CSSProperties}>
            {letter === " " ? " " : letter}
          </span>
        ))}
      </p>
      <div className="splash-bar">
        <span />
      </div>
      <SplashExit />
    </div>
  );
}
