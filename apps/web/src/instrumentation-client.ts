import * as Sentry from "@sentry/nextjs";

import { errorTrackingOptions } from "@/lib/error-tracking";

Sentry.init({
  ...errorTrackingOptions(),
  integrations: [
    // Click breadcrumbs record the text on screen, which can be amounts and names.
    Sentry.breadcrumbsIntegration({ dom: false }),
  ],
});
